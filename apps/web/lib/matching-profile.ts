import type { Prisma } from "@prisma/client";
import type { MatchProfile } from "./matching";

export type ProfileWithComune = Prisma.AdopterProfileGetPayload<{
  include: { searchComune: { select: { latitude: true; longitude: true } } };
}>;

export function toMatchProfile(profile: ProfileWithComune, radius = profile.searchRadiusKm): MatchProfile {
  if (!profile.searchComune || profile.searchComuneId === null) throw new Error("Il profilo non ha un comune di ricerca.");
  return {
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
}
