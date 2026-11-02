import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!body || typeof body !== "object") return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });
  const { message, locale } = body as { message?: unknown; locale?: unknown };
  if (typeof message !== "string" || message.trim().length < 2 || message.length > 1200 || !["it", "en"].includes(String(locale ?? "it"))) {
    return NextResponse.json({ error: "Inserisci una domanda breve in italiano o inglese." }, { status: 400 });
  }
  try {
    const response = await fetch(`${(process.env.CHAT_SERVICE_URL ?? "http://assistant:8002").replace(/\/$/, "")}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${process.env.CHAT_SERVICE_TOKEN ?? "local-chat-token"}` },
      body: JSON.stringify({ message: message.trim(), locale: locale ?? "it" }),
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
    const payload = await response.json();
    if (!response.ok) return NextResponse.json({ error: "Assistente temporaneamente non disponibile." }, { status: 503 });
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json({ error: "Assistente temporaneamente non disponibile." }, { status: 503 });
  }
}
