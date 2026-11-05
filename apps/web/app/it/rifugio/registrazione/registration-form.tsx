"use client";

import { FormEvent, useState } from "react";

const types = [["canile_comunale", "Canile comunale"], ["canile_privato", "Canile privato"], ["gattile", "Gattile"], ["associazione", "Associazione"], ["rifugio", "Rifugio"]];

export default function ShelterRegistrationForm() {
  const [comuneQuery, setComuneQuery] = useState("");
  const [comuni, setComuni] = useState<{ id: number; name: string; provinceCode: string }[]>([]);
  const [comuneId, setComuneId] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function searchComuni(value: string) {
    setComuneQuery(value); setComuneId("");
    if (value.trim().length < 2) { setComuni([]); return; }
    const response = await fetch(`/api/comuni?q=${encodeURIComponent(value)}`);
    setComuni(response.ok ? await response.json() : []);
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setMessage("");
    const formElement = event.currentTarget; const form = new FormData(formElement);
    const response = await fetch("/api/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ accountType: "shelter", fullName: form.get("fullName"), email: form.get("email"), password: form.get("password"), phone: form.get("phone"), shelterName: form.get("shelterName"), legalName: form.get("legalName"), taxId: form.get("taxId"), shelterType: form.get("shelterType"), addressLine: form.get("addressLine"), postalCode: form.get("postalCode"), comuneId }) });
    const result = await response.json(); setBusy(false); setMessage(result.message ?? result.error ?? "Registrazione non riuscita.");
    if (response.ok) formElement.reset();
  }
  return <form className="catalog-empty shelter-registration" onSubmit={submit}>
    <h2>Referente</h2><label>Nome completo<input name="fullName" required minLength={2} maxLength={160} /></label><label>Email ufficiale<input name="email" type="email" required maxLength={254} /></label><label>Password (minimo 12 caratteri)<input name="password" type="password" required minLength={12} maxLength={128} /></label><label>Telefono<input name="phone" type="tel" maxLength={32} /></label>
    <h2>Dati della struttura</h2><label>Nome rifugio<input name="shelterName" required minLength={2} maxLength={160} /></label><label>Denominazione legale<input name="legalName" required minLength={2} maxLength={200} /></label><label>Codice fiscale o partita IVA<input name="taxId" required minLength={11} maxLength={16} pattern="([0-9]{11}|[A-Za-z0-9]{16})" /></label><label>Tipo<select name="shelterType" required defaultValue=""><option value="" disabled>Seleziona</option>{types.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Indirizzo<input name="addressLine" required minLength={5} maxLength={255} /></label><label>CAP<input name="postalCode" required inputMode="numeric" pattern="[0-9]{5}" maxLength={5} /></label><label>Comune<input value={comuneQuery} onChange={(event) => void searchComuni(event.target.value)} required autoComplete="off" /></label>{comuni.length > 0 && <label>Seleziona il comune<select value={comuneId} onChange={(event) => setComuneId(event.target.value)} required><option value="">Scegli…</option>{comuni.map((comune) => <option value={comune.id} key={comune.id}>{comune.name} ({comune.provinceCode})</option>)}</select></label>}<button className="button" disabled={busy || !comuneId}>{busy ? "Invio…" : "Invia richiesta"}</button>{message && <p role="status">{message}</p>}
  </form>;
}
