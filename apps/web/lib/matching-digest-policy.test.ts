import assert from "node:assert/strict";
import { test } from "node:test";
import { canSendMatchDigest, MATCH_DIGEST_INTERVAL_MS } from "./matching-digest-policy";

test("digest policy allows at most one send in a rolling 48-hour window", () => {
  const now = new Date("2026-10-08T12:00:00Z");
  assert.equal(canSendMatchDigest(null, now), true);
  assert.equal(canSendMatchDigest(new Date(now.getTime() - MATCH_DIGEST_INTERVAL_MS + 1), now), false);
  assert.equal(canSendMatchDigest(new Date(now.getTime() - MATCH_DIGEST_INTERVAL_MS), now), true);
});
