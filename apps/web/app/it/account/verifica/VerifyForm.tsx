"use client";

import { useState } from "react";

export default function VerifyForm({ token }: { token: string }) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function verify() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "Link non valido.");
      setMessage("Email verificata. Il tuo profilo è collegato all'account.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Link non valido.");
    } finally {
      setBusy(false);
    }
  }
  return <section className="catalog-empty">{error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}{message ? <a className="button" href="/it/abbinamento/risultati">Vai ai tuoi abbinamenti</a> : <button className="button" type="button" onClick={verify} disabled={busy || !token}>{busy ? "Verifica…" : "Conferma email"}</button>}</section>;
}
