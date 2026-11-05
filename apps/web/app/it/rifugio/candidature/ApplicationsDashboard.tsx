"use client";

import { useEffect, useState } from "react";
import { resolveHomeVisitDraft } from "@/lib/application-input";

type Application = {
  id: string; status: string; motivationalNotes: string; shelterNotes: string | null; submittedAt: string;
  adopter: { fullName: string; email: string; phone: string | null };
  animal: { name: string; slug: string };
  homeVisit: { evaluatorName: string; scheduledAt: string; outcome: string } | null;
};
const statusLabels: Record<string, string> = { submitted: "Inviata", in_review: "In valutazione", home_visit: "Visita programmata", approved: "Approvata", rejected: "Non approvata" };
function toLocalDateTime(value: string) {
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

export default function ApplicationsDashboard() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [status, setStatus] = useState<Record<string, string>>({});
  const [schedule, setSchedule] = useState<Record<string, { evaluatorName: string; scheduledAt: string }>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true);
    try {
      const response = await fetch("/api/shelter/applications", { cache: "no-store" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? "Non riesco a caricare le candidature.");
      setApplications(payload.applications);
      setStatus(Object.fromEntries(payload.applications.map((application: Application) => [application.id, application.status])));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Errore di rete."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  async function update(applicationId: string) {
    setError("");
    const selected = status[applicationId];
    const application = applications.find((item) => item.id === applicationId);
    const existingVisit = application?.homeVisit;
    const editedVisit = schedule[applicationId];
    const visit = resolveHomeVisitDraft(editedVisit, existingVisit ? { evaluatorName: existingVisit.evaluatorName, scheduledAt: toLocalDateTime(existingVisit.scheduledAt) } : null);
    if (selected === "home_visit" && (!visit.evaluatorName.trim() || !visit.scheduledAt)) {
      setError("Per programmare la visita indica operatore e data.");
      return;
    }
    const body: Record<string, unknown> = { applicationId, status: selected };
    if (selected === "home_visit") body.visit = visit ? { ...visit, scheduledAt: new Date(visit.scheduledAt).toISOString() } : undefined;
    try {
      const response = await fetch("/api/shelter/applications", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? "Non riesco ad aggiornare la candidatura.");
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Errore di rete."); }
  }
  if (loading) return <p>Caricamento candidature…</p>;
  return <div className="application-list">{error && <p role="alert">{error}</p>}{applications.length ? applications.map((application) => <article className="application-card" key={application.id}>
    <p className="eyebrow">{application.animal.name} · {statusLabels[application.status] ?? application.status}</p>
    <h2>{application.adopter.fullName}</h2><p><a href={`mailto:${encodeURIComponent(application.adopter.email)}`}>{application.adopter.email}</a>{application.adopter.phone ? ` · ${application.adopter.phone}` : ""}</p>
    <p>{application.motivationalNotes}</p><p>Ricevuta il {new Date(application.submittedAt).toLocaleString("it-IT")}</p>
    {application.homeVisit && <p>Visita: {new Date(application.homeVisit.scheduledAt).toLocaleString("it-IT")} · {application.homeVisit.evaluatorName}</p>}
    <label>Stato <select value={status[application.id] ?? application.status} onChange={(event) => setStatus((previous) => ({ ...previous, [application.id]: event.target.value }))}>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    {status[application.id] === "home_visit" && <div className="visit-fields"><label>Operatore <input value={schedule[application.id]?.evaluatorName ?? application.homeVisit?.evaluatorName ?? ""} onChange={(event) => setSchedule((previous) => ({ ...previous, [application.id]: { evaluatorName: event.target.value, scheduledAt: previous[application.id]?.scheduledAt ?? (application.homeVisit ? toLocalDateTime(application.homeVisit.scheduledAt) : "") } }))} /></label><label>Data e ora <input type="datetime-local" value={schedule[application.id]?.scheduledAt ?? (application.homeVisit ? toLocalDateTime(application.homeVisit.scheduledAt) : "")} onChange={(event) => setSchedule((previous) => ({ ...previous, [application.id]: { evaluatorName: previous[application.id]?.evaluatorName ?? application.homeVisit?.evaluatorName ?? "", scheduledAt: event.target.value } }))} /></label></div>}
    <button className="button" type="button" onClick={() => void update(application.id)}>Salva aggiornamento</button>
  </article>) : <section className="application-card"><p>Non ci sono candidature per le schede dei tuoi rifugi.</p></section>}</div>;
}
