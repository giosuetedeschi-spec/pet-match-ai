"use client";

import { useState, type FormEvent } from "react";
import type { MatchingResponse } from "@/lib/matching";

export default function MatchForm() {
  const [response, setResponse] = useState<MatchingResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResponse(null);

    const form = new FormData(event.currentTarget);
    const payload: Record<string, unknown> = Object.fromEntries(form.entries());
    payload.outdoorSpace = form.get("outdoorSpace") === "yes";
    payload.hasDogs = form.get("hasDogs") === "yes";
    payload.hasCats = form.get("hasCats") === "yes";
    payload.dealbreakers = form.getAll("dealbreakers").map(String);
    payload.monthlyBudget = form.get("monthlyBudget") || null;

    try {
      const result = await fetch("/api/matching", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await result.json();
      if (!result.ok) throw new Error(data.error ?? "Richiesta non riuscita.");
      setResponse(data as MatchingResponse);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Non riesco a calcolare gli abbinamenti.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <form className="match-form" onSubmit={submit}>
        <fieldset>
          <legend>Che animale cerchi?</legend>
          <label>Specie
            <select name="species" defaultValue="any">
              <option value="any">Cane o gatto</option>
              <option value="dog">Cane</option>
              <option value="cat">Gatto</option>
            </select>
          </label>
          <label>Taglia preferita
            <select name="preferredSize" defaultValue="any">
              <option value="any">Nessuna preferenza</option>
              <option value="small">Piccola</option>
              <option value="medium">Media</option>
              <option value="large">Grande</option>
              <option value="xlarge">Molto grande</option>
            </select>
          </label>
          <label>Sesso preferito
            <select name="preferredSex" defaultValue="any">
              <option value="any">Nessuna preferenza</option>
              <option value="male">Maschio</option>
              <option value="female">Femmina</option>
            </select>
          </label>
        </fieldset>

        <fieldset>
          <legend>La tua casa e le persone con cui vivi</legend>
          <label>Abitazione
            <select name="housing" defaultValue="apartment">
              <option value="apartment">Appartamento</option>
              <option value="house">Casa senza giardino</option>
              <option value="garden">Casa con giardino</option>
              <option value="country">Campagna o cascina</option>
            </select>
          </label>
          <label>Superficie della casa
            <select name="housingSize" defaultValue="any">
              <option value="any">Qualsiasi</option>
              <option value="small">Meno di 50 m²</option>
              <option value="medium">Da 50 a 120 m²</option>
              <option value="large">Oltre 120 m²</option>
            </select>
          </label>
          <label>Hai uno spazio esterno?
            <select name="outdoorSpace" defaultValue="no">
              <option value="no">No</option>
              <option value="yes">Sì, balcone o giardino</option>
            </select>
          </label>
          <label>Età del bambino più piccolo in casa
            <select name="children" defaultValue="none">
              <option value="none">Non ci sono bambini</option>
              <option value="under6">Meno di 6 anni</option>
              <option value="6to11">Da 6 a 11 anni</option>
              <option value="12plus">12 anni o più</option>
            </select>
          </label>
          <label>Ci sono già cani in casa?
            <select name="hasDogs" defaultValue="no">
              <option value="no">No</option>
              <option value="yes">Sì</option>
            </select>
          </label>
          <label>Ci sono già gatti in casa?
            <select name="hasCats" defaultValue="no">
              <option value="no">No</option>
              <option value="yes">Sì</option>
            </select>
          </label>
        </fieldset>

        <fieldset>
          <legend>Il tempo e le cure che puoi dedicare</legend>
          <label>Ore al giorno in cui sarebbe solo
            <select name="hoursAlone" defaultValue="4">
              {[0, 2, 4, 6, 8, 10, 12, 14, 16].map((hours) => (
                <option key={hours} value={hours}>{hours} ore</option>
              ))}
            </select>
          </label>
          <label>Quanto sei attivo/a?
            <select name="activity" defaultValue="3">
              <option value="1">Poco, preferisco passeggiate brevi</option>
              <option value="2">Un po’ attivo/a</option>
              <option value="3">Moderatamente attivo/a</option>
              <option value="4">Molto attivo/a</option>
              <option value="5">Molto sportivo/a</option>
            </select>
          </label>
          <label>Esperienza con gli animali
            <select name="experience" defaultValue="first_time">
              <option value="first_time">È la prima volta</option>
              <option value="some">Ho già avuto animali</option>
              <option value="experienced">Ho molta esperienza</option>
            </select>
          </label>
          <label>Tempo per la cura del pelo
            <select name="groomingCapacity" defaultValue="3">
              <option value="1">Poco</option><option value="2">Un po’</option>
              <option value="3">Abbastanza</option><option value="4">Molto</option>
              <option value="5">Anche ogni giorno</option>
            </select>
          </label>
          <label>Tempo per l’educazione
            <select name="trainingCapacity" defaultValue="3">
              <option value="1">Poco</option><option value="2">Un po’</option>
              <option value="3">Abbastanza</option><option value="4">Molto</option>
              <option value="5">Anche ogni giorno</option>
            </select>
          </label>
          <label>Budget mensile indicativo per le cure (€)
            <input name="monthlyBudget" type="number" min="0" max="100000" step="10" placeholder="Facoltativo" />
          </label>
        </fieldset>

        <fieldset>
          <legend>Ci sono condizioni importanti per te?</legend>
          <p>Gli animali che non rispettano una condizione selezionata non compariranno tra i risultati.</p>
          {[
            ["no_special_needs", "Non posso accogliere un animale con esigenze speciali"],
            ["no_dogs_over_25kg", "Cerco un cane sotto i 25 kg"],
            ["house_trained", "È importante che sia già abituato alla vita in casa"],
            ["children", "Deve risultare compatibile con i bambini"],
            ["dogs", "Deve risultare compatibile con i cani"],
            ["cats", "Deve risultare compatibile con i gatti"],
            ["sterilized", "Cerco un animale già sterilizzato"],
          ].map(([value, label]) => (
            <label className="match-check" key={value}>
              <input type="checkbox" name="dealbreakers" value={value} /> {label}
            </label>
          ))}
        </fieldset>

        <p className="match-privacy">Le risposte vengono usate solo per calcolare questi risultati e non vengono salvate.</p>
        <button className="button" type="submit" disabled={loading}>
          {loading ? "Cerco gli abbinamenti…" : "Mostra gli abbinamenti"}
        </button>
        {error && <p className="match-error" role="alert">{error}</p>}
      </form>

      {response && (
        <section className="match-results" aria-live="polite">
          <h2>I tuoi possibili abbinamenti</h2>
          <p>
            {response.results.length} risultati mostrati su {response.eligibleCount} compatibili.
            {response.belowThresholdCount > 0 && ` ${response.belowThresholdCount} con punteggio basso non sono mostrati.`}
          </p>
          {Object.entries(response.excludedCounts).length > 0 && (
            <details className="match-exclusions">
              <summary>Motivi di esclusione · {response.totalAvailable - response.eligibleCount} animali</summary>
              <ul>{Object.entries(response.excludedCounts).map(([reason, count]) => <li key={reason}>{count}: {reason}</li>)}</ul>
            </details>
          )}
          {response.results.length > 0 ? (
            <div className="match-grid">
              {response.results.map((match) => (
                <article className="match-card" key={match.animal.slug}>
                  <p className="match-score">Compatibilità orientativa: <strong>{match.score}%</strong></p>
                  <h3>{match.animal.name}</h3>
                  <p className="animal-meta">
                    {match.animal.species === "dog" ? "Cane" : "Gatto"}
                    {match.animal.size ? ` · taglia ${match.animal.size}` : ""}
                    {match.animal.sex !== "unknown" ? ` · ${match.animal.sex === "male" ? "maschio" : "femmina"}` : ""}
                  </p>
                  <p className="animal-shelter">{match.animal.shelter.name} · {match.animal.shelter.comune.name}</p>
                  {match.reasons.length > 0 && <ul className="match-reasons">{match.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>}
                  {match.considerations.length > 0 && (
                    <details>
                      <summary>Da verificare con il rifugio ({match.considerations.length})</summary>
                      <ul>{match.considerations.map((item) => <li key={item}>{item}</li>)}</ul>
                    </details>
                  )}
                  <details>
                    <summary>Dettaglio del punteggio</summary>
                    <ul>{match.dimensions.map((dimension) => (
                      <li key={dimension.name}>{dimension.name}: {dimension.score}/100 ({Math.round(dimension.weight * 100)}%)</li>
                    ))}</ul>
                  </details>
                  <a className="match-catalog-link" href={`/it/animali?q=${encodeURIComponent(match.animal.name)}`}>
                    Trova {match.animal.name} nel catalogo
                  </a>
                </article>
              ))}
            </div>
          ) : (
            <p className="catalog-empty">Non ci sono abbinamenti da mostrare. Puoi modificare le risposte o allentare una condizione.</p>
          )}
          <p className="match-disclaimer">Il punteggio è indicativo: non garantisce l’esito dell’adozione e non sostituisce un colloquio con il rifugio.</p>
        </section>
      )}
    </>
  );
}
