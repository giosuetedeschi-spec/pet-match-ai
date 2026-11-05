import { Prisma } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { parseAnimalInput } from "@/lib/animal-input";
import { getShelterAccess, memberShelter } from "@/lib/shelter-access";
import { prisma } from "@/lib/prisma";

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export async function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  const { id } = await context.params;
  const animal = await prisma.animal.findFirst({
    where: { id, shelterId: { in: access.memberships.map(({ shelterId }) => shelterId) }, deletedAt: null },
    include: { behaviorProfile: true, media: { where: { deletedAt: null }, orderBy: [{ sortOrder: "asc" }, { createdAt: "asc" }] } },
  });
  if (!animal) return NextResponse.json({ error: "Scheda non trovata." }, { status: 404 });
  return NextResponse.json({ animal }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function PUT(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  const { id } = await context.params;
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!isRecord(body)) return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });
  const shelterId = typeof body.shelterId === "string" ? body.shelterId : "";
  if (!memberShelter(access, shelterId)) return NextResponse.json({ error: "Non hai accesso a questo rifugio." }, { status: 403 });
  const { errors, data, behavior } = parseAnimalInput(body);
  if (errors.length) return NextResponse.json({ error: "Controlla i campi indicati.", errors }, { status: 400 });
  const existing = await prisma.animal.findFirst({ where: { id, shelterId, deletedAt: null }, select: { id: true, status: true } });
  if (!existing) return NextResponse.json({ error: "Scheda non trovata." }, { status: 404 });
  if (existing.status !== "draft") return NextResponse.json({ error: "Le schede pubblicate non possono essere modificate da questo flusso." }, { status: 409 });
  try {
    const isProfileComplete = [behavior.energyLevel, behavior.sociabilityPeople, behavior.noiseTolerance, behavior.aloneToleranceHours, behavior.trainingNeeds, behavior.groomingNeeds, behavior.exerciseMinPerDay].every((value) => value !== null);
    const animal = await prisma.$transaction(async (transaction) => {
      await transaction.animal.update({ where: { id }, data });
      await transaction.animalBehaviorProfile.upsert({
        where: { animalId: id },
        create: { animalId: id, ...behavior, assessedBy: isProfileComplete ? access.userId : null, assessedAt: isProfileComplete ? new Date() : null },
        update: { ...behavior, assessedBy: isProfileComplete ? access.userId : null, assessedAt: isProfileComplete ? new Date() : null },
      });
      return transaction.animal.findUniqueOrThrow({ where: { id }, select: { id: true, status: true, slug: true } });
    });
    return NextResponse.json({ animal }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002") {
      return NextResponse.json({ error: "Il microchip risulta già associato a un altro animale." }, { status: 409 });
    }
    return NextResponse.json({ error: "Non è stato possibile salvare la scheda." }, { status: 503 });
  }
}
