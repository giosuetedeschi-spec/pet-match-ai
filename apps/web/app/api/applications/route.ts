import { AnimalStatus, Prisma, ShelterStatus } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { createRecordId, getRequestSession } from "@/lib/auth";
import { parseApplicationInput } from "@/lib/application-input";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

function responseError(error: string, status: number) {
  return NextResponse.json({ error }, { status, headers: { "Cache-Control": "private, no-store" } });
}

async function adopterSession(request: NextRequest) {
  const session = await getRequestSession(request);
  if (!session) return { error: responseError("Accedi per gestire le candidature.", 401) };
  if (session.user.role !== "adopter") return { error: responseError("Questa funzione è riservata agli account adottante.", 403) };
  return { session };
}

export async function GET(request: NextRequest) {
  const access = await adopterSession(request);
  if ("error" in access) return access.error;
  const applications = await prisma.adoptionApplication.findMany({
    where: { adopterId: access.session.user.id },
    orderBy: { submittedAt: "desc" },
    select: {
      id: true, status: true, motivationalNotes: true, submittedAt: true, updatedAt: true,
      animal: { select: { id: true, name: true, slug: true, species: true, status: true, shelter: { select: { name: true, comune: { select: { name: true } } } } } },
      homeVisit: { select: { evaluatorName: true, scheduledAt: true, outcome: true } },
    },
  });
  return NextResponse.json({ applications }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function POST(request: NextRequest) {
  const access = await adopterSession(request);
  if ("error" in access) return access.error;
  let body: unknown;
  try { body = await request.json(); } catch { return responseError("Richiesta non valida.", 400); }
  const parsed = parseApplicationInput(body);
  if ("error" in parsed) return responseError(parsed.error ?? "Richiesta non valida.", 400);
  const { animalId, motivationalNotes } = parsed.data;

  const animal = await prisma.animal.findFirst({
    where: {
      id: animalId, status: AnimalStatus.available, publishedAt: { not: null }, deletedAt: null,
      shelter: { status: ShelterStatus.active, deletedAt: null },
    },
    select: { id: true },
  });
  if (!animal) return responseError("Questo animale non è più disponibile.", 404);
  try {
    const application = await prisma.adoptionApplication.create({
      data: { id: createRecordId(), adopterId: access.session.user.id, animalId, motivationalNotes },
      select: { id: true, status: true, submittedAt: true, animal: { select: { name: true, slug: true } } },
    });
    return NextResponse.json({ application }, { status: 201, headers: { "Cache-Control": "private, no-store" } });
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002") {
      return responseError("Hai già inviato una candidatura per questo animale.", 409);
    }
    return responseError("Non è stato possibile inviare la candidatura.", 503);
  }
}
