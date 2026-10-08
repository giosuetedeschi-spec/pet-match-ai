import MatchWizard from "./MatchWizard";

export const metadata = {
  title: "Trova il tuo abbinamento — PetMatch AI",
  description: "Rispondi a poche domande per trovare animali compatibili con la tua vita.",
};

export default function MatchingPage() {
  return (
    <main className="catalog-page">
      <a className="catalog-home" href="/">PetMatch AI</a>
      <header className="catalog-heading">
        <p className="eyebrow">Un incontro adatto alla tua vita</p>
        <h1>Chi potrebbe sentirsi a casa con te?</h1>
        <p className="intro">
          Raccontaci qualcosa della tua quotidianità. Confronteremo le tue risposte
          con le informazioni condivise dai rifugi.
        </p>
      </header>
      <MatchWizard />
      <p className="match-method-note">
        Il profilo resta anonimo in questo browser e può essere cancellato in qualsiasi momento.
        Il punteggio confronta compatibilità e preferenze; non sostituisce il colloquio con il rifugio.
      </p>
    </main>
  );
}
