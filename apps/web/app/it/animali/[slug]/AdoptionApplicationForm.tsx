"use client";

import { useState } from "react";

export default function AdoptionApplicationForm({ animalId, animalName, applicationId, signedIn, canApply }: { animalId: string; animalName: string; applicationId: string | null; signedIn: boolean; canApply: boolean }) {
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(Boolean(applicationId));
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setBusy(true);
    try {
      const response = await fetch("/api/applications", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ animalId, motivationalNotes: notes }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? "Non è stato possibile inviare la candidatura.");
      setSent(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Errore di rete."); }
    finally { setBusy(false); }
  }
  return <section className="animal-application" aria-labelledby="application-title">
    <h2 id="application-title">Candidati per {animalName}</h2>
    {sent ? <><p>La tua candidatura è stata inviata. Puoi seguirne lo stato dalla tua area personale.</p><a href="/it/account/candidature">Le mie candidature</a></> : !signedIn ? <><p>Accedi o crea un account adottante per inviare una candidatura e seguirne gli aggiornamenti.</p><a className="button" href="/it/account/accedi">Accedi</a></> : !canApply ? <p>Per candidarti serve un account adottante.</p> : <form onSubmit={submit}>
      <label htmlFor="application-notes">Perché vorresti accogliere {animalName}?</label>
      <textarea id="application-notes" value={notes} onChange={(event) => setNotes(event.target.value)} minLength={20} maxLength={5000} required rows={5} />
      <p>La motivazione sarà condivisa con il rifugio. Non inserire dati sanitari o informazioni non necessarie.</p>
      {error && <p role="alert">{error}</p>}
      <button className="button" type="submit" disabled={busy || notes.trim().length < 20}>{busy ? "Invio…" : "Invia candidatura"}</button>
    </form>}
  </section>;
}
