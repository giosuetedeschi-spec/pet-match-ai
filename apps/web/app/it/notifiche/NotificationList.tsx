"use client";

import { useEffect, useState } from "react";

type Notification = { id: string; type: string; titleKey: string; payload: unknown; linkUrl: string | null; readAt: string | null; createdAt: string };

export default function NotificationList() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    fetch("/api/notifications", { cache: "no-store" }).then(async (response) => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "Notifiche non disponibili.");
      setNotifications(data.notifications ?? []);
    }).catch((cause) => setError(cause instanceof Error ? cause.message : "Notifiche non disponibili.")).finally(() => setLoaded(true));
  }, []);
  if (!loaded) return <p role="status">Caricamento…</p>;
  if (error) return <section className="catalog-empty"><p role="alert">{error}</p><a className="button" href="/it/account/accedi">Accedi</a></section>;
  if (!notifications.length) return <section className="catalog-empty"><h2>Ancora nessun nuovo abbinamento</h2><p>Quando troveremo nuovi animali compatibili, li mostreremo qui.</p><a className="button" href="/it/abbinamento/risultati">Torna ai risultati</a></section>;
  return <section className="notification-list">{notifications.map((notification) => {
    const payload = notification.payload as { animals?: { id: string; name: string; slug: string; score: number; explanation?: string }[] };
    return <article className={`notification-card${notification.readAt ? " read" : ""}`} key={notification.id}><p className="eyebrow">{new Date(notification.createdAt).toLocaleString("it-IT")}</p><h2>Nuovi abbinamenti</h2><ul>{(payload.animals ?? []).map((animal) => <li key={animal.id}><a href={`/it/animali/${animal.slug}`}>{animal.name}</a> · {animal.score}%{animal.explanation ? <p>{animal.explanation}</p> : null}</li>)}</ul>{!notification.readAt && <button className="button secondary" type="button" onClick={async () => { await fetch("/api/notifications", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: notification.id }) }); setNotifications((items) => items.map((item) => item.id === notification.id ? { ...item, readAt: new Date().toISOString() } : item)); }}>Segna come letta</button>}</article>;
  })}</section>;
}
