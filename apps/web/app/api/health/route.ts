import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    await prisma.comune.count();
    return Response.json({ status: "ok", database: "connected" });
  } catch {
    return Response.json(
      { status: "error", database: "unavailable" },
      { status: 503 },
    );
  }
}
