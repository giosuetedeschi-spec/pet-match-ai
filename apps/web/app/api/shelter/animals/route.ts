import { Prisma } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { animalSlug, parseAnimalInput } from "@/lib/animal-input";
import { getShelterAccess, memberShelter } from "@/lib/shelter-access";
import { createRecordId } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export async function GET(request: NextRequest) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  const shelterIds = access.memberships.map(({ shelterId }) => shelterId);
  const animals = await prisma.animal.findMany({
    where: { shelterId: { in: shelterIds }, deletedAt: null },
    orderBy: [{ updatedAt: "desc" }, { id: "asc" }],
    select: {
      id: true, name: true, slug: true, species: true, status: true, updatedAt: true,
      shelterId: true, shelter: { select: { name: true } },
      media: { where: { deletedAt: null, processingStatus: "ready", isPrimary: true }, take: 1, select: { id: true, altTextIt: true, altTextEn: true } },
    },
  });
  return NextResponse.json({ shelters: access.memberships, animals }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function POST(request: NextRequest) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!isRecord(body)) return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });
  const shelterId = typeof body.shelterId === "string" ? body.shelterId : "";
  if (!memberShelter(access, shelterId)) return NextResponse.json({ error: "Non hai accesso a questo rifugio." }, { status: 403 });

  const { errors, data, behavior } = parseAnimalInput(body);
  if (errors.length) return NextResponse.json({ error: "Controlla i campi indicati.", errors }, { status: 400 });
  try {
    const profileComplete = [behavior.energyLevel, behavior.sociabilityPeople, behavior.noiseTolerance, behavior.aloneToleranceHours, behavior.trainingNeeds, behavior.groomingNeeds, behavior.exerciseMinPerDay].every((value) => value !== null);
    const animal = await prisma.animal.create({
      data: {
        ...data,
        id: createRecordId(),
        shelterId,
        slug: animalSlug(data.name),
        createdBy: access.userId,
        behaviorProfile: { create: { ...behavior, assessedBy: profileComplete ? access.userId : null, assessedAt: profileComplete ? new Date() : null } },
      },
      select: { id: true, slug: true },
    });
    return NextResponse.json({ animal }, { status: 201, headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002") {
      return NextResponse.json({ error: "Il microchip risulta già associato a un altro animale." }, { status: 409 });
    }
    return NextResponse.json({ error: "Non è stato possibile salvare la scheda." }, { status: 503 });
  }
}
