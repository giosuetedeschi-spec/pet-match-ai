import AssistantChat from "./AssistantChat";

export const metadata = { title: "Assistente — PetMatch AI", description: "Assistente informativo con fonti verificate." };

export default function AssistantPage() {
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><AssistantChat /></main>;
}
