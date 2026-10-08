import UnsubscribeForm from "./UnsubscribeForm";

export const metadata = { title: "Disiscrizione digest — PetMatch AI" };

export default async function UnsubscribePage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><header className="catalog-heading"><p className="eyebrow">Preferenze email</p><h1>Disattiva i digest.</h1></header><UnsubscribeForm token={token} /></main>;
}
