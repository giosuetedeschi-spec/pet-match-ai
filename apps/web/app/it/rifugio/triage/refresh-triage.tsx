"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
export default function RefreshTriage() {
  const router = useRouter(); const [busy, setBusy] = useState(false); const [message, setMessage] = useState("");
  async function refresh() { setBusy(true); setMessage(""); const response = await fetch("/api/shelter/at-risk", { method: "POST" }); const data = await response.json(); setBusy(false); setMessage(data.error ?? `${data.refreshed} valutazioni aggiornate.`); if (response.ok) router.refresh(); }
  return <div className="actions"><button className="button" disabled={busy} onClick={() => void refresh()}>{busy ? "Aggiornamento…" : "Aggiorna valutazioni"}</button><p role="status">{message}</p></div>;
}
