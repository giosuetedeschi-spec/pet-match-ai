import { randomBytes } from "node:crypto";
import { AnimalStatus, Prisma, ShelterStatus } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { findMatches, matchingAnimalSelect, type MatchProfile } from "@/lib/matching";
import { prisma } from "@/lib/prisma";

const cookieName = "petmatch-adopter";
const engineVersion = "match-1.0.0";

function newId() {
  return randomBytes(13).toString("hex");
}

function setCookie(response: NextResponse, token: string) {
  response.cookies.set(cookieName, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 180,
  });
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export async function GET(request: NextRequest) {
  const token = request.cookies.get(cookieName)?.value;
  if (!token) return NextResponse.json({ error: "Completa prima il questionario." }, { status: 409 });

  try {
    const profile = await prisma.adopterProfile.findUnique({
      where: { anonymousToken: token },
      include: { searchComune: { select: { latitude: true, longitude: true } } },
    });
    if (!profile?.completedAt || !profile.searchComune || profile.searchComuneId === null) {
      return NextResponse.json({ error: "Completa il questionario per vedere i risultati." }, { status: 409 });
    }

    const requestedRadius = Number(request.nextUrl.searchParams.get("radius"));
    const radius = Number.isInteger(requestedRadius) && requestedRadius >= 10 && requestedRadius <= 200
      ? requestedRadius
      : profile.searchRadiusKm;

    const matchProfile: MatchProfile = {
      preferredSpecies: profile.preferredSpecies,
      housingType: profile.housingType!,
      housingSizeSqm: profile.housingSizeSqm!,
      hasOutdoorSpace: profile.hasOutdoorSpace!,
      outdoorSpaceSqm: profile.outdoorSpaceSqm!,
      householdAdults: profile.householdAdults!,
      childrenAges: Array.isArray(profile.childrenAges) ? profile.childrenAges.map(Number) : [],
      existingDogs: profile.existingDogs,
      existingCats: profile.existingCats,
      hoursAlonePerDay: profile.hoursAlonePerDay!,
      activityLevel: profile.activityLevel!,
      experienceLevel: profile.experienceLevel as MatchProfile["experienceLevel"],
      groomingCapacity: profile.groomingCapacity!,
      trainingCapacity: profile.trainingCapacity!,
      monthlyBudgetEur: profile.monthlyBudgetEur,
      preferredSizes: Array.isArray(profile.preferredSizes) ? profile.preferredSizes as MatchProfile["preferredSizes"] : [],
      preferredAgeBands: Array.isArray(profile.preferredAgeBands) ? profile.preferredAgeBands as MatchProfile["preferredAgeBands"] : [],
      preferredSex: profile.preferredSex,
      searchComuneId: profile.searchComuneId,
      searchRadiusKm: radius,
      searchLocation: {
        latitude: Number(profile.searchComune.latitude),
        longitude: Number(profile.searchComune.longitude),
      },
      dealbreakers: Array.isArray(profile.dealbreakers) ? profile.dealbreakers as string[] : [],
    };

    const animals = await prisma.animal.findMany({
      where: {
        status: AnimalStatus.available,
        publishedAt: { not: null },
        deletedAt: null,
        shelter: { status: ShelterStatus.active, deletedAt: null },
      },
      select: matchingAnimalSelect,
    });
    const matches = findMatches(matchProfile, animals);
    const cachedAt = new Date();

    await prisma.$transaction([
      prisma.matchResult.deleteMany({ where: { profileId: profile.id } }),
      ...(matches.allResults.length > 0 ? [prisma.matchResult.createMany({
        data: matches.allResults.map((match) => ({
          profileId: profile.id,
          animalId: match.animal.id,
          score: match.score,
          breakdown: { dimensions: match.dimensions, distanceKm: match.distanceKm } as Prisma.InputJsonValue,
          reasons: match.reasons as Prisma.InputJsonValue,
          considerations: match.considerations as Prisma.InputJsonValue,
          engineVersion,
          computedAt: cachedAt,
        })),
      })] : []),
    ]);

    const favoriteIds = new Set((await prisma.favorite.findMany({
      where: { profileId: profile.id },
      select: { animalId: true },
    })).map((favorite) => favorite.animalId));
    const { allResults: _cachedResults, ...publicMatches } = matches;
    return setCookie(NextResponse.json({
      ...publicMatches,
      radiusKm: radius,
      results: matches.results.map((match) => ({ ...match, isFavorite: favoriteIds.has(match.animal.id) })),
    }), token);
  } catch {
    return NextResponse.json({ error: "Non riesco a calcolare gli abbinamenti in questo momento." }, { status: 503 });
  }
}
