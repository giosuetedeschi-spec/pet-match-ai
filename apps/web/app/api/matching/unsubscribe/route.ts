import { NextRequest, NextResponse } from "next/server";
import { hashToken } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  let token = request.nextUrl.searchParams.get("token");
  if (!token) {
    const contentType = request.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      try { token = (await request.json()).token ?? null; } catch { token = null; }
    } else {
      const form = new URLSearchParams(await request.text());
      token = form.get("token") ?? form.get("List-Unsubscribe") ?? null;
    }
  }
  if (typeof token !== "string" || token.length < 32 || token.length > 128) return NextResponse.json({ error: "Link non valido o scaduto." }, { status: 400 });
  const record = await prisma.matchUnsubscribeToken.findFirst({
    where: { tokenHash: hashToken(token), consumedAt: null, expiresAt: { gt: new Date() } },
    select: { id: true, profileId: true, profile: { select: { userId: true } } },
  });
  if (!record) return NextResponse.json({ error: "Link non valido o scaduto." }, { status: 400 });
  try {
    await prisma.$transaction(async (transaction) => {
      const consumed = await transaction.matchUnsubscribeToken.updateMany({ where: { id: record.id, consumedAt: null, expiresAt: { gt: new Date() } }, data: { consumedAt: new Date() } });
      if (consumed.count !== 1) throw new Error("Unsubscribe token already consumed.");
      await transaction.adopterProfile.update({ where: { id: record.profileId }, data: { notifyNewMatches: false } });
      if (record.profile.userId) await transaction.notificationDelivery.updateMany({
        where: { notification: { is: { userId: record.profile.userId, type: "match.new" } }, channel: "email", status: { in: ["pending", "failed"] } },
        data: { status: "skipped" },
      });
    });
    return NextResponse.json({ unsubscribed: true }, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ error: "Disiscrizione non disponibile. Riprova." }, { status: 503 });
  }
}
