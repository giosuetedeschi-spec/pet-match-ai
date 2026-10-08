import { AnimalStatus, ShelterStatus } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { findAdopterProfile } from "@/lib/adopter-profile";
import { prisma } from "@/lib/prisma";
async function profileFor(request: NextRequest) {
  const profile = await findAdopterProfile(request);
  return profile ? { id: profile.id } : null;
}

export async function GET(request: NextRequest) {
  const profile = await profileFor(request);
  if (!profile) return NextResponse.json({ favorites: [] }, { headers: { "Cache-Control": "private, no-store" } });
  const favorites = await prisma.favorite.findMany({
    where: { profileId: profile.id },
    orderBy: { createdAt: "desc" },
    select: { animal: { select: { id: true, name: true, slug: true, species: true, size: true, shelter: { select: { name: true, comune: { select: { name: true } } } } } } },
  });
  return NextResponse.json({ favorites: favorites.map(({ animal }) => animal) }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function POST(request: NextRequest) {
  const profile = await profileFor(request);
  if (!profile) return NextResponse.json({ error: "Completa prima il profilo di matching." }, { status: 409 });
  let animalId: unknown;
  try { animalId = (await request.json()).animalId; } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (typeof animalId !== "string" || animalId.length > 64) return NextResponse.json({ error: "Animale non valido." }, { status: 400 });
  const animal = await prisma.animal.findFirst({ where: { id: animalId, status: AnimalStatus.available, publishedAt: { not: null }, deletedAt: null, shelter: { status: ShelterStatus.active, deletedAt: null } }, select: { id: true } });
  if (!animal) return NextResponse.json({ error: "Questo animale non è più disponibile." }, { status: 404 });
  const favorite = await prisma.favorite.upsert({ where: { profileId_animalId: { profileId: profile.id, animalId } }, create: { profileId: profile.id, animalId }, update: {} });
  return NextResponse.json({ favorite: true, id: favorite.animalId }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function DELETE(request: NextRequest) {
  const profile = await profileFor(request);
  if (!profile) return NextResponse.json({ favorite: false });
  const animalId = request.nextUrl.searchParams.get("animalId");
  if (!animalId) return NextResponse.json({ error: "Animale non valido." }, { status: 400 });
  await prisma.favorite.deleteMany({ where: { profileId: profile.id, animalId } });
  return NextResponse.json({ favorite: false }, { headers: { "Cache-Control": "private, no-store" } });
}
