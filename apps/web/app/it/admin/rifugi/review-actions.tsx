"use client";
import { useState } from "react";

export default function ShelterReviewActions({ shelterId, emailVerified }: { shelterId: string; emailVerified: boolean }) {
  const [reason, setReason] = useState(""); const [message, setMessage] = useState("");
  async function decide(decision: "approve" | "reject") {
    const response = await fetch("/api/admin/shelters", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ shelterId, decision, reason }) });
    const result = await response.json(); setMessage(response.ok ? `Decisione registrata.${result.emailSent ? " Email inviata." : " Email non inviata: verifica SMTP."} Aggiorna la pagina per ricaricare la coda.` : result.error);
  }
  return <div className="actions"><button className="button" disabled={!emailVerified} onClick={() => void decide("approve")}>Approva</button><label>Motivo rifiuto<input value={reason} onChange={(event) => setReason(event.target.value)} minLength={5} maxLength={2000} /></label><button className="button" disabled={reason.trim().length < 5} onClick={() => void decide("reject")}>Rifiuta</button><p role="status">{message}</p>{!emailVerified && <p>Per approvare serve la verifica dell’email.</p>}</div>;
}
