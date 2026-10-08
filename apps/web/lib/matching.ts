import { AnimalSex, AnimalSize, AnimalSpecies, HousingType, PreferredSex, PreferredSpecies, Prisma } from "@prisma/client";

export const MATCH_ENGINE_VERSION = "match-1.0.0";

export const matchingAnimalSelect = {
  id: true,
  name: true,
  slug: true,
  species: true,
  sex: true,
  size: true,
  birthDate: true,
  isSterilized: true,
  hasSpecialNeeds: true,
  weightKg: true,
  adoptionFeeCents: true,
  behaviorProfile: {
    select: {
      energyLevel: true,
      goodWithChildren: true,
      goodWithDogs: true,
      goodWithCats: true,
      houseTrained: true,
      aloneToleranceHours: true,
      trainingNeeds: true,
      groomingNeeds: true,
      exerciseMinPerDay: true,
      suitableForFirstTime: true,
      needsGarden: true,
    },
  },
  shelter: {
    select: {
      name: true,
      latitude: true,
      longitude: true,
      comune: { select: { id: true, name: true, latitude: true, longitude: true } },
    },
  },
} as const satisfies Prisma.AnimalSelect;

export type MatchingAnimal = Prisma.AnimalGetPayload<{
  select: typeof matchingAnimalSelect;
}>;

export type MatchProfile = {
  preferredSpecies: PreferredSpecies;
  housingType: HousingType;
  housingSizeSqm: number;
  hasOutdoorSpace: boolean;
  outdoorSpaceSqm: number;
  householdAdults: number;
  childrenAges: number[];
  existingDogs: number;
  existingCats: number;
  hoursAlonePerDay: number;
  activityLevel: number;
  experienceLevel: "first_time" | "some" | "experienced";
  groomingCapacity: number;
  trainingCapacity: number;
  monthlyBudgetEur: number | null;
  preferredSizes: AnimalSize[];
  preferredAgeBands: ("puppy" | "young" | "adult" | "senior")[];
  preferredSex: PreferredSex;
  searchComuneId: number;
  searchRadiusKm: number;
  searchLocation: { latitude: number; longitude: number };
  dealbreakers: string[];
};

export type AdopterAnswers = Omit<MatchProfile, "searchComuneId" | "searchLocation"> & {
  searchComuneId: number | null;
  currentStep: number;
  searchComune?: { id: number; name: string; provinceCode: string; region: string } | null;
};

export type MatchResult = {
  animal: {
    id: string;
    name: string;
    slug: string;
    species: AnimalSpecies;
    sex: AnimalSex;
    size: AnimalSize | null;
    shelter: { name: string; comune: { name: string } };
  };
  score: number;
  distanceKm: number | null;
  isFavorite?: boolean;
  explanationIt?: string | null;
  reasons: string[];
  considerations: string[];
  dimensions: { name: string; score: number; weight: number }[];
};

export type MatchingResponse = {
  totalAvailable: number;
  eligibleCount: number;
  belowThresholdCount: number;
  outsideRadiusCount: number;
  excludedCounts: Record<string, number>;
  results: MatchResult[];
  allResults: MatchResult[];
};

export const MATCHING_WEIGHTS = {
  energy: 0.2,
  space: 0.15,
  timeAlone: 0.15,
  household: 0.15,
  experience: 0.1,
  care: 0.1,
  preferences: 0.1,
  practical: 0.05,
} as const;

const weights = MATCHING_WEIGHTS;

const exclusionLabels: Record<string, string> = {
  species: "specie diversa da quella scelta",
  children: "non compatibile con bambini",
  dogs: "non compatibile con cani già presenti",
  cats: "non compatibile con gatti già presenti",
  noSpecialNeeds: "ha esigenze speciali",
  largeDogWeight: "pesa più di 25 kg",
  largeDogEstimate: "taglia grande usata come stima prudenziale del peso",
  houseTrained: "non è abituato alla vita in casa",
  sterilized: "non è sterilizzato",
  goodWithChildren: "non risulta adatto ai bambini",
  goodWithDogs: "non risulta adatto ai cani",
  goodWithCats: "non risulta adatto ai gatti",
  puppy: "è un cucciolo",
};

const clamp = (value: number) => Math.max(0, Math.min(100, value));

const sizeOrder: AnimalSize[] = ["small", "medium", "large", "xlarge"];
const ageOrder = ["puppy", "young", "adult", "senior"] as const;

function ageInMonths(birthDate: Date | null) {
  if (!birthDate) return null;
  const now = new Date();
  const calendarMonths = (now.getFullYear() - birthDate.getFullYear()) * 12 + now.getMonth() - birthDate.getMonth();
  return Math.max(0, calendarMonths - (now.getDate() < birthDate.getDate() ? 1 : 0));
}

function ageBand(months: number | null) {
  if (months === null) return null;
  if (months < 12) return "puppy";
  if (months < 24) return "young";
  if (months < 96) return "adult";
  return "senior";
}

function distanceKm(a: { latitude: number; longitude: number }, b: { latitude: number; longitude: number }) {
  const radians = (degrees: number) => degrees * Math.PI / 180;
  const latitudeDelta = radians(b.latitude - a.latitude);
  const longitudeDelta = radians(b.longitude - a.longitude);
  const value = Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(radians(a.latitude)) * Math.cos(radians(b.latitude)) * Math.sin(longitudeDelta / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(value), Math.sqrt(1 - value));
}

function scoreAnimal(profile: MatchProfile, animal: MatchingAnimal) {
  const behavior = animal.behaviorProfile;
  const exclusions: string[] = [];
  const considerations = new Set<string>();
  const childCompatibility = behavior?.goodWithChildren ?? "unknown";
  const dogCompatibility = behavior?.goodWithDogs ?? "unknown";
  const catCompatibility = behavior?.goodWithCats ?? "unknown";
  const houseTraining = behavior?.houseTrained ?? "unknown";
  const gardenNeed = behavior?.needsGarden ?? "unknown";
  const firstTimeSuitability = behavior?.suitableForFirstTime ?? "unknown";
  const animalAge = ageInMonths(animal.birthDate);
  const animalAgeBand = ageBand(animalAge);
  const youngestChild = profile.childrenAges.length ? Math.min(...profile.childrenAges) : null;
  const hasShelterCoordinates = animal.shelter.latitude !== null && animal.shelter.longitude !== null;
  const latitude = hasShelterCoordinates ? animal.shelter.latitude : animal.shelter.comune.latitude;
  const longitude = hasShelterCoordinates ? animal.shelter.longitude : animal.shelter.comune.longitude;
  const distance = latitude !== null && longitude !== null
    ? distanceKm(profile.searchLocation, { latitude: Number(latitude), longitude: Number(longitude) })
    : null;

  if (childCompatibility === "unknown") considerations.add("Compatibilità con i bambini non ancora valutata.");
  if (dogCompatibility === "unknown") considerations.add("Convivenza con cani non ancora valutata.");
  if (catCompatibility === "unknown") considerations.add("Convivenza con gatti non ancora valutata.");
  if (houseTraining === "unknown") considerations.add("Abitudine alla vita in casa da verificare con il rifugio.");
  if (gardenNeed === "unknown") considerations.add("Il rifugio non ha ancora valutato se serve uno spazio esterno.");
  if (firstTimeSuitability === "unknown") considerations.add("Idoneità per chi è alla prima esperienza non valutata.");

  if (profile.preferredSpecies !== "either" && profile.preferredSpecies !== animal.species) exclusions.push("species");
  if (youngestChild !== null && youngestChild < 6 && childCompatibility === "no") exclusions.push("children");
  if (profile.existingDogs > 0 && dogCompatibility === "no") exclusions.push("dogs");
  if (profile.existingCats > 0 && catCompatibility === "no") exclusions.push("cats");

  const deals = new Set(profile.dealbreakers);
  if (deals.has("no_special_needs") && animal.hasSpecialNeeds) exclusions.push("noSpecialNeeds");
  if (deals.has("no_dogs_over_25kg") && animal.species === "dog" &&
    (animal.weightKg !== null ? Number(animal.weightKg) > 25 : animal.size === "large" || animal.size === "xlarge")) {
    exclusions.push(animal.weightKg === null ? "largeDogEstimate" : "largeDogWeight");
  }
  if (deals.has("must_be_house_trained") && houseTraining === "no") exclusions.push("houseTrained");
  if (deals.has("must_be_good_with_children") && (childCompatibility === "no" || (childCompatibility === "older_only" && youngestChild !== null && youngestChild < 12))) exclusions.push("goodWithChildren");
  if (deals.has("must_be_good_with_dogs") && dogCompatibility === "no") exclusions.push("goodWithDogs");
  if (deals.has("must_be_good_with_cats") && catCompatibility === "no") exclusions.push("goodWithCats");
  if (deals.has("must_be_sterilized") && animal.isSterilized === false) exclusions.push("sterilized");
  if (deals.has("no_puppies") && animalAgeBand === "puppy") exclusions.push("puppy");

  if (deals.has("must_be_sterilized") && animal.isSterilized == null) considerations.add("Stato di sterilizzazione da verificare con il rifugio.");
  if (deals.has("no_puppies") && animalAgeBand === null) considerations.add("Età da verificare: il rifugio non l'ha indicata.");

  if (exclusions.length) return { exclusions, result: null };

  const dimensions: MatchResult["dimensions"] = [];
  const addDimension = (name: string, score: number, weight: number) => {
    dimensions.push({ name, score: clamp(score), weight });
  };

  const energy = behavior?.energyLevel;
  let energyScore = 65;
  if (energy == null) {
    considerations.add("Attività dell’animale non ancora valutata.");
  } else {
    const gap = Math.abs(profile.activityLevel - energy);
    energyScore = [100, 82, 55, 28, 8][gap] ?? 8;
    if (energy > profile.activityLevel) energyScore -= 10 * (energy - profile.activityLevel - 1);
  }
  if (behavior?.exerciseMinPerDay != null) {
    const offered = [20, 40, 60, 90, 120][profile.activityLevel - 1];
    if (offered < behavior.exerciseMinPerDay) {
      energyScore -= Math.min(25, (behavior.exerciseMinPerDay - offered) / 2);
    }
  } else {
    considerations.add("Tempo di attività quotidiana non indicato dal rifugio.");
  }
  addDimension("Attività", energyScore, weights.energy);

  const spaceMatrix: Record<HousingType, number[]> = {
    apartment: [100, 85, 55, 30],
    house_no_garden: [100, 95, 75, 55],
    house_with_garden: [95, 100, 100, 95],
    farm: [90, 100, 100, 100],
  };
  let space = animal.size ? spaceMatrix[profile.housingType][sizeOrder.indexOf(animal.size)] : 65;
  if (animal.size == null) considerations.add("Taglia non indicata dal rifugio.");
  if (gardenNeed === "yes" && !profile.hasOutdoorSpace) space -= 35;
  if (gardenNeed === "preferred" && !profile.hasOutdoorSpace) space -= 12;
  if (profile.housingSizeSqm < 50 && (animal.size === "large" || animal.size === "xlarge")) space -= 15;
  if (gardenNeed === "unknown") considerations.add("Il rifugio non ha ancora valutato se serve uno spazio esterno.");
  if (animal.species === "cat") space = Math.max(space, 85);
  addDimension("Spazio", space, weights.space);

  const timeAlone = behavior?.aloneToleranceHours;
  let timeScore = 65;
  if (timeAlone == null) {
    considerations.add("La tolleranza alla solitudine non è ancora nota.");
  } else {
    const surplus = timeAlone - profile.hoursAlonePerDay;
    timeScore = surplus >= 2 ? 100 : surplus >= 0 ? 90 : surplus >= -1 ? 65 : surplus >= -2 ? 40 : surplus >= -4 ? 15 : 0;
  }
  if (animalAgeBand === "puppy" && profile.hoursAlonePerDay > 4) timeScore = Math.min(timeScore, 30);
  addDimension("Tempo da solo", timeScore, weights.timeAlone);

  let household = 100;
  let householdUnknown = false;
  if (youngestChild !== null) {
    if (childCompatibility === "unknown") {
      householdUnknown = true;
    } else if (childCompatibility === "older_only") {
      household -= youngestChild < 12 ? 45 : 5;
      considerations.add("Il rifugio consiglia la convivenza con bambini più grandi.");
    }
  }
  if (profile.existingDogs > 0) {
    if (dogCompatibility === "unknown") {
      householdUnknown = true;
    } else if (dogCompatibility === "selective") household -= 20;
  }
  if (profile.existingCats > 0) {
    if (catCompatibility === "unknown") {
      householdUnknown = true;
    } else if (catCompatibility === "selective") household -= 20;
  }
  if (youngestChild !== null && youngestChild < 6 && (animal.size === "large" || animal.size === "xlarge") && (energy ?? 3) >= 4) household -= 15;
  if (householdUnknown) household = 65 + (household - 100);
  addDimension("Nucleo familiare", household, weights.household);

  const demand = behavior?.trainingNeeds;
  let experience = 65;
  if (demand == null || (profile.experienceLevel === "first_time" && firstTimeSuitability === "unknown")) {
    considerations.add("Impegno educativo non ancora valutato.");
  } else {
    const userLevel = { first_time: 1, some: 2, experienced: 3 }[profile.experienceLevel];
    const demandLevel = demand <= 2 ? 1 : demand <= 3 ? 2 : 3;
    experience = userLevel >= demandLevel ? 100 : userLevel === demandLevel - 1 ? 60 : 25;
    if (firstTimeSuitability === "yes" && profile.experienceLevel === "first_time") experience = Math.min(100, experience + 20);
    if (firstTimeSuitability === "no" && profile.experienceLevel === "first_time") experience = Math.min(experience, 30);
  }
  addDimension("Esperienza", experience, weights.experience);

  const careScore = (capacity: number, need: number | null, label: string) => {
    if (need == null) {
      considerations.add(`${label} non indicato dal rifugio.`);
      return 65;
    }
    return capacity >= need ? 100 : 100 - 30 * (need - capacity);
  };
  addDimension(
    "Cura ed educazione",
    (careScore(profile.groomingCapacity, behavior?.groomingNeeds ?? null, "Cura del pelo") +
      careScore(profile.trainingCapacity, behavior?.trainingNeeds ?? null, "Impegno educativo")) / 2,
    weights.care,
  );

  const sizePreference = animal.size === null
    ? 65
    : profile.preferredSizes.length === 0
      ? 100
      : profile.preferredSizes.includes(animal.size)
        ? 100
        : profile.preferredSizes.some((preferred) => Math.abs(sizeOrder.indexOf(animal.size!) - sizeOrder.indexOf(preferred)) === 1)
          ? 60
          : 20;
  const agePreference = profile.preferredAgeBands.length === 0
    ? 100
    : animalAgeBand === null
      ? 65
      : profile.preferredAgeBands.includes(animalAgeBand)
        ? 100
        : profile.preferredAgeBands.some((preferred) => Math.abs(ageOrder.indexOf(animalAgeBand as (typeof ageOrder)[number]) - ageOrder.indexOf(preferred)) === 1)
          ? 65
          : 30;
  const sexPreference = animal.sex === "unknown"
    ? 65
    : profile.preferredSex === "any"
      ? 100
      : animal.sex === profile.preferredSex ? 100 : 70;
  if (animal.size === null) considerations.add("Taglia non indicata: preferenza non valutata.");
  if (animal.sex === "unknown") considerations.add("Sesso non indicato: preferenza non valutata.");
  if (animalAgeBand === null) considerations.add("Età non indicata: la preferenza anagrafica non è stata valutata.");
  addDimension("Preferenze", sizePreference * 0.4 + agePreference * 0.4 + sexPreference * 0.2, weights.preferences);

  const monthlyBudget = profile.monthlyBudgetEur;
  const fee = animal.adoptionFeeCents == null ? null : animal.adoptionFeeCents / 100;
  const feeScore = fee == null || monthlyBudget == null || monthlyBudget <= 0
    ? 100
    : fee <= monthlyBudget * 0.2 ? 100 : fee <= monthlyBudget * 0.5 ? 80 : 50;
  const needsScore = animal.hasSpecialNeeds ? profile.experienceLevel === "experienced" ? 85 : 55 : 100;
  const distanceScore = distance === null
    ? 65
    : distance / profile.searchRadiusKm <= 0.33 ? 100
      : distance / profile.searchRadiusKm <= 0.66 ? 85
        : distance <= profile.searchRadiusKm ? 70 : 40;
  if (distance === null) considerations.add("Distanza non disponibile per questo rifugio.");
  else if (distance > profile.searchRadiusKm) considerations.add("Questo rifugio è oltre il raggio scelto.");
  addDimension("Aspetti pratici", distanceScore * 0.5 + feeScore * 0.2 + needsScore * 0.3, weights.practical);

  const score = Math.round(dimensions.reduce((total, dimension) => total + dimension.score * dimension.weight, 0));
  const reasons = dimensions
    .filter((dimension) => dimension.score >= 85)
    .sort((a, b) => b.score * b.weight - a.score * a.weight)
    .slice(0, 3)
    .map((dimension) => `Buona compatibilità su ${dimension.name.toLowerCase()}.`);
  for (const dimension of dimensions) {
    if (dimension.score < 55) considerations.add(`Possibile difficoltà su ${dimension.name.toLowerCase()}.`);
  }

  return {
    exclusions,
    result: {
      animal: {
        id: animal.id,
        name: animal.name,
        slug: animal.slug,
        species: animal.species,
        sex: animal.sex,
        size: animal.size,
        shelter: animal.shelter,
      },
      score,
      distanceKm: distance === null ? null : Math.round(distance * 10) / 10,
      reasons,
      considerations: [...considerations],
      dimensions,
    } satisfies MatchResult,
  };
}

export function findMatches(profile: MatchProfile, animals: MatchingAnimal[]) {
  const excludedCounts: Record<string, number> = {};
  const scored = animals.flatMap((animal) => {
    const { exclusions, result } = scoreAnimal(profile, animal);
    for (const reason of exclusions) excludedCounts[reason] = (excludedCounts[reason] ?? 0) + 1;
    return result ? [result] : [];
  });
  scored.sort((a, b) => b.score - a.score || a.animal.name.localeCompare(b.animal.name, "it"));
  const inRadius = scored.filter((match) => match.distanceKm === null || match.distanceKm <= profile.searchRadiusKm);
  const aboveThreshold = inRadius.filter((match) => match.score >= 45);

  return {
    totalAvailable: animals.length,
    eligibleCount: inRadius.length,
    belowThresholdCount: inRadius.filter((match) => match.score < 45).length,
    outsideRadiusCount: scored.length - inRadius.length,
    excludedCounts: Object.fromEntries(
      Object.entries(excludedCounts).map(([key, count]) => [exclusionLabels[key] ?? key, count]),
    ),
    results: aboveThreshold.slice(0, 20),
    allResults: scored,
  };
}
