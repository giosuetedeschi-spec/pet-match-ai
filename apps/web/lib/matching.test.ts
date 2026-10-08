import assert from "node:assert/strict";
import { test } from "node:test";
import { Prisma } from "@prisma/client";
import { findMatches, MATCHING_WEIGHTS, type MatchProfile, type MatchingAnimal } from "./matching";

const profile: MatchProfile = {
  preferredSpecies: "dog",
  housingType: "apartment",
  housingSizeSqm: 80,
  hasOutdoorSpace: false,
  outdoorSpaceSqm: 0,
  householdAdults: 2,
  childrenAges: [],
  existingDogs: 0,
  existingCats: 0,
  hoursAlonePerDay: 6,
  activityLevel: 3,
  experienceLevel: "first_time",
  groomingCapacity: 2,
  trainingCapacity: 3,
  monthlyBudgetEur: null,
  preferredSizes: ["small", "medium"],
  preferredAgeBands: ["adult"],
  preferredSex: "any",
  searchComuneId: 1,
  searchRadiusKm: 50,
  searchLocation: { latitude: 45, longitude: 9 },
  dealbreakers: ["must_be_house_trained"],
};

function animal(overrides: Partial<MatchingAnimal> = {}): MatchingAnimal {
  return {
    id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    name: "Luna",
    slug: "luna",
    species: "dog",
    sex: "female",
    size: "medium",
    birthDate: new Date("2023-07-01T00:00:00Z"),
    isSterilized: true,
    hasSpecialNeeds: false,
    adoptionFeeCents: null,
    weightKg: null,
    behaviorProfile: {
      energyLevel: 2,
      goodWithChildren: "yes",
      goodWithDogs: "yes",
      goodWithCats: "unknown",
      houseTrained: "yes",
      aloneToleranceHours: 6,
      trainingNeeds: 2,
      groomingNeeds: 2,
      exerciseMinPerDay: 60,
      suitableForFirstTime: "yes",
      needsGarden: "preferred",
    },
    shelter: {
      name: "Rifugio",
      latitude: new Prisma.Decimal(45 + 12.4 / 111.195),
      longitude: new Prisma.Decimal(9),
      comune: {
        id: 1,
        name: "Milano",
        latitude: new Prisma.Decimal(45),
        longitude: new Prisma.Decimal(9),
      },
    },
    ...overrides,
  } as MatchingAnimal;
}

test("dimension weights sum to one", () => {
  assert.equal(Object.values(MATCHING_WEIGHTS).reduce((sum, weight) => sum + weight, 0), 1);
});

test("reproduces Luna's documented score of 91", () => {
  const result = findMatches(profile, [animal()]).allResults[0];
  assert.ok(result);
  assert.equal(result.score, 91);
  assert.equal(result.distanceKm, 12.4);
});

test("reproduces Thor's documented score of 46", () => {
  const thor = animal({
    id: "01ARZ3NDEKTSV4RRFFQ69G5FAW",
    name: "Thor",
    slug: "thor",
    sex: "male",
    size: "large",
    birthDate: new Date("2025-03-01T00:00:00Z"),
    behaviorProfile: {
      energyLevel: 5,
      goodWithChildren: "unknown",
      goodWithDogs: "unknown",
      goodWithCats: "unknown",
      houseTrained: "partially",
      aloneToleranceHours: 3,
      trainingNeeds: 4,
      groomingNeeds: 3,
      exerciseMinPerDay: 120,
      suitableForFirstTime: "no",
      needsGarden: "yes",
    },
    shelter: {
      name: "Rifugio",
      latitude: new Prisma.Decimal(45 + 8 / 111.195),
      longitude: new Prisma.Decimal(9),
      comune: {
        id: 1,
        name: "Milano",
        latitude: new Prisma.Decimal(45),
        longitude: new Prisma.Decimal(9),
      },
    },
  });
  assert.equal(findMatches(profile, [thor]).allResults[0]?.score, 46);
});

test("a deal-breaker excludes instead of lowering the score", () => {
  const incompatible = animal({
    behaviorProfile: { ...animal().behaviorProfile!, houseTrained: "no" },
  });
  const matches = findMatches(profile, [incompatible]);
  assert.equal(matches.allResults.length, 0);
  assert.equal(matches.excludedCounts["non è abituato alla vita in casa"], 1);
});

test("the 25 kg dog deal-breaker uses weight and reports a size estimate when weight is missing", () => {
  const byWeight = animal({ weightKg: new Prisma.Decimal(26) });
  const excluded = findMatches({ ...profile, dealbreakers: ["no_dogs_over_25kg"] }, [byWeight]);
  assert.equal(excluded.allResults.length, 0);

  const bySize = animal({ weightKg: null, size: "large" });
  const estimated = findMatches({ ...profile, dealbreakers: ["no_dogs_over_25kg"] }, [bySize]);
  assert.equal(estimated.allResults.length, 0);
  assert.equal(estimated.excludedCounts["taglia grande usata come stima prudenziale del peso"], 1);
});

test("unknown behavior remains a visible consideration", () => {
  const unknown = animal({ behaviorProfile: null });
  const result = findMatches(profile, [unknown]).allResults[0];
  assert.ok(result);
  assert.ok(result.dimensions.some((dimension) => dimension.score === 65));
  assert.ok(result.considerations.length > 0);
});

test("safety exclusions apply to young children even without a selected deal-breaker", () => {
  const familyProfile = { ...profile, dealbreakers: [], childrenAges: [5] };
  const incompatible = animal({ behaviorProfile: { ...animal().behaviorProfile!, goodWithChildren: "no" } });
  const matches = findMatches(familyProfile, [incompatible]);
  assert.equal(matches.allResults.length, 0);
  assert.equal(matches.excludedCounts["non compatibile con bambini"], 1);
});

test("safety exclusions apply to resident dogs and cats without a selected deal-breaker", () => {
  const incompatibleDog = animal({ behaviorProfile: { ...animal().behaviorProfile!, goodWithDogs: "no" } });
  const dogMatch = findMatches({ ...profile, dealbreakers: [], existingDogs: 1 }, [incompatibleDog]);
  assert.equal(dogMatch.allResults.length, 0);
  assert.equal(dogMatch.excludedCounts["non compatibile con cani già presenti"], 1);

  const incompatibleCat = animal({ behaviorProfile: { ...animal().behaviorProfile!, goodWithCats: "no" } });
  const catMatch = findMatches({ ...profile, dealbreakers: [], existingCats: 1 }, [incompatibleCat]);
  assert.equal(catMatch.allResults.length, 0);
  assert.equal(catMatch.excludedCounts["non compatibile con gatti già presenti"], 1);
});

test("scores 10,000 animals in under 300 ms", () => {
  const base = animal();
  const animals = Array.from({ length: 10_000 }, (_, index) => ({
    ...base,
    id: index.toString().padStart(26, "0"),
    name: `Animale ${index}`,
  }));
  const startedAt = performance.now();
  const results = findMatches(profile, animals);
  const elapsedMs = performance.now() - startedAt;
  assert.equal(results.allResults.length, 10_000);
  assert.ok(elapsedMs < 300, `10,000 animals took ${elapsedMs.toFixed(1)} ms`);
});
