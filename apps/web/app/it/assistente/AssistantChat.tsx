"use client";

import { FormEvent, useState } from "react";

type Citation = { title: string; organization: string; url: string; verified_at: string };
type Reply = { answer: string; engine: string; pipeline: string[]; citations: Citation[]; disclosure: string };

const copy = {
  it: { title: "Assistente per adozione e cura", intro: "Fai una domanda: userò le fonti riportate qui sotto.", placeholder: "Es. Quali alimenti sono pericolosi per un cane?", send: "Invia", language: "Lingua", source: "Fonti", disclosure: "Informazione generale: per diagnosi, emergenze o decisioni sanitarie contatta un veterinario.", error: "Non riesco a contattare l’assistente. Riprova tra poco.", model: "Risposta generata con un modello linguistico e fonti", fallback: "Risposta estratta dalle fonti (nessun modello linguistico configurato)", safety: "Indicazione di sicurezza", unknown: "Nessuna risposta: fonti insufficienti" },
  en: { title: "Adoption and care assistant", intro: "Ask a question; the sources used are listed below.", placeholder: "E.g. Which foods are dangerous for a dog?", send: "Send", language: "Language", source: "Sources", disclosure: "General information: contact a veterinarian for diagnosis, emergencies, or health decisions.", error: "The assistant is unavailable. Please try again shortly.", model: "Answer generated with a language model and sources", fallback: "Source-based answer (no language model configured)", safety: "Safety guidance", unknown: "No answer: insufficient sources" },
} as const;

export default function AssistantChat() {
  const [locale, setLocale] = useState<"it" | "en">("it");
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState<Reply | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const text = copy[locale];

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setReply(null);
    try {
      const response = await fetch("/api/assistant", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, locale }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? text.error);
      setReply(payload as Reply);
    } catch { setError(text.error); } finally { setBusy(false); }
  }

  return <section className="assistant-chat">
    <label>{text.language}<select value={locale} onChange={(event) => setLocale(event.target.value as "it" | "en")}><option value="it">Italiano</option><option value="en">English</option></select></label>
    <h1>{text.title}</h1><p className="intro">{text.intro}</p>
    <form onSubmit={submit}><label htmlFor="assistant-question">{locale === "it" ? "La tua domanda" : "Your question"}</label><textarea id="assistant-question" value={message} maxLength={1200} required minLength={2} onChange={(event) => setMessage(event.target.value)} placeholder={text.placeholder} /><button className="button" disabled={busy}>{busy ? "…" : text.send}</button></form>
    {error && <p role="alert" className="match-error">{error}</p>}
    {reply && <article className="assistant-reply"><p>{reply.answer}</p><p className="match-disclaimer">{reply.disclosure}</p><p><strong>{text.source}</strong></p><ul>{reply.citations.map((citation) => <li key={citation.url}><a href={citation.url} target="_blank" rel="noreferrer">{citation.organization}: {citation.title}</a> · {citation.verified_at}</li>)}</ul><small>{reply.engine === "pretrained_model_rag" ? text.model : reply.engine === "retrieval_fallback" ? text.fallback : reply.engine === "safety_guidance" ? text.safety : text.unknown}</small></article>}
    <p className="match-disclaimer">{text.disclosure}</p>
  </section>;
}
