"use client";

import { useCallback, useEffect, useState } from "react";
import type { MatchResult, MatchingResponse } from "@/lib/matching";
import NotificationSettings from "./NotificationSettings";

type Response = Omit<MatchingResponse, "allResults"> & { radiusKm: number };

export default function MatchResults() {
  const [data, setData] = useState<Response | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (radius?: number) => {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/matching/results${radius ? `?radius=${radius}` : ""}`, { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Risultati non disponibili.");
      setData(body as Response);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Risultati non disponibili.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function toggleFavorite(match: MatchResult) {
    const wasFavorite = Boolean(match.isFavorite);
    const response = await fetch(wasFavorite ? `/api/matching/favorites?animalId=${encodeURIComponent(match.animal.id)}` : "/api/matching/favorites", {
      method: wasFavorite ? "DELETE" : "POST",
      ...(wasFavorite ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify({ animalId: match.animal.id }) }),
    });
    if (!response.ok) return;
    setData((current) => current ? { ...current, results: current.results.map((item) => item.animal.id === match.animal.id ? { ...item, isFavorite: !wasFavorite } : item) } : current);
  }

  if (busy && !data) return <p role="status">Calcolo dei tuoi abbinamenti…</p>;
  if (error && !data) return <section className="catalog-empty"><h1>Non riesco a caricare i risultati</h1><p>{error}</p><a className="button" href="/it/abbinamento">Rivedi il questionario</a></section>;
  if (!data) return null;

  return <>
    <header className="catalog-heading"><p className="eyebrow">Il tuo profilo di compatibilità</p><h1>Questi animali potrebbero essere adatti a te.</h1><p className="intro">Il punteggio riassume quanto le informazioni disponibili corrispondono alle tue risposte. Leggi sempre i dettagli e confrontati con il rifugio.</p><div className="actions"><a className="button secondary" href="/it/abbinamento">Modifica il profilo</a><a className="button secondary" href="/it/preferiti">I tuoi preferiti</a></div></header>
    <NotificationSettings />
    {error && <p role="alert" className="match-error">{error}</p>}
    <p className="catalog-count" aria-live="polite">{data.results.length} abbinamenti · {data.eligibleCount} compatibili nel raggio di {data.radiusKm} km · {data.totalAvailable} schede valutate</p>
    {data.outsideRadiusCount > 0 && data.radiusKm < 200 && <section className="match-exclusions"><h2>Vuoi allargare la ricerca?</h2><p>{data.outsideRadiusCount} animali compatibili si trovano oltre il raggio attuale.</p><button className="button" disabled={busy} onClick={() => void load(Math.min(200, data.radiusKm * 2))}>Estendi a {Math.min(200, data.radiusKm * 2)} km</button></section>}
    {Object.keys(data.excludedCounts).length > 0 && <details className="match-exclusions"><summary>Animali esclusi dalle tue condizioni</summary><ul>{Object.entries(data.excludedCounts).map(([reason, count]) => <li key={reason}>{reason}: {count}</li>)}</ul></details>}
    {data.results.length ? <section className="match-grid" aria-label="Abbinamenti ordinati per compatibilità">{data.results.map((match) => <article className="match-card" key={match.animal.id}>
      <p className="match-score"><strong>{match.score}%</strong> di compatibilità{match.distanceKm !== null ? ` · ${match.distanceKm} km` : ""}</p><h2>{match.animal.name}</h2><p>{match.animal.species === "dog" ? "Cane" : "Gatto"}{match.animal.size ? ` · ${match.animal.size}` : ""} · {match.animal.shelter.name}, {match.animal.shelter.comune.name}</p>
      {match.reasons.length > 0 && <ul className="match-reasons">{match.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>}
      {match.considerations.length > 0 && <details><summary>Aspetti da approfondire</summary><ul>{match.considerations.map((item) => <li key={item}>{item}</li>)}</ul></details>}
      <details><summary>Come si compone il punteggio</summary><ul>{match.dimensions.map((dimension) => <li key={dimension.name}>{dimension.name}: {dimension.score}/100 ({Math.round(dimension.weight * 100)}%)</li>)}</ul></details>
      <button className="button secondary" type="button" onClick={() => void toggleFavorite(match)}>{match.isFavorite ? "Rimuovi dai preferiti" : "Salva tra i preferiti"}</button>
      <a className="match-catalog-link" href={`/it/animali/${match.animal.slug}`}>Consulta la scheda</a>
    </article>)}</section> : <section className="catalog-empty"><h2>Nessun abbinamento sopra la soglia</h2><p>Puoi ampliare il raggio oppure modificare le preferenze. Il punteggio non sostituisce il colloquio con il rifugio.</p><a className="button" href="/it/abbinamento">Modifica il profilo</a></section>}
    {data.belowThresholdCount > 0 && <p className="match-disclaimer">Altri {data.belowThresholdCount} animali nel raggio hanno un punteggio inferiore alla soglia mostrata.</p>}
    <p className="match-disclaimer">I dati mancanti sono trattati con prudenza e indicati come aspetti da verificare. Nessun punteggio garantisce l’esito dell’adozione.</p>
  </>;
}
