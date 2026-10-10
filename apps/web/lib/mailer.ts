import nodemailer from "nodemailer";

function transporter() {
  const host = process.env.SMTP_HOST;
  if (!host) throw new Error("SMTP_HOST is not configured.");
  const port = Number(process.env.SMTP_PORT ?? 1025);
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASSWORD;
  return nodemailer.createTransport({
    host,
    port,
    secure: port === 465,
    ...(user && pass ? { auth: { user, pass } } : {}),
  });
}

function baseUrl() {
  return (process.env.APP_URL ?? "http://localhost:3000").replace(/\/$/, "");
}

export async function sendVerificationEmail(email: string, name: string, token: string) {
  const link = `${baseUrl()}/it/account/verifica?token=${encodeURIComponent(token)}`;
  return transporter().sendMail({
    from: process.env.SMTP_FROM ?? "PetMatch AI <noreply@petmatch.local>",
    to: email,
    subject: "Conferma il tuo account PetMatch AI",
    text: `Ciao ${name}, conferma il tuo indirizzo email aprendo questo link: ${link}\nIl link scade tra 24 ore. Se non hai creato l'account, ignora questo messaggio.`,
  });
}

export async function sendShelterDecisionEmail(input: { email: string; name: string; shelter: string; approved: boolean; reason?: string; locale: "it" | "en" }) {
  const italian = input.locale === "it";
  const subject = input.approved
    ? (italian ? "Richiesta rifugio approvata" : "Shelter application approved")
    : (italian ? "Aggiornamento sulla richiesta rifugio" : "Shelter application update");
  const text = input.approved
    ? (italian
      ? `Ciao ${input.name}, la richiesta per ${input.shelter} è stata approvata. Puoi accedere al portale e pubblicare gli animali dopo aver completato le schede.`
      : `Hello ${input.name}, the application for ${input.shelter} has been approved. You can sign in to the portal and publish animals once their profiles are complete.`)
    : (italian
      ? `Ciao ${input.name}, la richiesta per ${input.shelter} non è stata approvata. Motivo: ${input.reason ?? "non specificato"}. Puoi contattare il supporto se desideri chiarimenti.`
      : `Hello ${input.name}, the application for ${input.shelter} was not approved. Reason: ${input.reason ?? "not specified"}. Contact support if you need clarification.`);
  return transporter().sendMail({ from: process.env.SMTP_FROM ?? "PetMatch AI <noreply@petmatch.local>", to: input.email, subject, text });
}

export type DigestAnimal = { name: string; species: string; slug: string; score: number; explanation: string };

export async function sendMatchingDigestEmail(input: {
  email: string;
  name: string;
  animals: DigestAnimal[];
  unsubscribeToken: string;
}) {
  const lines = input.animals.map((animal) =>
    `- ${animal.name} (${animal.species}), compatibilità ${animal.score}%: ${baseUrl()}/it/animali/${encodeURIComponent(animal.slug)}\n  ${animal.explanation}`,
  );
  const unsubscribe = `${baseUrl()}/it/notifiche/disiscrizione?token=${encodeURIComponent(input.unsubscribeToken)}`;
  const oneClickUnsubscribe = `${baseUrl()}/api/matching/unsubscribe?token=${encodeURIComponent(input.unsubscribeToken)}`;
  return transporter().sendMail({
    from: process.env.SMTP_FROM ?? "PetMatch AI <noreply@petmatch.local>",
    to: input.email,
    subject: "Nuovi animali compatibili con il tuo profilo",
    text: `Ciao ${input.name}, ecco i nuovi abbinamenti per te:\n\n${lines.join("\n")}\n\nGestisci o disattiva i digest senza accedere: ${unsubscribe}`,
    headers: { "List-Unsubscribe": `<${oneClickUnsubscribe}>`, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click" },
  });
}
