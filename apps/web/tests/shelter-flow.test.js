import { describe, expect, test } from "bun:test";
import sharp from "sharp";
import { animalPublishBlockers, isDate, validateAnimalDraft } from "../lib/animal-validation.ts";
import { parseAnimalInput } from "../lib/animal-input.ts";
import { processAnimalPhoto } from "../lib/animal-media.ts";

const validInput = {
  species: "dog",
  name: "Luna",
  sex: "female",
  size: "medium",
  ageMonths: "24",
  intakeDate: "2026-02-01",
  isSterilized: "unknown",
  behavior: {
    energyLevel: "3",
    sociabilityPeople: "4",
    goodWithChildren: "unknown",
    goodWithDogs: "unknown",
    goodWithCats: "unknown",
    houseTrained: "unknown",
    leashTrained: "unknown",
    noiseTolerance: "3",
    aloneToleranceHours: "2",
    trainingNeeds: "2",
    groomingNeeds: "2",
    exerciseMinPerDay: "60",
    suitableForFirstTime: "unknown",
    needsGarden: "unknown",
  },
};

const completeAnimal = {
  name: "Luna",
  size: "medium",
  isSterilized: null,
  sterilizationAssessed: true,
  storyIt: "Descrizione",
  storyEn: null,
  birthDate: new Date("2024-02-01T00:00:00.000Z"),
  intakeDate: new Date("2026-02-01T00:00:00.000Z"),
  behaviorProfile: {
    energyLevel: 3,
    sociabilityPeople: 4,
    goodWithChildren: "unknown",
    goodWithDogs: "unknown",
    goodWithCats: "unknown",
    houseTrained: "unknown",
    leashTrained: "unknown",
    noiseTolerance: 3,
    aloneToleranceHours: 2,
    trainingNeeds: 2,
    groomingNeeds: 2,
    exerciseMinPerDay: 60,
    suitableForFirstTime: "unknown",
    needsGarden: "unknown",
    assessedAt: new Date(),
  },
  media: [{ altTextIt: "Luna al parco", altTextEn: null, processingStatus: "ready", deletedAt: null }],
};

describe("shelter animal authoring validation", () => {
  test("accepts a valid draft and keeps unknown sterilization explicit", () => {
    const parsed = parseAnimalInput(validInput);
    expect(parsed.errors).toEqual([]);
    expect(parsed.data.sterilizationAssessed).toBe(true);
    expect(parsed.data.isSterilized).toBeNull();
  });

  test("rejects invalid dates, microchip numbers, and out of range values", () => {
    expect(isDate("2026-02-30")).toBe(false);
    const parsed = validateAnimalDraft({ ...validInput, birthDate: "2026-02-30", microchipNumber: "123" });
    expect(parsed.errors).toContain("Inserisci una data di nascita valida.");
    expect(parsed.errors).toContain("Il microchip deve contenere 15 cifre.");
    expect(parseAnimalInput({ ...validInput, behavior: { ...validInput.behavior, energyLevel: "9" } }).errors.length).toBeGreaterThan(0);
  });

  test("blocks publication until the profile, sterilization assessment, and accessible photo are ready", () => {
    expect(animalPublishBlockers(completeAnimal)).toEqual([]);
    expect(animalPublishBlockers({
      ...completeAnimal,
      sterilizationAssessed: false,
      behaviorProfile: { ...completeAnimal.behaviorProfile, assessedAt: null },
      media: [{ ...completeAnimal.media[0], altTextIt: null }],
    }).length).toBeGreaterThanOrEqual(3);
  });
});

describe("photo validation and processing", () => {
  test("accepts a raster image, normalizes it to WebP, and creates every size", async () => {
    const input = await sharp({ create: { width: 64, height: 32, channels: 3, background: "#aabbcc" } }).png().toBuffer();
    const processed = await processAnimalPhoto(input);
    expect(processed.width).toBe(64);
    expect(processed.height).toBe(32);
    expect([...processed.variants.keys()]).toEqual(["original.webp", "320.webp", "640.webp", "1280.webp", "1920.webp"]);
    expect((await sharp(processed.variants.get("original.webp")).metadata()).format).toBe("webp");
  });

  test("applies EXIF orientation and strips the source metadata", async () => {
    const tagged = await sharp({ create: { width: 64, height: 32, channels: 3, background: "#aabbcc" } })
      .jpeg()
      .withMetadata({ orientation: 6 })
      .toBuffer();
    const processed = await processAnimalPhoto(tagged);
    const metadata = await sharp(processed.variants.get("original.webp")).metadata();
    expect(metadata.width).toBe(32);
    expect(metadata.height).toBe(64);
    expect(metadata.exif).toBeUndefined();
    expect(metadata.orientation).toBeUndefined();
  });

  test("rejects data that is not a supported image", async () => {
    await expect(processAnimalPhoto(Buffer.from("not an image"))).rejects.toThrow();
  });
});
