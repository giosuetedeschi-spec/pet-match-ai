import { NextRequest, NextResponse } from "next/server";
import { attachSessionCookie, createSession, verifyPassword } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });
  const input = body as Record<string, unknown>;
  const email = typeof input.email === "string" ? input.email.trim().toLowerCase() : "";
  const password = typeof input.password === "string" ? input.password : "";
  if (!email || !password || email.length > 254 || Buffer.byteLength(password, "utf8") > 128) {
    return NextResponse.json({ error: "Email o password non corrette, oppure email non verificata." }, { status: 401 });
  }

  try {
    const user = await prisma.user.findUnique({ where: { email }, select: { id: true, passwordHash: true, emailVerifiedAt: true, status: true, deletedAt: true } });
    if (!user?.passwordHash || !user.emailVerifiedAt || user.status !== "active" || user.deletedAt || !(await verifyPassword(password, user.passwordHash))) {
      return NextResponse.json({ error: "Email o password non corrette, oppure email non verificata." }, { status: 401 });
    }
    const session = await createSession(user.id);
    return attachSessionCookie(NextResponse.json({ authenticated: true }), session.token, session.expiresAt);
  } catch {
    return NextResponse.json({ error: "Accesso temporaneamente non disponibile." }, { status: 503 });
  }
}
