import { randomBytes } from "node:crypto";
import { adopterCookieName, getRequestSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const adopterProfileSelect = {
  id: true,
  userId: true,
  housingType: true,
  housingSizeSqm: true,
  hasOutdoorSpace: true,
  outdoorSpaceSqm: true,
  householdAdults: true,
  childrenAges: true,
  existingDogs: true,
  existingCats: true,
  hoursAlonePerDay: true,
  activityLevel: true,
  experienceLevel: true,
  groomingCapacity: true,
  trainingCapacity: true,
  monthlyBudgetEur: true,
  preferredSpecies: true,
  preferredSizes: true,
  preferredAgeBands: true,
  preferredSex: true,
  dealbreakers: true,
  searchComuneId: true,
  searchComune: { select: { id: true, name: true, provinceCode: true, region: true } },
  searchRadiusKm: true,
  currentStep: true,
  completedAt: true,
  notifyNewMatches: true,
  minNotifyScore: true,
} as const;

export type AdopterProfileRecord = Awaited<ReturnType<typeof findAdopterProfile>>;

export async function findAdopterProfile(request: Request) {
  const session = await getRequestSession(request);
  if (session) {
    return prisma.adopterProfile.findUnique({ where: { userId: session.user.id }, select: adopterProfileSelect });
  }
  const cookieHeader = request.headers.get("cookie") ?? "";
  const token = cookieHeader.match(/(?:^|;\s*)petmatch-adopter=([^;]+)/)?.[1];
  if (!token) return null;
  return prisma.adopterProfile.findUnique({ where: { anonymousToken: decodeURIComponent(token) }, select: adopterProfileSelect });
}

export async function getOrCreateAdopterProfile(request: Request) {
  const session = await getRequestSession(request);
  if (session) {
    const profile = await prisma.adopterProfile.upsert({
      where: { userId: session.user.id },
      create: { id: randomBytes(13).toString("hex"), userId: session.user.id },
      update: {},
      select: adopterProfileSelect,
    });
    return { profile, anonymousToken: null as string | null };
  }

  const cookieHeader = request.headers.get("cookie") ?? "";
  const existingToken = cookieHeader.match(/(?:^|;\s*)petmatch-adopter=([^;]+)/)?.[1];
  const anonymousToken = existingToken ? decodeURIComponent(existingToken) : randomBytes(16).toString("hex");
  const profile = await prisma.adopterProfile.upsert({
    where: { anonymousToken },
    create: { id: randomBytes(13).toString("hex"), anonymousToken },
    update: {},
    select: adopterProfileSelect,
  });
  return { profile, anonymousToken };
}

export { adopterCookieName };
