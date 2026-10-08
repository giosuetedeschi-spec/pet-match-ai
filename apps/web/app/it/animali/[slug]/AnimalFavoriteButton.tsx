"use client";

import { useState } from "react";

export default function AnimalFavoriteButton({ animalId, initialFavorite }: { animalId: string; initialFavorite: boolean }) {
  const [favorite, setFavorite] = useState(initialFavorite);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function toggle() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(favorite ? `/api/matching/favorites?animalId=${encodeURIComponent(animalId)}` : "/api/matching/favorites", {
        method: favorite ? "DELETE" : "POST",
        ...(favorite ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify({ animalId }) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "Preferenza non salvata.");
      setFavorite(!favorite);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Preferenza non salvata.");
    } finally {
      setBusy(false);
    }
  }
  return <div><button className="button secondary" type="button" disabled={busy} onClick={() => void toggle()}>{busy ? "Salvo…" : favorite ? "Rimuovi dai preferiti" : "Salva tra i preferiti"}</button>{error && <p role="alert" className="match-error">{error}</p>}</div>;
}
