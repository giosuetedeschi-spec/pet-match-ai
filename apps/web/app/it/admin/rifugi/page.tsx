import { redirect } from "next/navigation";
import { getCurrentUserSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import ShelterReviewActions from "./review-actions";

export const dynamic = "force-dynamic";
export default async function ShelterReviewPage() {
  const session = await getCurrentUserSession();
  if (!session || session.user.role !== "platform_admin") redirect("/");
  const shelters = await prisma.shelter.findMany({ where: { status: "pending", deletedAt: null }, orderBy: { createdAt: "asc" }, select: { id: true, name: true, legalName: true, type: true, taxId: true, email: true, phone: true, addressLine: true, postalCode: true, createdAt: true, comune: { select: { name: true, provinceCode: true } }, members: { take: 1, select: { user: { select: { fullName: true, email: true, emailVerifiedAt: true } } } } } });
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><header className="catalog-heading"><p className="eyebrow">Amministrazione</p><h1>Richieste rifugi</h1><p className="intro">Verifica identità, contatti e email prima di attivare una struttura.</p></header>{shelters.length ? shelters.map((shelter) => <article className="catalog-empty" key={shelter.id}><h2>{shelter.name}</h2><p>{shelter.legalName} · {shelter.type} · {shelter.taxId}</p><p>{shelter.addressLine}, {shelter.postalCode} {shelter.comune.name} ({shelter.comune.provinceCode})</p><p>{shelter.email} · {shelter.phone}</p><p>Referente: {shelter.members[0]?.user.fullName} — {shelter.members[0]?.user.email} · email {shelter.members[0]?.user.emailVerifiedAt ? "verificata" : "non verificata"}</p><p>Richiesta del {shelter.createdAt.toLocaleDateString("it-IT")}</p><ShelterReviewActions shelterId={shelter.id} emailVerified={Boolean(shelter.members[0]?.user.emailVerifiedAt)} /></article>) : <section className="catalog-empty"><h2>Nessuna richiesta in attesa</h2></section>}</main>;
}
