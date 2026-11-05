import { notFound } from "next/navigation";
import { getCurrentUserSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import AnimalForm from "../AnimalForm";

export const dynamic = "force-dynamic";

export default async function EditDraftPage({ params }: { params: Promise<{ id: string }> }) {
  const session = await getCurrentUserSession();
  if (!session) return null;
  const { id } = await params;
  const memberships = await prisma.shelterMember.findMany({
    where: { userId: session.user.id, shelter: { deletedAt: null } },
    select: { shelterId: true, shelter: { select: { name: true, status: true } } },
  });
  const animal = await prisma.animal.findFirst({
    where: { id, status: { in: ["draft", "available"] }, deletedAt: null, shelterId: { in: memberships.map(({ shelterId }) => shelterId) } },
    include: { behaviorProfile: true, media: { where: { kind: "photo", deletedAt: null, processingStatus: "ready" }, orderBy: { sortOrder: "asc" } } },
  });
  if (!animal) notFound();
  const fields: Record<string, string> = {
    name: animal.name,
    internalCode: animal.internalCode ?? "",
    species: animal.species,
    sex: animal.sex,
    ageMonths: animal.birthDate ? String(Math.max(0, (new Date().getFullYear() - animal.birthDate.getFullYear()) * 12 + new Date().getMonth() - animal.birthDate.getMonth())) : "",
    birthDate: animal.birthDate?.toISOString().slice(0, 10) ?? "",
    birthDateEstimated: String(animal.birthDateEstimated),
    intakeDate: animal.intakeDate.toISOString().slice(0, 10),
    size: animal.size ?? "",
    breedPrimary: animal.breedPrimary ?? "",
    coatColor: animal.coatColor ?? "",
    weightKg: animal.weightKg?.toString() ?? "",
    microchipNumber: animal.microchipNumber ?? "",
    headlineIt: animal.headlineIt ?? "",
    headlineEn: animal.headlineEn ?? "",
    storyIt: animal.storyIt ?? "",
    storyEn: animal.storyEn ?? "",
    isSterilized: !animal.sterilizationAssessed ? "" : animal.isSterilized === null ? "unknown" : animal.isSterilized ? "yes" : "no",
    isVaccinatedSummary: animal.isVaccinatedSummary === null ? "unknown" : animal.isVaccinatedSummary ? "yes" : "no",
    hasSpecialNeeds: String(animal.hasSpecialNeeds),
    specialNeedsSummary: animal.specialNeedsSummary ?? "",
    adoptionFeeEur: animal.adoptionFeeCents === null ? "" : (animal.adoptionFeeCents / 100).toFixed(2),
  };
  const profile = animal.behaviorProfile;
  const behavior: Record<string, string> = profile ? {
    energyLevel: profile.energyLevel?.toString() ?? "",
    sociabilityPeople: profile.sociabilityPeople?.toString() ?? "",
    goodWithChildren: profile.goodWithChildren,
    goodWithDogs: profile.goodWithDogs,
    goodWithCats: profile.goodWithCats,
    houseTrained: profile.houseTrained,
    leashTrained: profile.leashTrained,
    noiseTolerance: profile.noiseTolerance?.toString() ?? "",
    aloneToleranceHours: profile.aloneToleranceHours?.toString() ?? "",
    trainingNeeds: profile.trainingNeeds?.toString() ?? "",
    groomingNeeds: profile.groomingNeeds?.toString() ?? "",
    exerciseMinPerDay: profile.exerciseMinPerDay?.toString() ?? "",
    suitableForFirstTime: profile.suitableForFirstTime,
    needsGarden: profile.needsGarden,
    notesIt: profile.notesIt ?? "",
    notesEn: profile.notesEn ?? "",
  } : {};
  return <AnimalForm
    shelters={memberships.map(({ shelterId, shelter }) => ({ id: shelterId, name: shelter.name, status: shelter.status }))}
    published={animal.status === "available"}
    initial={{
      id: animal.id,
      shelterId: animal.shelterId,
      fields,
      behavior,
      photos: animal.media.map(({ id, altTextIt, altTextEn, isPrimary, sortOrder }) => ({ id, altTextIt, altTextEn, isPrimary, sortOrder })),
    }}
  />;
}
