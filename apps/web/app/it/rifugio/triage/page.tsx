import { redirect } from "next/navigation";
import { getCurrentUserSession } from "@/lib/auth";
import { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import RefreshTriage from "./refresh-triage";

export const dynamic = "force-dynamic";
type PredictionRow = { animalId: string; modelVersion: string; mode: string; predictedAt: Date; adoptionProbability: number; topFactors: unknown; dataCompleteness: number; name: string; slug: string; shelterName: string };
function factors(value: unknown): unknown[] { if (Array.isArray(value)) return value; if (typeof value === "string") { try { const parsed: unknown = JSON.parse(value); return Array.isArray(parsed) ? parsed : []; } catch { return []; } } return []; }
export default async function ShelterTriagePage() {
  const session = await getCurrentUserSession();
  if (!session || session.user.role !== "shelter_staff") redirect("/");
  const shelterIds = (await prisma.shelterMember.findMany({ where: { userId: session.user.id }, select: { shelterId: true } })).map(({ shelterId }) => shelterId);
  const predictions = shelterIds.length ? await prisma.$queryRaw<PredictionRow[]>(Prisma.sql`
    SELECT ap.animal_id AS animalId, ap.model_version AS modelVersion, ap.mode, ap.predicted_at AS predictedAt,
      ap.adoption_probability AS adoptionProbability, ap.top_factors AS topFactors, ap.data_completeness AS dataCompleteness,
      a.name, a.slug, s.name AS shelterName
    FROM animal_predictions ap JOIN animals a ON a.id = ap.animal_id JOIN shelters s ON s.id = a.shelter_id
    JOIN (SELECT animal_id, MAX(predicted_at) AS latest FROM animal_predictions GROUP BY animal_id) latest
      ON latest.animal_id = ap.animal_id AND latest.latest = ap.predicted_at
    WHERE a.shelter_id IN (${Prisma.join(shelterIds)}) AND a.status = 'available' AND a.deleted_at IS NULL AND s.status = 'active' AND s.deleted_at IS NULL
    ORDER BY ap.adoption_probability ASC LIMIT 100
  `) : [];
  const mode = predictions[0]?.mode ?? "mock";
  return <main className="catalog-page"><a className="catalog-home" href="/it/rifugio/animali">Area rifugi</a><header className="catalog-heading"><p className="eyebrow">Supporto operativo</p><h1>Animali da seguire</h1><p className="intro">Priorità indicative per organizzare le attività di promozione. L’esito non è una valutazione dell’animale.</p></header><RefreshTriage /><section className="catalog-empty"><h2>Trasparenza del modello</h2><p>Modalità attuale: <strong>{mode}</strong>. {mode === "mock" ? "Il servizio usa un mock di sviluppo non validato; le percentuali non sono previsioni calibrate." : "Le stime non sono verificate per rifugi italiani."}</p><p>Non usare questi dati per rifiutare ingressi, trasferire o escludere animali, decidere cure o valutare famiglie adottanti. Nessun dato viene mostrato al pubblico.</p><p>Il file Cox incluso non viene caricato perché la feature list contiene variabili di esito non disponibili al momento della previsione.</p></section>{predictions.length ? <section className="shelter-triage-list">{predictions.map((item) => <article className="shelter-triage-card" key={item.animalId}><p className="eyebrow">{item.shelterName} · {item.predictedAt.toLocaleString("it-IT")}</p><h2><a href={`/it/animali/${item.slug}`}>{item.name}</a></h2><p>Probabilità cumulativa a 90 giorni (mock): {Math.round(item.adoptionProbability * 100)}%</p><p>Completezza dati: {Math.round(item.dataCompleteness * 100)}%</p><ul>{factors(item.topFactors).map((factor, index) => { const label = factor && typeof factor === "object" && "label" in factor ? String(factor.label) : "Indicatore"; return <li key={index}>{label}</li>; })}</ul></article>)}</section> : <section className="catalog-empty"><h2>Nessuna previsione salvata</h2><p>Genera una valutazione per gli animali pubblicati nei tuoi rifugi attivi.</p></section>}</main>;
}
