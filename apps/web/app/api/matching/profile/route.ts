import { AnimalSize, HousingType, PreferredSex, PreferredSpecies, Prisma } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { adopterCookieName, adopterProfileSelect, findAdopterProfile, getOrCreateAdopterProfile } from "@/lib/adopter-profile";
import { getRequestSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

const experienceLevels = ["first_time", "some", "experienced"];
const ageBands = ["puppy", "young", "adult", "senior"];
const dealbreakers = [
  "must_be_house_trained",
  "no_special_needs",
  "no_dogs_over_25kg",
  "must_be_good_with_children",
  "must_be_good_with_cats",
  "must_be_good_with_dogs",
  "no_puppies",
  "must_be_sterilized",
];

function attachTokenCookie(response: NextResponse, token: string | null) {
  if (token) response.cookies.set(adopterCookieName, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 180,
  });
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

function record(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function integer(value: unknown, min: number, max: number) {
  return typeof value === "number" && Number.isInteger(value) && value >= min && value <= max;
}

function enumValue<T extends Record<string, string>>(value: unknown, values: T) {
  return typeof value === "string" && Object.values(values).includes(value) ? value : null;
}

function stringArray(value: unknown, allowed: string[], max: number) {
  return Array.isArray(value) && value.length <= max && value.every((item) =>
    typeof item === "string" && allowed.includes(item),
  );
}

export async function GET(request: NextRequest) {
  try {
    const { profile, anonymousToken } = await getOrCreateAdopterProfile(request);
    return attachTokenCookie(NextResponse.json(profile), anonymousToken);
  } catch {
    return NextResponse.json({ error: "Profilo non disponibile." }, { status: 503 });
  }
}

export async function PUT(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Formato della richiesta non valido." }, { status: 400 });
  }
  if (!record(body) || !record(body.profile) || !integer(body.currentStep, 0, 14)) {
    return NextResponse.json({ error: "Risposte non valide." }, { status: 400 });
  }

  const input = body.profile;
  const invalid =
    !enumValue(input.housingType, HousingType) ||
    !integer(input.housingSizeSqm, 20, 1000) ||
    typeof input.hasOutdoorSpace !== "boolean" ||
    !integer(input.outdoorSpaceSqm, 0, 10000) ||
    !integer(input.householdAdults, 1, 20) ||
    !Array.isArray(input.childrenAges) || input.childrenAges.length > 20 || !input.childrenAges.every((age) => integer(age, 0, 17)) ||
    !integer(input.existingDogs, 0, 20) ||
    !integer(input.existingCats, 0, 20) ||
    !integer(input.hoursAlonePerDay, 0, 16) ||
    !integer(input.activityLevel, 1, 5) ||
    typeof input.experienceLevel !== "string" || !experienceLevels.includes(input.experienceLevel) ||
    !integer(input.groomingCapacity, 1, 5) ||
    !integer(input.trainingCapacity, 1, 5) ||
    (input.monthlyBudgetEur !== null && !integer(input.monthlyBudgetEur, 0, 100000)) ||
    !enumValue(input.preferredSpecies, PreferredSpecies) ||
    !stringArray(input.preferredSizes, Object.values(AnimalSize), 4) ||
    !stringArray(input.preferredAgeBands, ageBands, 4) ||
    !enumValue(input.preferredSex, PreferredSex) ||
    !stringArray(input.dealbreakers, dealbreakers, dealbreakers.length) ||
    (input.searchComuneId !== null && !integer(input.searchComuneId, 1, 65535)) ||
    !integer(input.searchRadiusKm, 10, 200);

  if (invalid) return NextResponse.json({ error: "Controlla le risposte del questionario." }, { status: 400 });

  if (input.searchComuneId != null) {
    const comune = await prisma.comune.findUnique({ where: { id: input.searchComuneId as number }, select: { id: true } });
    if (!comune) return NextResponse.json({ error: "Seleziona un comune valido." }, { status: 400 });
  }

  const currentStep = body.currentStep as number;
  const completedAt = currentStep === 14 ? new Date() : null;
  const profileData = {
    housingType: input.housingType as HousingType,
    housingSizeSqm: input.housingSizeSqm as number,
    hasOutdoorSpace: input.hasOutdoorSpace as boolean,
    outdoorSpaceSqm: input.outdoorSpaceSqm as number,
    householdAdults: input.householdAdults as number,
    childrenAges: input.childrenAges as Prisma.InputJsonValue,
    existingDogs: input.existingDogs as number,
    existingCats: input.existingCats as number,
    hoursAlonePerDay: input.hoursAlonePerDay as number,
    activityLevel: input.activityLevel as number,
    experienceLevel: input.experienceLevel as string,
    groomingCapacity: input.groomingCapacity as number,
    trainingCapacity: input.trainingCapacity as number,
    monthlyBudgetEur: input.monthlyBudgetEur as number | null,
    preferredSpecies: input.preferredSpecies as PreferredSpecies,
    preferredSizes: input.preferredSizes as Prisma.InputJsonValue,
    preferredAgeBands: input.preferredAgeBands as Prisma.InputJsonValue,
    preferredSex: input.preferredSex as PreferredSex,
    dealbreakers: input.dealbreakers as Prisma.InputJsonValue,
    searchComuneId: input.searchComuneId as number | null,
    searchRadiusKm: input.searchRadiusKm as number,
    currentStep,
    completedAt,
  };

  try {
    const { profile, anonymousToken } = await getOrCreateAdopterProfile(request);
    const saved = await prisma.adopterProfile.update({
      where: { id: profile.id },
      data: profileData,
      select: adopterProfileSelect,
    });
    await prisma.matchResult.updateMany({ where: { profileId: saved.id }, data: { engineVersion: "invalidated" } });
    return attachTokenCookie(NextResponse.json(saved), anonymousToken);
  } catch {
    return NextResponse.json({ error: "Non riesco a salvare le risposte in questo momento." }, { status: 503 });
  }
}

export async function DELETE(request: NextRequest) {
  const profile = await findAdopterProfile(request);
  if (profile) await prisma.adopterProfile.delete({ where: { id: profile.id } });
  const response = NextResponse.json({ status: "deleted" });
  const session = await getRequestSession(request);
  if (!session) response.cookies.set(adopterCookieName, "", { path: "/", maxAge: 0 });
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}
