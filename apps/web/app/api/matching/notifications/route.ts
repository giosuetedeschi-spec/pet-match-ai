import { NextRequest, NextResponse } from "next/server";
import { createRecordId, getRequestSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const session = await getRequestSession(request);
  if (!session) return NextResponse.json({ authenticated: false }, { headers: { "Cache-Control": "private, no-store" } });
  const profile = await prisma.adopterProfile.findUnique({ where: { userId: session.user.id }, select: { notifyNewMatches: true, minNotifyScore: true, completedAt: true } });
  return NextResponse.json({ authenticated: true, enabled: profile?.notifyNewMatches ?? false, ready: Boolean(profile?.completedAt), minimumScore: profile?.minNotifyScore ?? 70 }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function PUT(request: NextRequest) {
  const session = await getRequestSession(request);
  if (!session) return NextResponse.json({ error: "Accedi con un account verificato per attivare i digest." }, { status: 401 });
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!body || typeof body !== "object" || Array.isArray(body) || typeof (body as Record<string, unknown>).enabled !== "boolean") {
    return NextResponse.json({ error: "Preferenza non valida." }, { status: 400 });
  }
  const enabled = (body as Record<string, unknown>).enabled as boolean;
  const minimumScore = (body as Record<string, unknown>).minimumScore ?? 70;
  if (typeof minimumScore !== "number" || !Number.isInteger(minimumScore) || minimumScore < 45 || minimumScore > 100) {
    return NextResponse.json({ error: "La soglia deve essere tra 45 e 100." }, { status: 400 });
  }
  const profile = await prisma.adopterProfile.upsert({
    where: { userId: session.user.id },
    create: { id: createRecordId(), userId: session.user.id },
    update: {},
    select: { id: true, completedAt: true },
  });
  if (enabled && !profile.completedAt) return NextResponse.json({ error: "Completa prima il questionario." }, { status: 409 });
  await prisma.adopterProfile.update({
    where: { id: profile.id },
    data: { notifyNewMatches: enabled, minNotifyScore: minimumScore },
  });
  return NextResponse.json({ enabled, minimumScore }, { headers: { "Cache-Control": "private, no-store" } });
}
