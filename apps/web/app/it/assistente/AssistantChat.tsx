"use client";

import { FormEvent, useState } from "react";

type Citation = { id: string; title: string; organization: string; url: string; verified_at: string };
type Claim = { text: string; source_ids: string[] };
type Animal = { name: string; slug: string; species: string; breed: string; shelter: string; city: string; description: string };
type CommerceOffer = { retailer: string; product_name: string; brand: string; product_url: string; price_amount: string; currency: string; availability: "available" | "unavailable"; availability_scope: "online"; fetched_at: string };
type Reply = { answer: string; claims: Claim[]; engine: string; pipeline: string[]; retrieved: { id: string; title: string }[]; citations: Citation[]; catalog_animals: Animal[]; catalog_filters?: { species?: "dog" | "cat"; city?: string; good_with_children?: boolean }; commerce_offers?: CommerceOffer[]; abstained: boolean; disclosure: string };
type Message = { role: "user" | "assistant"; content: string; reply?: Reply };

const copy = {
  it: { title: "Assistente per adozione e cura", intro: "Fai domande su cani, gatti e adozione. Risponderò con fonti, oppure dichiarerò quando non ne ho abbastanza.", placeholder: "Es. Come scelgo un cane adatto alla mia vita?", send: "Invia", language: "Lingua", source: "Fonte", disclosure: "Informazione generale: per diagnosi, emergenze o decisioni sanitarie contatta un veterinario.", error: "Non riesco a contattare l’assistente. Riprova tra poco.", model: "Risposta generata con un modello linguistico e affermazioni collegate alle fonti", fallback: "Estratto dalla fonte (modello non configurato o risposta generata non accettata)", controlled: "Fonte sanitaria controllata; generazione esclusa", safety: "Indicazione di sicurezza", catalog: "Catalogo pubblico consultato", unknown: "Fonti insufficienti", commerce: "Offerte online verificate", onlineScope: "Disponibilita online", onlineAvailable: "Disponibile online", onlineUnavailable: "Non disponibile online", localStockUnknown: "Disponibilita del negozio fisico non verificata", fetchedAt: "Dati recuperati il", clear: "Nuova conversazione", trace: "Come ho costruito la risposta", animals: "Schede pubbliche disponibili", filters: "Filtri applicati", children: "compatibilità esplicita con bambini", childNote: "Compatibilità da confermare comunque con il rifugio.", abstainExample: "Le offerte visualizzate sono online. Per la disponibilita in un negozio fisico, verifica con il rivenditore.", adoption: "Catalogo consultato in sola lettura. Chiedi al rifugio per confermare compatibilità e disponibilità." },
  en: { title: "Adoption and care assistant", intro: "Ask about dogs, cats, and adoption. I’ll cite sources or say when evidence is insufficient.", placeholder: "E.g. How do I choose a dog that fits my life?", send: "Send", language: "Language", source: "Source", disclosure: "General information: contact a veterinarian for diagnosis, emergencies, or health decisions.", error: "The assistant is unavailable. Please try again shortly.", model: "Generated model answer with claims linked to sources", fallback: "Source excerpt (model not configured or generated answer rejected)", controlled: "Controlled health source; generation disabled", safety: "Safety guidance", catalog: "Public catalogue checked", unknown: "Insufficient sources", commerce: "Verified online offers", onlineScope: "Online availability", onlineAvailable: "Available online", onlineUnavailable: "Unavailable online", localStockUnknown: "Physical-store availability not checked", fetchedAt: "Fetched at", clear: "New conversation", trace: "How this answer was built", animals: "Published animals available", filters: "Applied filters", children: "explicit child-compatibility assessment", childNote: "Confirm compatibility with the shelter before adoption.", abstainExample: "Displayed offers are online. Check physical store stock with the retailer.", adoption: "Read-only public catalogue. Contact the shelter to confirm fit and availability." },
} as const;

export function engineLabel(engine: string, text: { model: string; fallback: string; controlled: string; safety: string; catalog: string; commerce: string; unknown: string }) {
  if (engine === "pretrained_model_rag") return text.model;
  if (engine === "retrieval_fallback") return text.fallback;
  if (engine === "controlled_source") return text.controlled;
  if (engine === "safety_guidance") return text.safety;
  if (engine === "catalog_lookup") return text.catalog;
  if (engine === "commerce_lookup") return text.commerce;
  return text.unknown;
}

export default function AssistantChat() {
  const [locale, setLocale] = useState<"it" | "en">("it");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const text = copy[locale];

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = message.trim();
    if (!question) return;
    setBusy(true); setError(""); setMessage("");
    const history = messages.map(({ role, content }) => ({ role, content }));
    try {
      const response = await fetch("/api/assistant", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: question, locale, history }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? text.error);
      setMessages((current) => [...current, { role: "user", content: question }, { role: "assistant", content: payload.answer, reply: payload as Reply }]);
    } catch { setError(text.error); setMessage(question); } finally { setBusy(false); }
  }

  return <section className="assistant-chat">
    <label>{text.language}<select value={locale} onChange={(event) => setLocale(event.target.value as "it" | "en")}><option value="it">Italiano</option><option value="en">English</option></select></label>
    <h1>{text.title}</h1><p className="intro">{text.intro}</p>
    <details className="assistant-demo-note"><summary>{locale === "it" ? "Ambito e limiti" : "Scope and limits"}</summary><p>{text.abstainExample}</p><p>{text.disclosure}</p></details>
    <form onSubmit={submit}><label htmlFor="assistant-question">{locale === "it" ? "La tua domanda" : "Your question"}</label><textarea id="assistant-question" value={message} maxLength={1200} required minLength={2} onChange={(event) => setMessage(event.target.value)} placeholder={text.placeholder} /><div className="assistant-actions"><button className="button" disabled={busy}>{busy ? "…" : text.send}</button>{messages.length > 0 && <button className="button secondary" type="button" onClick={() => setMessages([])}>{text.clear}</button>}</div></form>
    {error && <p role="alert" className="match-error">{error}</p>}
    <div className="assistant-thread" aria-live="polite">{messages.map((item, index) => <article className={`assistant-message ${item.role}`} key={`${index}-${item.role}`}><strong>{item.role === "user" ? (locale === "it" ? "Tu" : "You") : text.title}</strong>{(!item.reply || item.reply.claims.length === 0) && <p>{item.content}</p>}{item.reply && <>
      {item.reply.claims.map((claim, claimIndex) => <div className="assistant-claim" key={claimIndex}><span>{claim.text}</span>{claim.source_ids.map((id) => { const source = item.reply?.citations.find((citation) => citation.id === id); return source ? <a key={id} href={source.url} target="_blank" rel="noreferrer">[{source.organization}: {source.title}]</a> : null; })}</div>)}
      {item.reply.catalog_animals.length > 0 && <section className="assistant-animal-results"><h2>{text.animals}</h2>{item.reply.catalog_filters && <small>{text.filters}: {[item.reply.catalog_filters.species, item.reply.catalog_filters.city, item.reply.catalog_filters.good_with_children ? text.children : ""].filter(Boolean).join(" · ")}</small>}<div>{item.reply.catalog_animals.map((animal) => <article key={animal.slug}><h3><a href={`/it/animali/${animal.slug}`}>{animal.name}</a></h3><p>{animal.species} · {animal.breed || (locale === "it" ? "Meticcio" : "Mixed breed")} · {animal.shelter}, {animal.city}</p>{animal.description && <p>{animal.description}</p>}</article>)}</div>{item.reply.catalog_filters?.good_with_children && <small>{text.childNote}</small>}<small>{text.adoption}</small></section>}
      {!!item.reply.commerce_offers?.length && <section className="assistant-commerce-results"><h2>{text.commerce}</h2>{item.reply.commerce_offers.map((offer, offerIndex) => { const fetched = new Date(offer.fetched_at); const fetchedLabel = Number.isNaN(fetched.getTime()) ? offer.fetched_at : `${fetched.toLocaleString(locale === "it" ? "it-IT" : "en-GB", { timeZone: "UTC" })} UTC`; return <article key={`${offer.product_url}-${offerIndex}`}><h3><a href={offer.product_url} target="_blank" rel="noreferrer">{offer.product_name}</a></h3><p>{offer.brand} · {offer.retailer}</p><p><strong>{offer.price_amount} {offer.currency}</strong></p><p>{text.onlineScope}: {offer.availability === "available" ? text.onlineAvailable : text.onlineUnavailable}</p><small>{text.localStockUnknown}</small><br /><small>{text.fetchedAt}: <time dateTime={offer.fetched_at}>{fetchedLabel}</time></small></article>;})}</section>}
      <small>{engineLabel(item.reply.engine, text)}</small><details className="assistant-trace"><summary>{text.trace}</summary><ol>{item.reply.pipeline.map((step, stepIndex) => <li key={stepIndex}>{step}</li>)}</ol>{item.reply.retrieved.length > 0 && <p>{locale === "it" ? "Fonti candidate recuperate" : "Candidate sources retrieved"}: {item.reply.retrieved.map((source) => source.title).join("; ")}</p>}</details>
      <p className="match-disclaimer">{item.reply.disclosure}</p>
    </>}</article>)}</div>
    <p className="match-disclaimer">{text.disclosure}</p>
  </section>;
}
