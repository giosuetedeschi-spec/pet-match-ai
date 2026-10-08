import MatchResults from "./MatchResults";

export const metadata = {
  title: "I tuoi abbinamenti — PetMatch AI",
  description: "Scopri gli animali compatibili con la tua quotidianità.",
};

export default function ResultsPage() {
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><MatchResults /></main>;
}
