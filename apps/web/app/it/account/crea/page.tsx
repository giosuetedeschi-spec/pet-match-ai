import AuthForm from "../AuthForm";

export const metadata = { title: "Crea un account — PetMatch AI" };

export default function RegisterPage() {
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><header className="catalog-heading"><p className="eyebrow">Conserva il tuo matching</p><h1>Crea un account.</h1><p className="intro">Verifica la tua email per collegare il profilo e i preferiti a un account, e scegliere se ricevere i nuovi abbinamenti.</p></header><AuthForm mode="register" /></main>;
}
