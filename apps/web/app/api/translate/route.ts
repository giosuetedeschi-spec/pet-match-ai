import { NextRequest, NextResponse } from "next/server";

const requests = new Map<string, number[]>();
export async function POST(request: NextRequest) {
  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  const now = Date.now(); const recent = (requests.get(ip) ?? []).filter((time) => now - time < 60_000);
  if (recent.length >= 40) return NextResponse.json({ error: "Limite traduzioni raggiunto." }, { status: 429 });
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });
  const input = body as Record<string, unknown>;
  const texts = input.texts;
  if ((input.target !== "en" && input.target !== "it") || !Array.isArray(texts) || texts.length > 50 || texts.some((text) => typeof text !== "string" || text.length > 5000)) {
    return NextResponse.json({ error: "Testi o lingua non validi." }, { status: 400 });
  }
  requests.set(ip, [...recent, now]);
  const url = (process.env.TRANSLATION_SERVICE_URL ?? "http://translate:5000").replace(/\/$/, "");
  try {
    const response = await fetch(`${url}/translate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: texts, source: "auto", target: input.target, format: "text" }),
      signal: AbortSignal.timeout(10_000), cache: "no-store",
    });
    if (!response.ok) throw new Error("Translation engine unavailable");
    const result = await response.json() as { translatedText?: string | string[] };
    const translated = Array.isArray(result.translatedText) ? result.translatedText : [result.translatedText];
    if (translated.length !== texts.length || translated.some((text) => typeof text !== "string")) throw new Error("Invalid translation response");
    return NextResponse.json({ translations: translated });
  } catch {
    return NextResponse.json({ error: "Traduzione temporaneamente non disponibile." }, { status: 503 });
  }
}
