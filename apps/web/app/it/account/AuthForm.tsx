"use client";

import { FormEvent, useState } from "react";

export default function AuthForm({ mode }: { mode: "register" | "login" }) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(mode === "register" ? "/api/auth/register" : "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, fullName, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "Richiesta non riuscita.");
      if (mode === "login") window.location.assign("/it/abbinamento/risultati");
      else setMessage(data.message ?? "Controlla la tua casella email.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Richiesta non riuscita.");
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/resend-verification", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "Richiesta non riuscita.");
      setMessage(data.message);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Richiesta non riuscita.");
    } finally {
      setBusy(false);
    }
  }

  return <form className="account-form" onSubmit={submit}>
    {mode === "register" && <label>Nome completo<input required minLength={2} maxLength={160} autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} /></label>}
    <label>Email<input required type="email" maxLength={254} autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
    <label>Password<input required type="password" minLength={mode === "register" ? 12 : 1} maxLength={128} autoComplete={mode === "register" ? "new-password" : "current-password"} value={password} onChange={(event) => setPassword(event.target.value)} />{mode === "register" && <small>Almeno 12 caratteri.</small>}</label>
    {error && <p className="match-error" role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
    <button className="button" disabled={busy}>{busy ? "Attendi…" : mode === "register" ? "Crea account" : "Accedi"}</button>
    {mode === "register" && message && <button className="button secondary" type="button" disabled={busy} onClick={resend}>Invia di nuovo il link</button>}
  </form>;
}
