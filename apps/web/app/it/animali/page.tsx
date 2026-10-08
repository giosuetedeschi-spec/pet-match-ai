import {
  AnimalSize,
  AnimalSpecies,
  AnimalStatus,
  Prisma,
  ShelterStatus,
} from "@prisma/client";
import { cookies } from "next/headers";
import { getUserSession, sessionCookieName } from "@/lib/auth";
import { MATCH_ENGINE_VERSION } from "@/lib/matching";
import { prisma } from "@/lib/prisma";

const pageSize = 24;
const speciesOptions = [AnimalSpecies.dog, AnimalSpecies.cat];
const sizeOptions = [
  AnimalSize.small,
  AnimalSize.medium,
  AnimalSize.large,
  AnimalSize.xlarge,
];

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function label(value: string) {
  if (value === "dog") return "Cane";
  if (value === "cat") return "Gatto";
  return value;
}

function sexLabel(value: string) {
  if (value === "male") return "Maschio";
  if (value === "female") return "Femmina";
  return "Sesso non indicato";
}

function sizeLabel(value: string) {
  const labels: Record<string, string> = {
    small: "Piccola",
    medium: "Media",
    large: "Grande",
    xlarge: "Molto grande",
  };
  return labels[value] ?? value;
}

export const dynamic = "force-dynamic";

export default async function CatalogPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const speciesValue = first(params.species);
  const sizeValue = first(params.size);
  const species = speciesOptions.find((value) => value === speciesValue);
  const size = sizeOptions.find((value) => value === sizeValue);
  const query = (first(params.q) ?? "").trim().slice(0, 80);
  const sortByMatch = first(params.sort) === "match";
  const rawPage = Number.parseInt(first(params.page) ?? "1", 10);
  const page = Number.isFinite(rawPage) ? Math.max(1, Math.min(rawPage, 1000)) : 1;

  const where: Prisma.AnimalWhereInput = {
    status: AnimalStatus.available,
    publishedAt: { not: null },
    deletedAt: null,
    shelter: { status: ShelterStatus.active, deletedAt: null },
    ...(species ? { species } : {}),
    ...(size ? { size } : {}),
    ...(query
      ? {
          OR: [
            { name: { contains: query } },
            { breedPrimary: { contains: query } },
            { headlineIt: { contains: query } },
            { storyIt: { contains: query } },
          ],
        }
      : {}),
  };

  const cookieStore = sortByMatch ? await cookies() : null;
  const token = cookieStore?.get("petmatch-adopter")?.value;
  const session = sortByMatch ? await getUserSession(cookieStore?.get(sessionCookieName)?.value) : null;
  const profile = session
    ? await prisma.adopterProfile.findUnique({ where: { userId: session.user.id }, select: { id: true, completedAt: true } })
    : token ? await prisma.adopterProfile.findUnique({ where: { anonymousToken: token }, select: { id: true, completedAt: true } }) : null;
  const rankedIds = profile?.completedAt
    ? (await prisma.matchResult.findMany({ where: { profileId: profile.id, engineVersion: MATCH_ENGINE_VERSION, animal: where }, orderBy: [{ score: "desc" }, { animal: { name: "asc" } }], select: { animalId: true } })).map((match) => match.animalId)
    : [];
  const total = sortByMatch && profile?.completedAt ? rankedIds.length : await prisma.animal.count({ where });
  const currentPage = Math.min(page, Math.max(1, Math.ceil(total / pageSize)));
  const pageIds = rankedIds.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const fetchedAnimals = await prisma.animal.findMany({
    where: sortByMatch && profile?.completedAt ? { ...where, id: { in: pageIds } } : where,
    orderBy: [{ publishedAt: "desc" }, { id: "asc" }],
    ...(sortByMatch && profile?.completedAt ? {} : { skip: (currentPage - 1) * pageSize, take: pageSize }),
    select: {
      id: true,
      name: true,
      slug: true,
      species: true,
      sex: true,
      size: true,
      breedPrimary: true,
      headlineIt: true,
      storyIt: true,
      shelter: { select: { name: true, comune: { select: { name: true } } } },
    },
  });
  const animalOrder = new Map(pageIds.map((id, index) => [id, index]));
  const animals = sortByMatch && profile?.completedAt
    ? fetchedAnimals.sort((a, b) => (animalOrder.get(a.id) ?? 0) - (animalOrder.get(b.id) ?? 0))
    : fetchedAnimals;

  function pageHref(targetPage: number) {
    const next = new URLSearchParams();
    if (species) next.set("species", species);
    if (size) next.set("size", size);
    if (query) next.set("q", query);
    if (sortByMatch) next.set("sort", "match");
    if (targetPage > 1) next.set("page", String(targetPage));
    const search = next.toString();
    return search ? `/it/animali?${search}` : "/it/animali";
  }

  return (
    <main className="catalog-page">
      <a className="catalog-home" href="/">PetMatch AI</a>
      <header className="catalog-heading">
        <p className="eyebrow">In cerca di casa</p>
        <h1>Trova il tuo prossimo compagno.</h1>
        <p className="intro">Esplora gli animali pubblicati dai rifugi.</p>
        <a className="match-catalog-link" href="/it/abbinamento">Preferisci partire dalle tue esigenze? Prova il matching.</a>
      </header>

      <form className="catalog-filters" action="/it/animali">
        <label>
          Cerca
          <input
            name="q"
            type="search"
            maxLength={80}
            defaultValue={query}
            placeholder="Nome o razza"
          />
        </label>
        <label>
          Specie
          <select name="species" defaultValue={species ?? ""}>
            <option value="">Tutte</option>
            {speciesOptions.map((value) => (
              <option key={value} value={value}>
                {label(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Taglia
          <select name="size" defaultValue={size ?? ""}>
            <option value="">Tutte</option>
            {sizeOptions.map((value) => (
              <option key={value} value={value}>
                {sizeLabel(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Ordina per
          <select name="sort" defaultValue={sortByMatch ? "match" : "recent"}>
            <option value="recent">Più recenti</option>
            <option value="match">Compatibilità personale</option>
          </select>
        </label>
        <button className="button" type="submit">
          Filtra
        </button>
        <a className="clear-filters" href="/it/animali">Rimuovi filtri</a>
      </form>

      <p className="catalog-count" aria-live="polite">
        {total === 1 ? "1 animale disponibile" : `${total} animali disponibili`}
      </p>

      {animals.length ? (
        <>
          <section className="animal-grid" aria-label="Animali disponibili">
            {animals.map((animal) => (
              <article className="animal-card" key={animal.slug}>
                <div className="animal-mark" aria-hidden="true">
                  {animal.species === "dog" ? "🐕" : "🐈"}
                </div>
                <div className="animal-card-body">
                  <p className="animal-meta">
                    {label(animal.species)} · {sexLabel(animal.sex)}
                    {animal.size ? ` · ${sizeLabel(animal.size)}` : ""}
                  </p>
                  <h2><a href={`/it/animali/${animal.slug}`}>{animal.name}</a></h2>
                  {animal.breedPrimary && (
                    <p className="animal-breed">{animal.breedPrimary}</p>
                  )}
                  {animal.headlineIt && (
                    <p className="animal-headline">{animal.headlineIt}</p>
                  )}
                  {animal.storyIt && (
                    <p className="animal-story">{animal.storyIt}</p>
                  )}
                  <p className="animal-shelter">
                    {animal.shelter.name} · {animal.shelter.comune.name}
                  </p>
                </div>
              </article>
            ))}
          </section>
          <nav className="catalog-pagination" aria-label="Paginazione catalogo">
            {currentPage > 1 && (
              <a className="button secondary" href={pageHref(currentPage - 1)}>
                Precedenti
              </a>
            )}
            <span>Pagina {currentPage}</span>
            {currentPage * pageSize < total && (
              <a className="button" href={pageHref(currentPage + 1)}>
                Successivi
              </a>
            )}
          </nav>
        </>
      ) : (
        <section className="catalog-empty">
          <h2>Nessun animale trovato</h2>
          <p>Prova a cambiare i filtri. I nuovi animali pubblicati appariranno qui.</p>
        </section>
      )}
    </main>
  );
}
