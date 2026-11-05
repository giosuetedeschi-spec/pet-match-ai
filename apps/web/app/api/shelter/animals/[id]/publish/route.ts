import { AnimalStatus } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { animalPublishBlockers } from "@/lib/animal-validation";
import { getShelterAccess } from "@/lib/shelter-access";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  const { id } = await context.params;
  const animal = await prisma.animal.findFirst({
    where: { id, shelterId: { in: access.memberships.map(({ shelterId }) => shelterId) }, deletedAt: null },
    include: {
      shelter: { select: { status: true } },
      behaviorProfile: true,
      media: { where: { kind: "photo", deletedAt: null }, select: { altTextIt: true, altTextEn: true, processingStatus: true, deletedAt: true } },
    },
  });
  if (!animal) return NextResponse.json({ error: "Scheda non trovata." }, { status: 404 });
  if (animal.shelter.status !== "active") return NextResponse.json({ error: "La struttura deve essere approvata prima di pubblicare." }, { status: 403 });
  if (animal.status !== AnimalStatus.draft && animal.status !== AnimalStatus.available) {
    return NextResponse.json({ error: "Solo una scheda in bozza può essere pubblicata." }, { status: 409 });
  }
  const blockers = animalPublishBlockers(animal);
  if (blockers.length) return NextResponse.json({ error: "Completa i requisiti prima della pubblicazione.", blockers }, { status: 422 });
  const published = await prisma.animal.update({
    where: { id },
    data: { status: AnimalStatus.available, publishedAt: animal.publishedAt ?? new Date() },
    select: { id: true, slug: true, status: true, publishedAt: true },
  });
  return NextResponse.json({ animal: published }, { headers: { "Cache-Control": "no-store" } });
}
