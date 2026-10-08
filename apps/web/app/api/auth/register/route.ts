import { NextRequest, NextResponse } from "next/server";
import { createOpaqueToken, createRecordId, hashPassword, hashToken } from "@/lib/auth";
import { sendVerificationEmail } from "@/lib/mailer";
import { prisma } from "@/lib/prisma";

function record(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export async function POST(request: NextRequest) {
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!record(body)) return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });

  const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
  const fullName = typeof body.fullName === "string" ? body.fullName.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254) {
    return NextResponse.json({ error: "Inserisci un indirizzo email valido." }, { status: 400 });
  }
  if (fullName.length < 2 || fullName.length > 160) {
    return NextResponse.json({ error: "Il nome deve avere tra 2 e 160 caratteri." }, { status: 400 });
  }
  if (password.length < 12 || Buffer.byteLength(password, "utf8") > 128) {
    return NextResponse.json({ error: "La password deve avere almeno 12 caratteri e non superare 128 byte." }, { status: 400 });
  }

  const verificationToken = createOpaqueToken();
  const cookieToken = request.cookies.get("petmatch-adopter")?.value;
  try {
    const passwordHash = await hashPassword(password);
    const result = await prisma.$transaction(async (transaction) => {
      const user = await transaction.user.create({ data: { id: createRecordId(), email, fullName, passwordHash } });
      const profile = cookieToken
        ? await transaction.adopterProfile.findUnique({ where: { anonymousToken: cookieToken }, select: { id: true } })
        : null;
      await transaction.verificationToken.create({
        data: {
          id: createRecordId(),
          userId: user.id,
          adopterProfileId: profile?.id,
          tokenHash: hashToken(verificationToken),
          purpose: "email_verification",
          expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
        },
      });
      return user;
    });
    await sendVerificationEmail(result.email, result.fullName, verificationToken);
    return NextResponse.json({ message: "Se l'indirizzo può essere registrato, riceverai un link di verifica." }, { status: 202 });
  } catch {
    return NextResponse.json({ error: "Registrazione temporaneamente non disponibile. Riprova tra poco." }, { status: 503 });
  }
}
