export default function Home() {
  return (
    <main className="page">
      <p className="eyebrow">PetMatch AI · in sviluppo</p>
      <h1>Ogni incontro può diventare casa.</h1>
      <p className="intro">
        Esplora gli animali pubblicati dai rifugi e scopri chi cerca una famiglia vicino a te.
        Il catalogo MVP è già disponibile; la nuova esperienza web cresce in parallelo.
      </p>
      <div className="actions">
        <a className="button" href="http://localhost:8501">Apri il catalogo MVP</a>
        <a className="button secondary" href="/api/health">Stato servizi</a>
      </div>
      <p className="note">Demo locale: le foto stock nel catalogo non ritraggono gli animali indicati.</p>
    </main>
  );
}
