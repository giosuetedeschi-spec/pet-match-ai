import { NextResponse } from "next/server";
import { AnimalSpecies, AnimalStatus, ShelterStatus } from "@prisma/client";
import { prisma } from "@/lib/prisma";

export const runtime = "nodejs";
const requestsByIp = new Map<string, number[]>();
const CHAT_LIMIT = 10;
const WINDOW_MS = 60_000;

function isRateLimited(request: Request) {
  const now = Date.now();
  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  const recent = (requestsByIp.get(ip) ?? []).filter((timestamp) => now - timestamp < WINDOW_MS);
  if (recent.length >= CHAT_LIMIT) {
    requestsByIp.set(ip, recent);
    return true;
  }
  requestsByIp.set(ip, [...recent, now]);
  if (requestsByIp.size > 5000) {
    for (const [key, timestamps] of requestsByIp) {
      if (!timestamps.some((timestamp) => now - timestamp < WINDOW_MS)) requestsByIp.delete(key);
    }
  }
  return false;
}

function asksForAnimals(message: string) {
  return /(adott|cerc\w*.{0,24}(cane|gatto|animal)|looking for (a )?(dog|cat|pet)|find me (a )?(dog|cat|pet)|available animals|animali disponibili|schede disponibili)/i.test(message);
}

export async function POST(request: Request) {
  if (isRateLimited(request)) return NextResponse.json({ error: "Hai raggiunto il limite temporaneo. Riprova tra un minuto." }, { status: 429, headers: { "Retry-After": "60" } });
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 }); }
  if (!body || typeof body !== "object") return NextResponse.json({ error: "Richiesta non valida." }, { status: 400 });
  const { message, locale, history } = body as { message?: unknown; locale?: unknown; history?: unknown };
  if (typeof message !== "string" || message.trim().length < 2 || message.length > 1200 || !["it", "en"].includes(String(locale ?? "it"))) {
    return NextResponse.json({ error: "Inserisci una domanda breve in italiano o inglese." }, { status: 400 });
  }
  try {
    const catalogAnimals = [];
    if (asksForAnimals(message)) {
      const text = message.toLowerCase();
      const species = text.includes("gatt") || text.includes("cat") ? AnimalSpecies.cat : text.includes("can") || text.includes("dog") ? AnimalSpecies.dog : undefined;
      const animals = await prisma.animal.findMany({
        where: {
          status: AnimalStatus.available,
          publishedAt: { not: null },
          deletedAt: null,
          shelter: { status: ShelterStatus.active, deletedAt: null },
          ...(species ? { species } : {}),
        },
        orderBy: [{ publishedAt: "desc" }, { name: "asc" }],
        take: 6,
        select: { name: true, slug: true, species: true, breedPrimary: true, headlineIt: true, shelter: { select: { name: true, comune: { select: { name: true } } } } },
      });
      catalogAnimals.push(...animals.map((animal) => ({
        name: animal.name, slug: animal.slug, species: animal.species, breed: animal.breedPrimary ?? "",
        shelter: animal.shelter.name, city: animal.shelter.comune.name, description: animal.headlineIt ?? "",
      })));
    }
    const safeHistory = Array.isArray(history) ? history.slice(-8).flatMap((item) => {
      if (!item || typeof item !== "object") return [];
      const entry = item as { role?: unknown; content?: unknown };
      return (entry.role === "user" || entry.role === "assistant") && typeof entry.content === "string"
        ? [{ role: entry.role, content: entry.content.slice(0, 1200) }]
        : [];
    }) : [];
    const response = await fetch(`${(process.env.CHAT_SERVICE_URL ?? "http://assistant:8002").replace(/\/$/, "")}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${process.env.CHAT_SERVICE_TOKEN ?? "local-chat-token"}` },
      body: JSON.stringify({ message: message.trim(), locale: locale ?? "it", history: safeHistory, catalog_animals: catalogAnimals }),
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
