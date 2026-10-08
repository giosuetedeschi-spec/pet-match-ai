import { NextRequest, NextResponse } from "next/server";
import { createOpaqueToken, createRecordId, hashToken } from "@/lib/auth";
import { sendVerificationEmail } from "@/lib/mailer";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  const email = body && typeof body === "object" && !Array.isArray(body) && typeof (body as Record<string, unknown>).email === "string"
    ? ((body as Record<string, unknown>).email as string).trim().toLowerCase()
    : "";
  if (!email || email.length > 254) return NextResponse.json({ message: "Se l'account esiste e non è verificato, riceverai un link." }, { status: 202 });

  try {
    const user = await prisma.user.findUnique({ where: { email }, select: { id: true, fullName: true, emailVerifiedAt: true, status: true } });
    if (user && !user.emailVerifiedAt && user.status === "active") {
      const token = createOpaqueToken();
      const anonymousToken = request.cookies.get("petmatch-adopter")?.value;
      const profile = anonymousToken
        ? await prisma.adopterProfile.findUnique({ where: { anonymousToken }, select: { id: true } })
        : null;
      await prisma.verificationToken.create({
        data: {
          id: createRecordId(),
          userId: user.id,
          adopterProfileId: profile?.id,
          tokenHash: hashToken(token),
          purpose: "email_verification",
          expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
        },
      });
      await sendVerificationEmail(email, user.fullName, token);
    }
    return NextResponse.json({ message: "Se l'account esiste e non è verificato, riceverai un link." }, { status: 202 });
  } catch {
    return NextResponse.json({ error: "Richiesta non disponibile. Riprova tra poco." }, { status: 503 });
  }
}
