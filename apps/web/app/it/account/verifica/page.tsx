import VerifyForm from "./VerifyForm";

export const metadata = { title: "Verifica email — PetMatch AI" };

export default async function VerifyPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><header className="catalog-heading"><p className="eyebrow">Verifica account</p><h1>Confermiamo la tua email.</h1></header><VerifyForm token={token} /></main>;
}
