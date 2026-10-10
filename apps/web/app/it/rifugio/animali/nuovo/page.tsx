import { getCurrentUserSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import AnimalForm from "../AnimalForm";

export const dynamic = "force-dynamic";

export default async function NewAnimalPage() {
  const session = await getCurrentUserSession();
  if (!session) return null;
  const shelters = await prisma.shelterMember.findMany({
    where: { userId: session.user.id, shelter: { deletedAt: null } },
    select: { shelterId: true, shelter: { select: { name: true, status: true } } },
    orderBy: { joinedAt: "asc" },
  });
  return <AnimalForm shelters={shelters.map(({ shelterId, shelter }) => ({ id: shelterId, name: shelter.name, status: shelter.status }))} />;
}
