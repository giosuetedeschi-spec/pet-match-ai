import { AnimalStatus, ShelterStatus } from "@prisma/client";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { getUserSession, sessionCookieName } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import AnimalFavoriteButton from "./AnimalFavoriteButton";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const animal = await prisma.animal.findFirst({
    where: { slug, status: AnimalStatus.available, publishedAt: { not: null }, deletedAt: null, shelter: { status: ShelterStatus.active, deletedAt: null } },
    select: { name: true, headlineIt: true },
  });
  return animal ? { title: `${animal.name} cerca casa — PetMatch AI`, description: animal.headlineIt ?? `Scopri il profilo di ${animal.name}.` } : { title: "Animale non disponibile — PetMatch AI" };
}

export default async function AnimalPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const animal = await prisma.animal.findFirst({
    where: { slug, status: AnimalStatus.available, publishedAt: { not: null }, deletedAt: null, shelter: { status: ShelterStatus.active, deletedAt: null } },
    select: {
      id: true, name: true, species: true, sex: true, size: true, birthDate: true, breedPrimary: true,
      headlineIt: true, storyIt: true, hasSpecialNeeds: true,
      shelter: { select: { name: true, email: true, phone: true, comune: { select: { name: true, provinceCode: true } } } },
      behaviorProfile: { select: { energyLevel: true, goodWithChildren: true, goodWithDogs: true, goodWithCats: true, houseTrained: true, aloneToleranceHours: true, trainingNeeds: true, groomingNeeds: true, needsGarden: true } },
      media: { where: { kind: "photo", processingStatus: "ready", deletedAt: null }, orderBy: [{ sortOrder: "asc" }, { createdAt: "asc" }], select: { id: true, altTextIt: true, altTextEn: true } },
    },
  });
  if (!animal) notFound();

  const cookieStore = await cookies();
  const session = await getUserSession(cookieStore.get(sessionCookieName)?.value);
  const anonymousToken = cookieStore.get("petmatch-adopter")?.value;
  const profile = session
    ? await prisma.adopterProfile.findUnique({ where: { userId: session.user.id }, select: { id: true } })
    : anonymousToken ? await prisma.adopterProfile.findUnique({ where: { anonymousToken }, select: { id: true } }) : null;
  const [match, favorite] = profile ? await Promise.all([
    prisma.matchResult.findUnique({ where: { profileId_animalId: { profileId: profile.id, animalId: animal.id } }, select: { score: true, reasons: true, considerations: true, explanationIt: true, breakdown: true } }),
    prisma.favorite.findUnique({ where: { profileId_animalId: { profileId: profile.id, animalId: animal.id } }, select: { id: true } }),
  ]) : [null, null];
  const ageMonths = animal.birthDate ? Math.max(0, (new Date().getFullYear() - animal.birthDate.getFullYear()) * 12 + new Date().getMonth() - animal.birthDate.getMonth()) : null;
  const dimensions = match?.breakdown && typeof match.breakdown === "object" && "dimensions" in match.breakdown && Array.isArray(match.breakdown.dimensions)
    ? match.breakdown.dimensions as { name: string; score: number; weight: number }[]
    : [];
  const reasons = Array.isArray(match?.reasons) ? match.reasons as string[] : [];
  const considerations = Array.isArray(match?.considerations) ? match.considerations as string[] : [];

  return <main className="catalog-page"><a className="catalog-home" href="/it/animali">← Tutti gli animali</a><header className="catalog-heading"><p className="eyebrow">{animal.shelter.name} · {animal.shelter.comune.name} ({animal.shelter.comune.provinceCode})</p><h1>{animal.name}</h1><p className="intro">{animal.headlineIt ?? animal.breedPrimary ?? (animal.species === "dog" ? "Cane" : "Gatto")}</p></header>
    <section className="animal-profile-layout"><article className="animal-profile-card"><p>{animal.species === "dog" ? "Cane" : "Gatto"} · {animal.sex === "male" ? "Maschio" : animal.sex === "female" ? "Femmina" : "Sesso non indicato"}{animal.size ? ` · ${animal.size}` : ""}{ageMonths !== null ? ` · ${Math.floor(ageMonths / 12)} anni` : ""}</p>{animal.breedPrimary && <p>Razza indicativa: {animal.breedPrimary}</p>}{animal.storyIt && <p className="animal-story-full">{animal.storyIt}</p>}{animal.hasSpecialNeeds && <p>Il rifugio segnala esigenze speciali: chiedi quali cure siano necessarie.</p>}<div className="actions"><AnimalFavoriteButton animalId={animal.id} initialFavorite={Boolean(favorite)} /><a className="button" href={`mailto:${animal.shelter.email}?subject=${encodeURIComponent(`Informazioni su ${animal.name}`)}`}>Contatta il rifugio</a></div><p className="match-disclaimer">La disponibilità va confermata direttamente con il rifugio.</p></article>
      <aside className="match-card"><h2>Compatibilità con il tuo profilo</h2>{match ? <><p className="match-score"><strong>{match.score}%</strong> di compatibilità</p>{match.explanationIt && <p>{match.explanationIt}</p>}{reasons.length > 0 && <ul className="match-reasons">{reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>}{considerations.length > 0 && <details><summary>Aspetti da approfondire</summary><ul>{considerations.map((item) => <li key={item}>{item}</li>)}</ul></details>}{dimensions.length > 0 && <details><summary>Dettaglio del punteggio</summary><ul>{dimensions.map((item) => <li key={item.name}>{item.name}: {item.score}/100 ({Math.round(item.weight * 100)}%)</li>)}</ul></details>}</> : <><p>Completa il questionario per vedere la compatibilità con il tuo stile di vita.</p><a className="button" href="/it/abbinamento">Crea il tuo profilo</a></>}</aside></section>
    {animal.media.length > 0 && <section className="animal-photo-gallery" aria-label={`Foto di ${animal.name}`}>{animal.media.map((photo) => <img key={photo.id} src={`/api/media/${photo.id}?width=1280`} alt={photo.altTextIt || photo.altTextEn || `Foto di ${animal.name}`} />)}</section>}
  </main>;
}
