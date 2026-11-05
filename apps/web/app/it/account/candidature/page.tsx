import { redirect } from "next/navigation";
import { getCurrentUserSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";
const labels: Record<string, string> = { submitted: "Inviata", in_review: "In valutazione", home_visit: "Visita programmata", approved: "Approvata", rejected: "Non approvata", withdrawn: "Ritirata" };

export default async function ApplicationsPage() {
  const session = await getCurrentUserSession();
  if (!session) redirect("/it/account/accedi");
  if (session.user.role !== "adopter") redirect("/it/animali");
  const applications = await prisma.adoptionApplication.findMany({
    where: { adopterId: session.user.id }, orderBy: { submittedAt: "desc" },
    select: { id: true, status: true, motivationalNotes: true, submittedAt: true, animal: { select: { name: true, slug: true, species: true, shelter: { select: { name: true, comune: { select: { name: true } } } } } }, homeVisit: { select: { evaluatorName: true, scheduledAt: true } } },
  });
  return <main className="catalog-page"><a className="catalog-home" href="/it/animali">← Tutti gli animali</a><header className="catalog-heading"><p className="eyebrow">Area personale</p><h1>Le mie candidature</h1><p className="intro">Consulta lo stato e gli eventuali appuntamenti comunicati dai rifugi.</p></header>
    {applications.length ? <div className="application-list">{applications.map((application) => <article className="application-card" key={application.id}><p className="eyebrow">{labels[application.status] ?? application.status}</p><h2><a href={`/it/animali/${application.animal.slug}`}>{application.animal.name}</a></h2><p>{application.animal.shelter.name} · {application.animal.shelter.comune.name} · inviata il {application.submittedAt.toLocaleDateString("it-IT")}</p><details><summary>La tua motivazione</summary><p>{application.motivationalNotes}</p></details>{application.homeVisit && <p>Visita pre-affido: {application.homeVisit.scheduledAt.toLocaleString("it-IT")} · {application.homeVisit.evaluatorName}</p>}</article>)}</div> : <section className="application-card"><p>Non hai ancora inviato candidature.</p><a className="button" href="/it/animali">Esplora gli animali</a></section>}
  </main>;
}
