import { redirect } from "next/navigation";
import { getCurrentUserSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export default async function ShelterLayout({ children }: { children: React.ReactNode }) {
  const session = await getCurrentUserSession();
  if (!session) redirect("/it/account/accedi?next=%2Fit%2Frifugio%2Fanimali");
  if (session.user.role !== "shelter_staff") redirect("/it/account/accedi");
  const membership = await prisma.shelterMember.findFirst({
    where: { userId: session.user.id, shelter: { deletedAt: null } },
    select: { id: true },
  });
  if (!membership) redirect("/it/account/accedi");
  return <>{children}</>;
}
