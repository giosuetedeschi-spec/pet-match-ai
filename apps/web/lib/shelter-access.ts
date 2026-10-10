import { getRequestSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function getShelterAccess(request: Request) {
  const session = await getRequestSession(request);
  if (!session) return { response: Response.json({ error: "Accedi per continuare." }, { status: 401 }) };
  if (session.user.role !== "shelter_staff") {
    return { response: Response.json({ error: "Questa sezione è riservata ai membri dei rifugi." }, { status: 403 }) };
  }

  const memberships = await prisma.shelterMember.findMany({
    where: { userId: session.user.id, shelter: { deletedAt: null } },
    select: {
      shelterId: true,
      shelter: { select: { name: true, status: true } },
    },
  });
  if (!memberships.length) {
    return { response: Response.json({ error: "Il tuo account non è associato a un rifugio." }, { status: 403 }) };
  }
  return { userId: session.user.id, memberships };
}

export function memberShelter(access: Awaited<ReturnType<typeof getShelterAccess>>, shelterId: string) {
  if ("response" in access) return null;
  return access.memberships.find((membership) => membership.shelterId === shelterId) ?? null;
}
