import { NextResponse } from "next/server";

/** @deprecated Matching now uses the persisted anonymous profile and results endpoints. */
export async function POST() {
  return NextResponse.json(
    { error: "Usa il questionario aggiornato per creare il tuo profilo di compatibilità." },
    { status: 410, headers: { "Cache-Control": "no-store" } },
  );
}
