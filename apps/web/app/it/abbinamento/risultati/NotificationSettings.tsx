"use client";

import { useEffect, useState } from "react";

type Preferences = { authenticated: boolean; enabled?: boolean; ready?: boolean; minimumScore?: number };

export default function NotificationSettings() {
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    fetch("/api/matching/notifications", { cache: "no-store" }).then((response) => response.json()).then(setPreferences).catch(() => setPreferences({ authenticated: false }));
  }, []);
  async function update(enabled: boolean) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/matching/notifications", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled, minimumScore: preferences?.minimumScore ?? 70 }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "Preferenza non salvata.");
      setPreferences((current) => current ? { ...current, enabled: data.enabled, minimumScore: data.minimumScore } : current);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Preferenza non salvata.");
    } finally {
      setBusy(false);
    }
  }
  if (!preferences) return <p role="status">Caricamento preferenze…</p>;
  if (!preferences.authenticated) return <section className="match-notification-setting"><h2>Ricevi i nuovi abbinamenti</h2><p>Collega il profilo a un account verificato per ricevere un digest email ogni 48 ore al massimo.</p><a className="button secondary" href="/it/account/crea">Crea account</a> <a href="/it/account/accedi">Accedi</a></section>;
  if (!preferences.ready) return <p>Completa il profilo per poter attivare le notifiche.</p>;
  return <section className="match-notification-setting"><h2>Nuovi abbinamenti</h2><label className="match-choice"><input type="checkbox" checked={Boolean(preferences.enabled)} disabled={busy} onChange={(event) => void update(event.target.checked)} /> Invia un digest email dei nuovi abbinamenti (massimo uno ogni 48 ore)</label><p><a href="/it/notifiche">Apri le notifiche in-app</a></p>{error && <p className="match-error" role="alert">{error}</p>}</section>;
}
