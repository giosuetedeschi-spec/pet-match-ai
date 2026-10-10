import { NextRequest, NextResponse } from "next/server";
import { getRequestSession } from "@/lib/auth";
import { sendShelterDecisionEmail } from "@/lib/mailer";
import { prisma } from "@/lib/prisma";

async function admin(request: Request) {
  const session = await getRequestSession(request);
  return session?.user.role === "platform_admin" ? session : null;
}

export async function GET(request: NextRequest) {
  const session = await admin(request);
  if (!session) return NextResponse.json({ error: "Accesso amministratore richiesto." }, { status: 403 });
  const shelters = await prisma.shelter.findMany({
    where: { status: "pending", deletedAt: null }, orderBy: { createdAt: "asc" },
    select: { id: true, name: true, legalName: true, type: true, taxId: true, email: true, phone: true, addressLine: true, postalCode: true, comune: { select: { name: true, provinceCode: true } }, createdAt: true, members: { take: 1, select: { user: { select: { fullName: true, email: true, emailVerifiedAt: true } } } } },
  });
  return NextResponse.json({ shelters }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function POST(request: NextRequest) {
  const session = await admin(request);
  if (!session) return NextResponse.json({ error: "Accesso amministratore richiesto." }, { status: 403 });
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });
  const input = body as Record<string, unknown>;
  const id = typeof input.shelterId === "string" ? input.shelterId : "";
  const decision = input.decision;
  const reason = typeof input.reason === "string" ? input.reason.trim() : "";
  if (!id || (decision !== "approve" && decision !== "reject") || (decision === "reject" && (reason.length < 5 || reason.length > 2000))) {
    return NextResponse.json({ error: "Decisione o motivazione non valida." }, { status: 400 });
  }
  const applicant = await prisma.shelter.findFirst({ where: { id, status: "pending", deletedAt: null }, select: { name: true, members: { take: 1, select: { user: { select: { email: true, fullName: true, locale: true, emailVerifiedAt: true } } } } } });
  if (!applicant) return NextResponse.json({ error: "Richiesta non trovata o già esaminata." }, { status: 409 });
  const contact = applicant.members[0]?.user;
  if (!contact) return NextResponse.json({ error: "Referente del rifugio non trovato." }, { status: 409 });
  if (decision === "approve" && !contact.emailVerifiedAt) return NextResponse.json({ error: "Prima di approvare serve la verifica dell'email del referente." }, { status: 409 });
  const result = await prisma.shelter.updateMany({
    where: { id, status: "pending", deletedAt: null },
    data: decision === "approve"
      ? { status: "active", approvedAt: new Date(), approvedBy: session.user.id, rejectionReason: null }
      : { status: "archived", rejectionReason: reason },
  });
  if (!result.count) return NextResponse.json({ error: "Richiesta non trovata o già esaminata." }, { status: 409 });
  let emailSent = false;
  try { await sendShelterDecisionEmail({ email: contact.email, name: contact.fullName, shelter: applicant.name, approved: decision === "approve", reason, locale: contact.locale }); emailSent = true; } catch { /* Keep the decision; delivery can be retried through the normal support workflow. */ }
  return NextResponse.json({ decided: true, status: decision === "approve" ? "active" : "archived", emailSent });
}
