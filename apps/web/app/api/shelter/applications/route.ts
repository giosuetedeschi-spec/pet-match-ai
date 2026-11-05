import { AdoptionApplicationStatus, Prisma } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { createRecordId } from "@/lib/auth";
import { parseHomeVisitInput } from "@/lib/application-input";
import { getShelterAccess } from "@/lib/shelter-access";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";
const shelterStatuses = new Set(["in_review", "home_visit", "approved", "rejected"]);

function errorResponse(error: string, status: number) {
  return NextResponse.json({ error }, { status, headers: { "Cache-Control": "private, no-store" } });
}

export async function GET(request: NextRequest) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  const shelterIds = access.memberships.map(({ shelterId }) => shelterId);
  const applications = await prisma.adoptionApplication.findMany({
    where: { animal: { shelterId: { in: shelterIds }, deletedAt: null } },
    orderBy: { submittedAt: "desc" },
    select: {
      id: true, status: true, motivationalNotes: true, shelterNotes: true, submittedAt: true,
      adopter: { select: { fullName: true, email: true, phone: true } },
      animal: { select: { id: true, name: true, slug: true, shelterId: true } },
      homeVisit: { select: { id: true, evaluatorName: true, scheduledAt: true, outcome: true, reportNotes: true } },
    },
  });
  return NextResponse.json({ applications }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function PATCH(request: NextRequest) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  let body: unknown;
  try { body = await request.json(); } catch { return errorResponse("Richiesta non valida.", 400); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return errorResponse("Richiesta non valida.", 400);
  const input = body as Record<string, unknown>;
  const applicationId = typeof input.applicationId === "string" ? input.applicationId : "";
  const status = typeof input.status === "string" ? input.status : "";
  if (!applicationId || !shelterStatuses.has(status)) return errorResponse("Candidatura o stato non valido.", 400);
  const visit = status === "home_visit" ? parseHomeVisitInput(input.visit) : null;
  if (visit && "error" in visit) return errorResponse(visit.error ?? "Data visita non valida.", 400);

  const shelterIds = access.memberships.map(({ shelterId }) => shelterId);
  const application = await prisma.adoptionApplication.findFirst({
    where: { id: applicationId, animal: { shelterId: { in: shelterIds }, deletedAt: null } },
    select: { id: true, homeVisit: { select: { id: true } } },
  });
  if (!application) return errorResponse("Candidatura non trovata.", 404);

  try {
    const updated = await prisma.$transaction(async (tx) => {
      if (visit && "data" in visit) {
        await tx.homeVisit.upsert({
          where: { applicationId },
          create: { id: createRecordId(), applicationId, ...visit.data },
          update: { ...visit.data, outcome: "pending" },
        });
      }
      return tx.adoptionApplication.update({
        where: { id: applicationId },
        data: { status: status as AdoptionApplicationStatus },
        select: { id: true, status: true, homeVisit: { select: { evaluatorName: true, scheduledAt: true, outcome: true } } },
      });
    });
    return NextResponse.json({ application: updated }, { headers: { "Cache-Control": "private, no-store" } });
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError) return errorResponse("Non è stato possibile aggiornare la candidatura.", 503);
    return errorResponse("Non è stato possibile aggiornare la candidatura.", 503);
  }
}
