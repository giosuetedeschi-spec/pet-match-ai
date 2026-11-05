import type { AnimalSex, AnimalSize, AnimalSpecies, Prisma } from "@prisma/client";
import { isDate, validateAnimalDraft } from "@/lib/animal-validation";

const enumValues = {
  sex: ["male", "female", "unknown"],
  size: ["small", "medium", "large", "xlarge"],
  sterilized: ["yes", "no", "unknown"],
  compatibility: ["yes", "selective", "no", "unknown"],
  children: ["yes", "older_only", "no", "unknown"],
  training: ["yes", "partially", "no", "unknown"],
  suitability: ["yes", "no", "unknown"],
  garden: ["yes", "preferred", "no", "unknown"],
} as const;

function optionalText(value: unknown, max: number, label: string, errors: string[]) {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value !== "string" || value.trim().length > max) {
    errors.push(`${label}: massimo ${max} caratteri.`);
    return null;
  }
  return value.trim();
}

function numeric(value: unknown, min: number, max: number, label: string, errors: string[]) {
  if (value === undefined || value === null || value === "") return null;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    errors.push(`${label}: inserisci un valore tra ${min} e ${max}.`);
    return null;
  }
  return parsed;
}

function choice<T extends readonly string[]>(value: unknown, options: T, fallback: T[number], label: string, errors: string[]) {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value !== "string" || !options.includes(value)) {
    errors.push(`${label}: selezione non valida.`);
    return fallback;
  }
  return value as T[number];
}

export function parseAnimalInput(input: Record<string, unknown>) {
  const validation = validateAnimalDraft(input);
  const errors = [...validation.errors];
  const species = choice(input.species, ["dog", "cat"] as const, "dog", "Specie", errors);
  const sex = choice(input.sex, enumValues.sex, "unknown", "Sesso", errors);
  const size = choice(input.size, enumValues.size, "small", "Taglia", errors);
  const sterilized = choice(input.isSterilized, enumValues.sterilized, "unknown", "Sterilizzazione", errors);
  const vaccinated = choice(input.isVaccinatedSummary, ["yes", "no", "unknown"] as const, "unknown", "Vaccinazioni", errors);
  const microchipNumber = optionalText(input.microchipNumber, 15, "Microchip", errors);
  const weightKg = input.weightKg === undefined || input.weightKg === "" ? null : Number(input.weightKg);
  if (weightKg !== null && (!Number.isFinite(weightKg) || weightKg <= 0 || weightKg > 999.99)) errors.push("Il peso deve essere maggiore di 0 e inferiore a 1000 kg.");
  const fee = input.adoptionFeeEur === undefined || input.adoptionFeeEur === "" ? null : Number(input.adoptionFeeEur);
  if (fee !== null && (!Number.isFinite(fee) || fee < 0 || fee > 42949672 || Math.round(fee * 100) > 4294967295)) errors.push("Il contributo spese non è valido.");
  const birthDate = validation.birthDate && isDate(validation.birthDate) ? new Date(`${validation.birthDate}T00:00:00.000Z`) : null;
  const intakeDate = typeof input.intakeDate === "string" && isDate(input.intakeDate) ? new Date(`${input.intakeDate}T00:00:00.000Z`) : new Date();
  let estimatedBirthDate = birthDate;
  if (!estimatedBirthDate && validation.ageMonths !== null) {
    estimatedBirthDate = new Date();
    estimatedBirthDate.setUTCHours(0, 0, 0, 0);
    estimatedBirthDate.setUTCDate(1);
    estimatedBirthDate.setUTCMonth(estimatedBirthDate.getUTCMonth() - validation.ageMonths);
  }
  const behaviorInput = input.behavior && typeof input.behavior === "object" && !Array.isArray(input.behavior)
    ? input.behavior as Record<string, unknown>
    : {};
  const behavior = {
    energyLevel: numeric(behaviorInput.energyLevel, 1, 5, "Energia", errors),
    sociabilityPeople: numeric(behaviorInput.sociabilityPeople, 1, 5, "Socievolezza", errors),
    goodWithChildren: choice(behaviorInput.goodWithChildren, enumValues.children, "unknown", "Compatibilità bambini", errors),
    goodWithDogs: choice(behaviorInput.goodWithDogs, enumValues.compatibility, "unknown", "Compatibilità cani", errors),
    goodWithCats: choice(behaviorInput.goodWithCats, enumValues.compatibility, "unknown", "Compatibilità gatti", errors),
    houseTrained: choice(behaviorInput.houseTrained, enumValues.training, "unknown", "Abitudine alla casa", errors),
    leashTrained: choice(behaviorInput.leashTrained, enumValues.training, "unknown", "Abitudine al guinzaglio", errors),
    noiseTolerance: numeric(behaviorInput.noiseTolerance, 1, 5, "Tolleranza ai rumori", errors),
    aloneToleranceHours: numeric(behaviorInput.aloneToleranceHours, 0, 24, "Ore da solo", errors),
    trainingNeeds: numeric(behaviorInput.trainingNeeds, 1, 5, "Bisogno di addestramento", errors),
    groomingNeeds: numeric(behaviorInput.groomingNeeds, 1, 5, "Bisogno di toelettatura", errors),
    exerciseMinPerDay: numeric(behaviorInput.exerciseMinPerDay, 0, 1440, "Attività giornaliera", errors),
    suitableForFirstTime: choice(behaviorInput.suitableForFirstTime, enumValues.suitability, "unknown", "Prima adozione", errors),
    needsGarden: choice(behaviorInput.needsGarden, enumValues.garden, "unknown", "Giardino", errors),
    notesIt: optionalText(behaviorInput.notesIt, 10000, "Note comportamento", errors),
    notesEn: optionalText(behaviorInput.notesEn, 10000, "Behaviour notes", errors),
  };

  const nameInput = optionalText(input.name, 80, "Nome", errors);
  const internalCode = optionalText(input.internalCode, 40, "Codice interno", errors);
  const name = nameInput || (internalCode ? `Codice ${internalCode}`.slice(0, 80) : "");
  const data: Omit<Prisma.AnimalUncheckedCreateInput, "id" | "slug" | "shelterId"> = {
    name,
    internalCode,
    species: species as AnimalSpecies,
    sex: sex as AnimalSex,
    size: input.size ? size as AnimalSize : null,
    breedPrimary: optionalText(input.breedPrimary, 80, "Razza", errors),
    coatColor: optionalText(input.coatColor, 60, "Colore mantello", errors),
    birthDate: estimatedBirthDate,
    birthDateEstimated: input.birthDateEstimated === true || input.birthDateEstimated === "on",
    weightKg,
    microchipNumber,
    isSterilized: sterilized === "unknown" ? null : sterilized === "yes",
    sterilizationAssessed: ["yes", "no", "unknown"].includes(String(input.isSterilized)),
    hasSpecialNeeds: input.hasSpecialNeeds === true || input.hasSpecialNeeds === "true",
    specialNeedsSummary: optionalText(input.specialNeedsSummary, 255, "Bisogni speciali", errors),
    isVaccinatedSummary: vaccinated === "unknown" ? null : vaccinated === "yes",
    headlineIt: optionalText(input.headlineIt, 140, "Titolo italiano", errors),
    headlineEn: optionalText(input.headlineEn, 140, "Titolo inglese", errors),
    storyIt: optionalText(input.storyIt, 20000, "Descrizione italiana", errors),
    storyEn: optionalText(input.storyEn, 20000, "Descrizione inglese", errors),
    adoptionFeeCents: fee === null ? null : Math.round(fee * 100),
    intakeDate,
    status: "draft",
  };
  return { errors, data, behavior };
}

export function animalSlug(name: string) {
  const base = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 120) || "animale";
  return `${base}-${crypto.randomUUID().slice(0, 8)}`;
}
