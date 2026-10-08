import { AnimalStatus, Prisma, ShelterStatus } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { findAdopterProfile } from "@/lib/adopter-profile";
import { findMatches, MATCH_ENGINE_VERSION, matchingAnimalSelect } from "@/lib/matching";
import { deterministicExplanation, generateClaudeExplanation } from "@/lib/matching-explanations";
import { toMatchProfile } from "@/lib/matching-profile";
import { prisma } from "@/lib/prisma";


function privateResponse(response: NextResponse) {
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export async function GET(request: NextRequest) {
  try {
    const adopterProfile = await findAdopterProfile(request);
    if (!adopterProfile) return NextResponse.json({ error: "Completa prima il questionario." }, { status: 409 });
    const profile = await prisma.adopterProfile.findUnique({
      where: { id: adopterProfile.id },
      include: { searchComune: { select: { latitude: true, longitude: true } } },
    });
    if (!profile?.completedAt || !profile.searchComune || profile.searchComuneId === null) {
      return NextResponse.json({ error: "Completa il questionario per vedere i risultati." }, { status: 409 });
    }

    const requestedRadius = Number(request.nextUrl.searchParams.get("radius"));
    const radius = Number.isInteger(requestedRadius) && requestedRadius >= 10 && requestedRadius <= 200
      ? requestedRadius
      : profile.searchRadiusKm;

    const matchProfile = toMatchProfile(profile, radius);

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
    const previousResults = await prisma.matchResult.findMany({
      where: { profileId: profile.id },
      select: { animalId: true, score: true, reasons: true, explanationIt: true, explanationEn: true, notifiedAt: true, engineVersion: true },
    });
    const previousByAnimal = new Map(previousResults.map((item) => [item.animalId, item]));
    const hasSameReasons = (match: typeof matches.results[number], previous: (typeof previousResults)[number] | undefined) =>
      previous?.engineVersion === MATCH_ENGINE_VERSION && previous.score === match.score && JSON.stringify(previous.reasons) === JSON.stringify(match.reasons);
    const explanationByAnimal = new Map<string, { publicText: string; cachedText: string | null }>();
    for (let index = 0; index < matches.results.length; index += 3) {
      const batch = matches.results.slice(index, index + 3);
      const generated = await Promise.all(batch.map(async (match) => {
        const previous = previousByAnimal.get(match.animal.id);
        const cachedText = hasSameReasons(match, previous) ? previous?.explanationIt ?? null : null;
        const aiText = cachedText ?? await generateClaudeExplanation({ profile: matchProfile, match });
        return [match.animal.id, { publicText: aiText ?? deterministicExplanation(match), cachedText: aiText }] as const;
      }));
      generated.forEach(([animalId, explanation]) => explanationByAnimal.set(animalId, explanation));
    }

    await prisma.$transaction([
      prisma.matchResult.deleteMany({ where: { profileId: profile.id } }),
      ...(matches.allResults.length > 0 ? [prisma.matchResult.createMany({
        data: matches.allResults.map((match) => ({
          ...(() => {
            const previous = previousByAnimal.get(match.animal.id);
            const same = hasSameReasons(match, previous);
            const visibleExplanation = explanationByAnimal.get(match.animal.id);
            return {
              notifiedAt: previous?.notifiedAt ?? null,
              explanationIt: visibleExplanation?.cachedText ?? (same ? previous?.explanationIt ?? null : null),
              explanationEn: same ? previous?.explanationEn ?? null : null,
            };
          })(),
          profileId: profile.id,
          animalId: match.animal.id,
          score: match.score,
          breakdown: { dimensions: match.dimensions, distanceKm: match.distanceKm } as Prisma.InputJsonValue,
          reasons: match.reasons as Prisma.InputJsonValue,
          considerations: match.considerations as Prisma.InputJsonValue,
          engineVersion: MATCH_ENGINE_VERSION,
          computedAt: cachedAt,
        })),
      })] : []),
    ]);

    const favoriteIds = new Set((await prisma.favorite.findMany({
      where: { profileId: profile.id },
      select: { animalId: true },
    })).map((favorite) => favorite.animalId));
    const { allResults: _cachedResults, ...publicMatches } = matches;
    return privateResponse(NextResponse.json({
      ...publicMatches,
      radiusKm: radius,
      results: matches.results.map((match) => ({
        ...match,
        isFavorite: favoriteIds.has(match.animal.id),
        explanationIt: explanationByAnimal.get(match.animal.id)?.publicText ?? deterministicExplanation(match),
      })),
    }));
  } catch {
    return NextResponse.json({ error: "Non riesco a calcolare gli abbinamenti in questo momento." }, { status: 503 });
  }
}
