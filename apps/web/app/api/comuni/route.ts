import { prisma } from "@/lib/prisma";

export async function GET(request: Request) {
  const query = new URL(request.url).searchParams.get("q")?.trim().slice(0, 80) ?? "";
  if (query.length < 2) return Response.json([]);

  try {
    const comuni = await prisma.comune.findMany({
      where: { name: { contains: query } },
      select: { id: true, name: true, provinceCode: true, region: true },
      orderBy: [{ name: "asc" }, { id: "asc" }],
      take: 20,
    });
    return Response.json(comuni, { headers: { "Cache-Control": "private, max-age=60" } });
  } catch {
    return Response.json({ error: "Elenco comuni non disponibile." }, { status: 503 });
  }
}
