import type { Metadata } from "next";
import "./globals.css";
import AutomaticTranslation from "@/components/automatic-translation";

export const metadata: Metadata = {
  title: "PetMatch AI — Trova il tuo compagno",
  description: "Un catalogo di animali in cerca di casa, gestito dai rifugi.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="it">
      <body><AutomaticTranslation />{children}</body>
    </html>
  );
}
