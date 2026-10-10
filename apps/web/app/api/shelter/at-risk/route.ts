import { Prisma } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";
import { createRecordId } from "@/lib/auth";
import { getShelterAccess } from "@/lib/shelter-access";
import { prisma } from "@/lib/prisma";

type Prediction = { ref: string; prediction: { adoption_probability: number; bucket_probabilities: Record<string, number>; top_factors: unknown[]; data_completeness: number; model_version: string; mode: string } };
type StoredPrediction = { animalId: string; modelVersion: string; mode: string; predictedAt: Date; adoptionProbability: number; bucketProbabilities: unknown; topFactors: unknown; dataCompleteness: number; name: string; slug: string; intakeDate: Date; species: string; shelterId: string; shelterName: string };
const mlUrl = () => (process.env.ML_SERVICE_URL ?? "http://ml:8001").replace(/\/$/, "");
const refreshes = new Map<string, number[]>();

export async function GET(request: NextRequest) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  const ids = access.memberships.map((membership) => membership.shelterId);
  if (!ids.length) return NextResponse.json({ predictions: [], modelInfo: null, serviceAvailable: false });
  const predictions = await prisma.$queryRaw<StoredPrediction[]>(Prisma.sql`
    SELECT ap.animal_id AS animalId, ap.model_version AS modelVersion, ap.mode, ap.predicted_at AS predictedAt,
      ap.adoption_probability AS adoptionProbability, ap.bucket_probabilities AS bucketProbabilities,
      ap.top_factors AS topFactors, ap.data_completeness AS dataCompleteness,
      a.name, a.slug, a.intake_date AS intakeDate, a.species, a.shelter_id AS shelterId, s.name AS shelterName
    FROM animal_predictions ap JOIN animals a ON a.id = ap.animal_id JOIN shelters s ON s.id = a.shelter_id
    JOIN (SELECT ap2.animal_id, MAX(ap2.predicted_at) AS latest FROM animal_predictions ap2 GROUP BY ap2.animal_id) latest
      ON latest.animal_id = ap.animal_id AND latest.latest = ap.predicted_at
    WHERE a.shelter_id IN (${Prisma.join(ids)}) AND a.status = 'available' AND a.deleted_at IS NULL
      AND s.status = 'active' AND s.deleted_at IS NULL
    ORDER BY ap.adoption_probability ASC LIMIT 100
  `);
  const [infoResponse, healthResponse] = await Promise.all([
    fetch(`${mlUrl()}/model-info`, { headers: { Authorization: `Bearer ${process.env.ML_SERVICE_TOKEN ?? "local-development-token"}` }, cache: "no-store" }).catch(() => null),
    fetch(`${mlUrl()}/health`, { cache: "no-store" }).catch(() => null),
  ]);
  const modelInfo = infoResponse?.ok ? await infoResponse.json() : null;
  const serviceAvailable = Boolean(healthResponse?.ok);
  predictions.sort((a, b) => a.adoptionProbability - b.adoptionProbability);
  return NextResponse.json({ predictions, modelInfo, serviceAvailable }, { headers: { "Cache-Control": "private, no-store" } });
}

export async function POST(request: NextRequest) {
  const access = await getShelterAccess(request);
  if ("response" in access) return access.response;
  const now = Date.now(); const recent = (refreshes.get(access.userId) ?? []).filter((time) => now - time < 60_000);
  if (recent.length >= 6) return NextResponse.json({ error: "Hai raggiunto il limite temporaneo di aggiornamenti." }, { status: 429 });
  refreshes.set(access.userId, [...recent, now]);
  const ids = access.memberships.map((membership) => membership.shelterId);
  const animals = await prisma.animal.findMany({
    where: { shelterId: { in: ids }, status: "available", deletedAt: null, shelter: { status: "active", deletedAt: null } },
    orderBy: { intakeDate: "asc" }, take: 500,
    select: { id: true, name: true, species: true, sex: true, isSterilized: true, isMixed: true, birthDate: true, intakeDate: true, breedPrimary: true },
  });
  if (!animals.length) return NextResponse.json({ refreshed: 0, message: "Non ci sono animali pubblicati in rifugi attivi." });
  try {
    const response = await fetch(`${mlUrl()}/predict/batch`, {
      method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${process.env.ML_SERVICE_TOKEN ?? "local-development-token"}` }, cache: "no-store",
      body: JSON.stringify({ items: animals.map((animal) => ({ ref: animal.id, features: {
        species: animal.species, sex: animal.sex, is_sterilized: animal.isSterilized, is_mixed: animal.isMixed,
        age_months_at_intake: animal.birthDate ? Math.max(0, (animal.intakeDate.getTime() - animal.birthDate.getTime()) / (30.4375 * 86400000)) : null,
        days_in_care: Math.max(0, (Date.now() - animal.intakeDate.getTime()) / 86400000), has_name: Boolean(animal.name.trim()), breed: animal.breedPrimary,
      } })) }),
      signal: AbortSignal.timeout(2000),
    });
    if (!response.ok) throw new Error("ML service rejected the request");
    const result = await response.json() as { predictions: Prediction[] };
    const byId = new Map(animals.map((animal) => [animal.id, animal]));
    const rows = result.predictions.flatMap(({ ref, prediction }) => {
      if (!byId.has(ref)) return [];
      return [{ id: createRecordId(), animalId: ref, modelVersion: prediction.model_version, mode: prediction.mode, adoptionProbability: prediction.adoption_probability, bucketProbabilities: JSON.stringify(prediction.bucket_probabilities), topFactors: JSON.stringify(prediction.top_factors), dataCompleteness: prediction.data_completeness }];
    });
    if (rows.length) await Promise.all(rows.map((row) => prisma.$executeRaw(Prisma.sql`INSERT INTO animal_predictions (id, animal_id, model_version, mode, predicted_at, adoption_probability, bucket_probabilities, top_factors, data_completeness) VALUES (${row.id}, ${row.animalId}, ${row.modelVersion}, ${row.mode}, NOW(3), ${row.adoptionProbability}, CAST(${row.bucketProbabilities} AS JSON), CAST(${row.topFactors} AS JSON), ${row.dataCompleteness})`)));
    return NextResponse.json({ refreshed: rows.length });
  } catch {
    return NextResponse.json({ error: "Servizio di previsione non disponibile. Riprova più tardi.", code: "dependency_unavailable" }, { status: 503 });
  }
}
