import { NextRequest, NextResponse } from "next/server";
import { getRequestSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const session = await getRequestSession(request);
  if (!session) return NextResponse.json({ error: "Accedi per vedere le notifiche." }, { status: 401 });
  const notifications = await prisma.notification.findMany({
    where: { userId: session.user.id },
    orderBy: { createdAt: "desc" },
    take: 30,
    select: { id: true, type: true, titleKey: true, payload: true, linkUrl: true, readAt: true, createdAt: true },
  });
  return NextResponse.json({ notifications: notifications.map((item) => ({ ...item, id: item.id.toString() })) }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function POST(request: NextRequest) {
  const session = await getRequestSession(request);
  if (!session) return NextResponse.json({ error: "Accedi per aggiornare le notifiche." }, { status: 401 });
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  const id = body && typeof body === "object" && !Array.isArray(body) ? (body as Record<string, unknown>).id : null;
  if (typeof id !== "string" || !/^\d+$/.test(id)) return NextResponse.json({ error: "Notifica non valida." }, { status: 400 });
  await prisma.notification.updateMany({ where: { id: BigInt(id), userId: session.user.id }, data: { readAt: new Date() } });
  return NextResponse.json({ read: true }, { headers: { "Cache-Control": "private, no-store" } });
}
