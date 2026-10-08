export const MATCH_DIGEST_INTERVAL_MS = 48 * 60 * 60 * 1000;

export function canSendMatchDigest(lastSentAt: Date | null, now = new Date()) {
  return lastSentAt === null || now.getTime() - lastSentAt.getTime() >= MATCH_DIGEST_INTERVAL_MS;
}
