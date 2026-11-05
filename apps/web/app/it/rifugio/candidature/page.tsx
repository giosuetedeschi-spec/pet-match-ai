import { redirect } from "next/navigation";
import { getCurrentUserSession } from "@/lib/auth";
import ApplicationsDashboard from "./ApplicationsDashboard";

export default async function ShelterApplicationsPage() {
  const session = await getCurrentUserSession();
  if (!session || session.user.role !== "shelter_staff") redirect("/it/account/accedi");
  return <main className="catalog-page"><a className="catalog-home" href="/it/rifugio">← Area rifugio</a><header className="catalog-heading"><p className="eyebrow">Area rifugio</p><h1>Candidature ricevute</h1><p className="intro">Valuta le richieste per gli animali dei tuoi rifugi e comunica l’esito o una visita.</p></header><ApplicationsDashboard /></main>;
}
