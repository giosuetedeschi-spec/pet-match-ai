import FavoriteList from "./FavoriteList";

export const metadata = { title: "I tuoi preferiti — PetMatch AI" };

export default function FavoritesPage() {
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><header className="catalog-heading"><p className="eyebrow">La tua selezione</p><h1>Animali che vuoi ricordare.</h1><p className="intro">I preferiti restano associati al profilo anonimo salvato in questo browser.</p><a className="match-catalog-link" href="/it/abbinamento/risultati">Torna ai tuoi abbinamenti</a></header><FavoriteList /></main>;
}
