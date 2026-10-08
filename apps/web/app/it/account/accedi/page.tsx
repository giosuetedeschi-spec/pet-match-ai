import AuthForm from "../AuthForm";

export const metadata = { title: "Accedi — PetMatch AI" };

export default function LoginPage() {
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><header className="catalog-heading"><p className="eyebrow">Il tuo profilo</p><h1>Accedi.</h1><p className="intro">Dopo l'accesso ritroverai il profilo adottante e i preferiti collegati al tuo account.</p></header><AuthForm mode="login" /><p><a className="match-catalog-link" href="/it/account/crea">Crea un account</a></p></main>;
}
