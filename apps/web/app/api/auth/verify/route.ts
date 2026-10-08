import { NextRequest, NextResponse } from "next/server";
import { attachSessionCookie, clearAdopterCookie, createOpaqueToken, createRecordId, hashToken, sessionCookieName } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Link non valido." }, { status: 400 }); }
  const token = body && typeof body === "object" && !Array.isArray(body) ? (body as Record<string, unknown>).token : null;
  if (typeof token !== "string" || token.length < 32 || token.length > 128) return NextResponse.json({ error: "Link non valido o scaduto." }, { status: 400 });

  const verification = await prisma.verificationToken.findFirst({
    where: { tokenHash: hashToken(token), purpose: "email_verification", consumedAt: null, expiresAt: { gt: new Date() } },
    select: { id: true, userId: true, adopterProfileId: true },
  });
  if (!verification) return NextResponse.json({ error: "Link non valido o scaduto." }, { status: 400 });

  const sessionToken = createOpaqueToken();
  const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
  try {
    await prisma.$transaction(async (transaction) => {
      const consumed = await transaction.verificationToken.updateMany({
        where: { id: verification.id, consumedAt: null, expiresAt: { gt: new Date() } },
        data: { consumedAt: new Date() },
      });
      if (consumed.count !== 1) throw new Error("Verification token already consumed.");
      await transaction.user.update({ where: { id: verification.userId }, data: { emailVerifiedAt: new Date() } });
      if (verification.adopterProfileId) {
        await transaction.adopterProfile.updateMany({
          where: { id: verification.adopterProfileId, userId: null },
          data: { userId: verification.userId, anonymousToken: null },
        });
      }
      await transaction.session.create({
        data: { id: createRecordId(), userId: verification.userId, tokenHash: hashToken(sessionToken), expiresAt },
      });
    });
    const response = NextResponse.json({ verified: true });
    attachSessionCookie(response, sessionToken, expiresAt);
    clearAdopterCookie(response);
    return response;
  } catch {
    return NextResponse.json({ error: "Verifica temporaneamente non disponibile." }, { status: 503 });
  }
}
