export default function Home() {
  return (
    <main className="page">
      <p className="eyebrow">PetMatch AI</p>
      <h1>Ogni incontro può diventare casa.</h1>
      <p className="intro">
        Scopri gli animali che cercano una famiglia e conosci i rifugi che se ne
        prendono cura.
      </p>
      <div className="actions">
        <a className="button" href="/it/animali">
          Esplora gli animali
        </a>
        <a className="button secondary" href="/it/abbinamento">
          Trova un abbinamento
        </a>
        <a className="button secondary" href="http://localhost:8501">
          Catalogo MVP
        </a>
      </div>
    </main>
  );
}
