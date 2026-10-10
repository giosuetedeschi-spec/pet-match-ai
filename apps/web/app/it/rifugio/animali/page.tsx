import { AnimalStatus } from "@prisma/client";
import { getCurrentUserSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

const statusLabel: Record<AnimalStatus, string> = {
  draft: "Bozza",
  available: "Disponibile",
  reserved: "Riservato",
  adopted: "Adottato",
  unavailable: "Non disponibile",
  transferred: "Trasferito",
  deceased: "Deceduto",
};

export default async function ShelterAnimalsPage() {
  const session = await getCurrentUserSession();
  if (!session) return null;
  const shelters = await prisma.shelterMember.findMany({
    where: { userId: session.user.id, shelter: { deletedAt: null } },
    select: { shelterId: true, shelter: { select: { name: true, status: true } } },
  });
  const animals = await prisma.animal.findMany({
    where: { shelterId: { in: shelters.map((item) => item.shelterId) }, deletedAt: null },
    orderBy: [{ updatedAt: "desc" }, { name: "asc" }],
    select: {
      id: true, name: true, slug: true, species: true, status: true, updatedAt: true,
      shelter: { select: { name: true } },
      media: { where: { isPrimary: true, deletedAt: null }, take: 1, select: { id: true } },
    },
  });

  return <main className="catalog-page shelter-page">
    <a className="catalog-home" href="/">PetMatch AI</a>
    <header className="catalog-heading">
      <p className="eyebrow">Area rifugi</p>
      <h1>I tuoi animali</h1>
      <p className="intro">Crea le schede e pubblicale quando tutti i requisiti sono completi.</p>
      <a className="button" href="/it/rifugio/animali/nuovo">Aggiungi un animale</a>
      <a className="button secondary" href="/it/rifugio/triage">Apri triage ML</a>
    </header>
    {animals.length ? <section className="animal-grid" aria-label="Schede animali">
      {animals.map((animal) => <article className="animal-card" key={animal.id}>
        <div className="animal-mark" aria-hidden="true">{animal.species === "dog" ? "🐕" : "🐈"}</div>
        <div className="animal-card-body">
          <p className="animal-meta">{animal.shelter.name} · {statusLabel[animal.status]}</p>
          <h2>{animal.status === "draft" || animal.status === "available" ? <a href={`/it/rifugio/animali/${animal.id}`}>{animal.name}</a> : animal.name}</h2>
          {animal.status === "available" && <a className="match-catalog-link" href={`/it/animali/${animal.slug}`}>Apri la scheda pubblica</a>}
          <p className="animal-meta">Aggiornato il {animal.updatedAt.toLocaleDateString("it-IT", { timeZone: "Europe/Rome" })}</p>
        </div>
      </article>)}
    </section> : <section className="catalog-empty"><h2>Ancora nessuna scheda</h2><p>Inizia con una bozza: potrai completarla e pubblicarla in seguito.</p></section>}
  </main>;
}
