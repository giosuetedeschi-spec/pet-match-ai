import { AnimalStatus, BackgroundJobStatus, Prisma, ShelterStatus } from "@prisma/client";
import { createOpaqueToken, createRecordId, hashToken } from "../lib/auth";
import { sendMatchingDigestEmail, type DigestAnimal } from "../lib/mailer";
import { findMatches, MATCH_ENGINE_VERSION, matchingAnimalSelect, type MatchResult } from "../lib/matching";
import { canSendMatchDigest } from "../lib/matching-digest-policy";
import { generateClaudeExplanation, deterministicExplanation } from "../lib/matching-explanations";
import { toMatchProfile } from "../lib/matching-profile";
import { prisma } from "../lib/prisma";

const jobType = "matching.recompute";
const pollIntervalMs = 5_000;
const scheduleIntervalMs = 5 * 60_000;
const recomputeIntervalMs = 5 * 60_000;
const maxDigestSize = 5;

type Profile = NonNullable<Awaited<ReturnType<typeof loadProfiles>>[number]>;

async function loadProfiles() {
  const staleBefore = new Date(Date.now() - recomputeIntervalMs);
  return prisma.adopterProfile.findMany({
    where: {
      isActive: true,
      notifyNewMatches: true,
      completedAt: { not: null },
      OR: [{ lastMatchComputedAt: null }, { lastMatchComputedAt: { lt: staleBefore } }],
      searchComune: { isNot: null },
      user: { is: { status: "active", deletedAt: null, emailVerifiedAt: { not: null } } },
    },
    include: {
      searchComune: { select: { latitude: true, longitude: true } },
      user: { select: { email: true, fullName: true } },
    },
  });
}

async function activeAnimals() {
  return prisma.animal.findMany({
    where: {
      status: AnimalStatus.available,
      publishedAt: { not: null },
      deletedAt: null,
      shelter: { status: ShelterStatus.active, deletedAt: null },
    },
    select: matchingAnimalSelect,
  });
}

function sameMatch(match: MatchResult, previous: { score: number; reasons: Prisma.JsonValue; engineVersion: string } | undefined) {
  return previous?.engineVersion === MATCH_ENGINE_VERSION && previous.score === match.score && JSON.stringify(previous.reasons) === JSON.stringify(match.reasons);
}

async function deliverEmail(notificationId: bigint, profileId: string) {
  const notification = await prisma.notification.findUnique({
    where: { id: notificationId },
    select: { payload: true, user: { select: { email: true, fullName: true } } },
  });
  const profile = await prisma.adopterProfile.findUnique({ where: { id: profileId }, select: { notifyNewMatches: true } });
  if (!notification || !profile?.notifyNewMatches) {
    await prisma.notificationDelivery.updateMany({ where: { notificationId, channel: "email", status: { in: ["pending", "failed"] } }, data: { status: "skipped" } });
    return;
  }
  const animals = payloadToDigestAnimals(notification.payload);
  if (!animals.length) return;
  const token = createOpaqueToken();
  await prisma.matchUnsubscribeToken.create({
    data: { id: createRecordId(), profileId, tokenHash: hashToken(token), expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000) },
  });
  try {
    const sent = await sendMatchingDigestEmail({ email: notification.user.email, name: notification.user.fullName, animals, unsubscribeToken: token });
    await prisma.notificationDelivery.updateMany({
      where: { notificationId, channel: "email", status: { in: ["pending", "failed"] }, attempts: { lt: 3 } },
      data: { status: "sent", attempts: { increment: 1 }, sentAt: new Date(), providerMessageId: sent.messageId ?? null, error: null },
    });
  } catch (error) {
    await prisma.notificationDelivery.updateMany({
      where: { notificationId, channel: "email", status: { in: ["pending", "failed"] }, attempts: { lt: 3 } },
      data: { status: "failed", attempts: { increment: 1 }, error: error instanceof Error ? error.message.slice(0, 255) : "SMTP delivery failed" },
    });
  }
}

async function retryFailedEmailDeliveries() {
  const deliveries = await prisma.notificationDelivery.findMany({
    where: { channel: "email", status: { in: ["pending", "failed"] }, attempts: { lt: 3 } },
    select: {
      notificationId: true,
      notification: {
        select: {
          user: { select: { adopterProfile: { select: { id: true } } } },
        },
      },
    },
  });
  for (const delivery of deliveries) {
    const profileId = delivery.notification.user.adopterProfile?.id;
    if (profileId) await deliverEmail(delivery.notificationId, profileId);
  }
}

async function createOrRefreshMatches(profile: Profile, animals: Awaited<ReturnType<typeof activeAnimals>>) {
  const now = new Date();
  const result = findMatches(toMatchProfile(profile), animals);
  const previous = await prisma.matchResult.findMany({ where: { profileId: profile.id }, select: { animalId: true, score: true, reasons: true, explanationIt: true, explanationEn: true, notifiedAt: true, engineVersion: true } });
  const previousByAnimal = new Map(previous.map((item) => [item.animalId, item]));
  const dueForDigest = canSendMatchDigest(profile.lastMatchDigestAt, now);
  const newMatches = dueForDigest
    ? result.results.filter((match) => match.score >= profile.minNotifyScore && !previousByAnimal.get(match.animal.id)?.notifiedAt).slice(0, maxDigestSize)
    : [];

  const digestTexts = new Map<string, { text: string; cached: string | null }>();
  for (const match of newMatches) {
    const matchProfile = toMatchProfile(profile);
    const generated = await generateClaudeExplanation({ profile: matchProfile, match });
    digestTexts.set(match.animal.id, { text: generated ?? deterministicExplanation(match), cached: generated });
  }

  const notifiedIds = new Set(newMatches.map((match) => match.animal.id));
  const data = result.allResults.map((match) => {
    const old = previousByAnimal.get(match.animal.id);
    const reusable = sameMatch(match, old);
    const digestText = digestTexts.get(match.animal.id);
    return {
      profileId: profile.id,
      animalId: match.animal.id,
      score: match.score,
      breakdown: { dimensions: match.dimensions, distanceKm: match.distanceKm } as Prisma.InputJsonValue,
      reasons: match.reasons as Prisma.InputJsonValue,
      considerations: match.considerations as Prisma.InputJsonValue,
      explanationIt: digestText?.cached ?? (reusable ? old?.explanationIt ?? null : null),
      explanationEn: reusable ? old?.explanationEn ?? null : null,
      engineVersion: MATCH_ENGINE_VERSION,
      computedAt: now,
      notifiedAt: notifiedIds.has(match.animal.id) ? now : old?.notifiedAt ?? null,
    };
  });

  let notificationId: bigint | null = null;
  if (newMatches.length > 0) {
    const payloadAnimals = newMatches.map((match) => ({
      id: match.animal.id,
      name: match.animal.name,
      slug: match.animal.slug,
      species: match.animal.species,
      score: match.score,
      explanation: digestTexts.get(match.animal.id)?.text ?? deterministicExplanation(match),
    }));
    await prisma.$transaction(async (transaction) => {
      await transaction.matchResult.deleteMany({ where: { profileId: profile.id } });
      if (data.length) await transaction.matchResult.createMany({ data });
      const notification = await transaction.notification.create({
        data: {
          userId: profile.userId!,
          type: "match.new",
          titleKey: "notifications.match.new",
          payload: { animals: payloadAnimals } as Prisma.InputJsonValue,
          linkUrl: "/it/notifiche",
        },
        select: { id: true },
      });
      notificationId = notification.id;
      await transaction.notificationDelivery.createMany({
        data: [
          { notificationId: notification.id, channel: "in_app", status: "sent", sentAt: now },
          { notificationId: notification.id, channel: "email", status: "pending" },
        ],
      });
      await transaction.adopterProfile.update({ where: { id: profile.id }, data: { lastMatchDigestAt: now, lastMatchComputedAt: now } });
    });
  } else {
    await prisma.$transaction(async (transaction) => {
      await transaction.matchResult.deleteMany({ where: { profileId: profile.id } });
      if (data.length) await transaction.matchResult.createMany({ data });
      await transaction.adopterProfile.update({ where: { id: profile.id }, data: { lastMatchComputedAt: now } });
    });
  }

  if (notificationId) await deliverEmail(notificationId, profile.id);
}

function payloadToDigestAnimals(payload: Prisma.JsonValue | undefined): DigestAnimal[] {
  if (!payload || typeof payload !== "object" || !("animals" in payload) || !Array.isArray(payload.animals)) return [];
  return payload.animals.filter((animal): animal is DigestAnimal =>
    animal !== null && typeof animal === "object" && "name" in animal && "species" in animal && "slug" in animal && "score" in animal && "explanation" in animal &&
    typeof animal.name === "string" && typeof animal.species === "string" && typeof animal.slug === "string" && typeof animal.score === "number" && typeof animal.explanation === "string",
  );
}

async function processDueProfiles() {
  const [profiles, animals] = await Promise.all([loadProfiles(), activeAnimals()]);
  for (const profile of profiles) {
    try {
      await createOrRefreshMatches(profile, animals);
    } catch (error) {
      console.error("Matching profile refresh failed", profile.id, error instanceof Error ? error.message : "unknown error");
    }
  }
}

async function ensureScheduledJob() {
  const queued = await prisma.backgroundJob.findFirst({ where: { type: jobType, status: BackgroundJobStatus.queued }, select: { id: true } });
  if (!queued) await prisma.backgroundJob.create({ data: { type: jobType, payload: {}, runAt: new Date() } });
}

async function runScheduledJob() {
  await ensureScheduledJob();
  const job = await prisma.backgroundJob.findFirst({ where: { type: jobType, status: BackgroundJobStatus.queued, runAt: { lte: new Date() } }, orderBy: { runAt: "asc" } });
  if (!job) return;
  const claimed = await prisma.backgroundJob.updateMany({ where: { id: job.id, status: BackgroundJobStatus.queued }, data: { status: BackgroundJobStatus.running, lockedAt: new Date(), attempts: { increment: 1 } } });
  if (claimed.count !== 1) return;
  try {
    await processDueProfiles();
    await retryFailedEmailDeliveries();
    await prisma.backgroundJob.update({ where: { id: job.id }, data: { status: BackgroundJobStatus.completed, completedAt: new Date(), lastError: null } });
  } catch (error) {
    await prisma.backgroundJob.update({ where: { id: job.id }, data: { status: BackgroundJobStatus.failed, completedAt: new Date(), lastError: error instanceof Error ? error.message.slice(0, 500) : "Unknown matching job failure" } });
    console.error("Matching digest job failed", error);
  } finally {
    await prisma.backgroundJob.create({ data: { type: jobType, payload: {}, runAt: new Date(Date.now() + scheduleIntervalMs) } });
  }
}

console.info("Matching worker started");
while (true) {
  try {
    await runScheduledJob();
  } catch (error) {
    console.error("Matching worker poll failed", error instanceof Error ? error.message : "unknown error");
  }
  await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
}
