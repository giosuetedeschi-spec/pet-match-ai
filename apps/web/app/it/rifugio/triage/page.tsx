import { redirect } from "next/navigation";
import { getCurrentUserSession } from "@/lib/auth";
import { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import RefreshTriage from "./refresh-triage";

export const dynamic = "force-dynamic";

type Factor = { label: string; direction?: "positive" | "negative" };
type PredictionRow = {
  animalId: string;
  modelVersion: string;
  mode: string;
  predictedAt: Date;
  adoptionProbability: number;
  estimatedDaysIfAdopted: number | null;
  bucketProbabilities: unknown;
  topFactors: unknown;
  dataCompleteness: number;
  name: string;
  slug: string;
  shelterName: string;
};

function factors(value: unknown): Factor[] {
  let parsed = value;
  if (typeof value === "string") {
    try { parsed = JSON.parse(value); } catch { return []; }
  }
  if (!Array.isArray(parsed)) return [];
  return parsed.flatMap((item) => {
    if (!item || typeof item !== "object" || !("label" in item)) return [];
    const direction = "direction" in item && (item.direction === "positive" || item.direction === "negative") ? item.direction : undefined;
    return [{ label: String(item.label), direction }];
  });
}

function buckets(value: unknown): Record<string, number> {
  let parsed = value;
  if (typeof value === "string") { try { parsed = JSON.parse(value); } catch { return {}; } }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
  return Object.fromEntries(Object.entries(parsed).filter((entry): entry is [string, number] => typeof entry[1] === "number"));
}

export default async function ShelterTriagePage() {
  const session = await getCurrentUserSession();
  if (!session || session.user.role !== "shelter_staff") redirect("/");
  const shelterIds = (await prisma.shelterMember.findMany({
    where: { userId: session.user.id }, select: { shelterId: true },
  })).map(({ shelterId }) => shelterId);
  const predictions = shelterIds.length ? await prisma.$queryRaw<PredictionRow[]>(Prisma.sql`
    SELECT ap.animal_id AS animalId, ap.model_version AS modelVersion, ap.mode, ap.predicted_at AS predictedAt,
      ap.adoption_probability AS adoptionProbability, ap.estimated_days_if_adopted AS estimatedDaysIfAdopted,
      ap.bucket_probabilities AS bucketProbabilities, ap.top_factors AS topFactors, ap.data_completeness AS dataCompleteness,
      a.name, a.slug, s.name AS shelterName
    FROM animal_predictions ap JOIN animals a ON a.id = ap.animal_id JOIN shelters s ON s.id = a.shelter_id
    JOIN (SELECT animal_id, MAX(predicted_at) AS latest FROM animal_predictions GROUP BY animal_id) latest
      ON latest.animal_id = ap.animal_id AND latest.latest = ap.predicted_at
    WHERE a.shelter_id IN (${Prisma.join(shelterIds)}) AND a.status = 'available' AND a.deleted_at IS NULL
      AND s.status = 'active' AND s.deleted_at IS NULL
    ORDER BY ap.adoption_probability ASC LIMIT 100
  `) : [];
  const mode = predictions[0]?.mode ?? "none";

  return (
    <main className="catalog-page">
      <a className="catalog-home" href="/it/rifugio/animali">Area rifugi</a>
      <header className="catalog-heading">
        <p className="eyebrow">Supporto operativo</p>
        <h1>Animali da seguire</h1>
        <p className="intro">Stime sperimentali per aiutare a organizzare la promozione. Non valutano l’animale né una coppia adottante.</p>
      </header>
      <RefreshTriage />
      <section className="catalog-empty">
        <h2>Trasparenza del modello</h2>
        {mode === "none" ? <p>Nessuna valutazione disponibile. Aggiorna le stime per gli animali pubblicati.</p> : (
          <p>Modalità: <strong>{mode}</strong>. Il modello usa esiti storici di Austin, Texas; non è validato per rifugi italiani.</p>
        )}
        <p>La percentuale indica adozione fra gli esiti storici osservati. Non è una probabilità a 90 giorni né una data prevista. La permanenza è stimata solo condizionatamente a un’adozione registrata.</p>
        <p>Non usare queste stime per rifiutare ingressi, trasferire o escludere animali, decidere cure o valutare famiglie. Non sono mostrate al pubblico.</p>
      </section>
      {predictions.length ? (
        <section className="shelter-triage-list">
          {predictions.map((item) => (
            <article className="shelter-triage-card" key={`${item.animalId}-${item.predictedAt.toISOString()}`}>
              <p className="eyebrow">{item.shelterName} · {item.predictedAt.toLocaleString("it-IT")}</p>
              <h2><a href={`/it/animali/${item.slug}`}>{item.name}</a></h2>
              <p>Adozione tra gli esiti storici osservati: {Math.round((buckets(item.bucketProbabilities).adoption ?? item.adoptionProbability) * 100)}% · altri esiti: {Math.round((buckets(item.bucketProbabilities).other_observed_outcome ?? 1 - item.adoptionProbability) * 100)}%</p>
              <p>Permanenza prevista, solo se adottato: {item.estimatedDaysIfAdopted === null ? "non disponibile" : `${Math.round(item.estimatedDaysIfAdopted)} giorni`}. Non è una data promessa.</p>
              <p>Completezza dei quattro campi del modello: {Math.round(item.dataCompleteness * 100)}%</p>
              <p className="eyebrow">Modello {item.modelVersion}</p>
              {factors(item.topFactors).length > 0 && (
                <ul>{factors(item.topFactors).map((factor, index) => (
                  <li key={index}>{factor.label} — segnale {factor.direction === "positive" ? "associato a più adozioni" : "associato a meno adozioni"} nello storico</li>
                ))}</ul>
              )}
            </article>
          ))}
        </section>
      ) : (
        <section className="catalog-empty"><h2>Nessuna previsione salvata</h2><p>Genera una valutazione per gli animali pubblicati nei tuoi rifugi attivi.</p></section>
      )}
    </main>
  );
}
