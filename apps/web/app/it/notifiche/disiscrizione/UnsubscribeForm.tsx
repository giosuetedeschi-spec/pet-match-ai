"use client";

import { useState } from "react";

export default function UnsubscribeForm({ token }: { token: string }) {
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  async function unsubscribe() {
    setError("");
    const response = await fetch(`/api/matching/unsubscribe?token=${encodeURIComponent(token)}`, { method: "POST" });
    const data = await response.json();
    if (!response.ok) { setError(data.error ?? "Disiscrizione non riuscita."); return; }
    setDone(true);
  }
  return <section className="catalog-empty">{done ? <p role="status">Disiscrizione completata. Non riceverai altri digest.</p> : <><p>Puoi interrompere i digest email di PetMatch AI senza accedere.</p><button className="button" type="button" onClick={unsubscribe} disabled={!token}>Disiscrivimi</button></>}{error && <p role="alert" className="match-error">{error}</p>}</section>;
}
