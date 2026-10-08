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
