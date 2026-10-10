type Behaviour = {
  energyLevel: number | null;
  sociabilityPeople: number | null;
  goodWithChildren: string;
  goodWithDogs: string;
  goodWithCats: string;
  houseTrained: string;
  leashTrained: string;
  noiseTolerance: number | null;
  aloneToleranceHours: number | null;
  trainingNeeds: number | null;
  groomingNeeds: number | null;
  exerciseMinPerDay: number | null;
  suitableForFirstTime: string;
  needsGarden: string;
  assessedAt: Date | null;
};

type Media = { altTextIt: string | null; altTextEn: string | null; processingStatus: string; deletedAt: Date | null };

export function animalPublishBlockers(animal: {
  name: string;
  size: string | null;
  isSterilized: boolean | null;
  sterilizationAssessed: boolean;
  storyIt: string | null;
  storyEn: string | null;
  birthDate: Date | null;
  intakeDate: Date;
  behaviorProfile: Behaviour | null;
  media: Media[];
}) {
  const blockers: string[] = [];
  if (!animal.name.trim()) blockers.push("Nome o codice temporaneo");
  if (!animal.birthDate) blockers.push("Età o data di nascita stimata");
  if (!animal.size) blockers.push("Taglia");
  if (!animal.sterilizationAssessed) blockers.push("Stato di sterilizzazione (anche “non noto” va indicato)");
  if (!animal.storyIt?.trim() && !animal.storyEn?.trim()) blockers.push("Descrizione in italiano o inglese");
  if (!animal.media.some((photo) => !photo.deletedAt && photo.processingStatus === "ready" && Boolean(photo.altTextIt?.trim() || photo.altTextEn?.trim()))) {
    blockers.push("Almeno una foto pronta con testo alternativo");
  }
  const behaviour = animal.behaviorProfile;
  if (!behaviour || !behaviour.assessedAt) {
    blockers.push("Profilo comportamentale valutato");
  } else if ([behaviour.energyLevel, behaviour.sociabilityPeople, behaviour.noiseTolerance, behaviour.aloneToleranceHours, behaviour.trainingNeeds, behaviour.groomingNeeds, behaviour.exerciseMinPerDay].some((value) => value === null)) {
    blockers.push("Completa tutti i valori del profilo comportamentale; per le compatibilità puoi selezionare “non noto”");
  }
  if (animal.birthDate && animal.birthDate > animal.intakeDate) blockers.push("La data di nascita deve precedere l'ingresso al rifugio");
  if (animal.intakeDate > new Date()) blockers.push("La data di ingresso non può essere futura");
  return blockers;
}

export function validateAnimalDraft(input: Record<string, unknown>) {
  const errors: string[] = [];
  if (input.species !== "dog" && input.species !== "cat") errors.push("Seleziona cane o gatto.");
  const name = typeof input.name === "string" ? input.name.trim() : "";
  const internalCode = typeof input.internalCode === "string" ? input.internalCode.trim() : "";
  if (!name && !internalCode) errors.push("Inserisci il nome o il codice temporaneo.");
  if (name.length > 80 || internalCode.length > 40) errors.push("Nome o codice superano la lunghezza consentita.");
  const ageMonths = input.ageMonths === "" || input.ageMonths === null || input.ageMonths === undefined ? null : Number(input.ageMonths);
  const birthDate = typeof input.birthDate === "string" ? input.birthDate.trim() : "";
  if (birthDate && !isDate(birthDate)) errors.push("Inserisci una data di nascita valida.");
  if (!birthDate && (ageMonths === null || !Number.isInteger(ageMonths) || ageMonths < 0 || ageMonths > 360)) {
    errors.push("Inserisci una data di nascita stimata o un'età tra 0 e 360 mesi.");
  }
  if (input.sex !== undefined && !["male", "female", "unknown"].includes(String(input.sex))) errors.push("Il sesso selezionato non è valido.");
  if (typeof input.intakeDate !== "string" || !isDate(input.intakeDate)) errors.push("Inserisci una data di ingresso valida.");
  if (input.microchipNumber && (typeof input.microchipNumber !== "string" || !/^\d{15}$/.test(input.microchipNumber))) {
    errors.push("Il microchip deve contenere 15 cifre.");
  }
  return { errors, ageMonths, birthDate };
}

export function isDate(value: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}
