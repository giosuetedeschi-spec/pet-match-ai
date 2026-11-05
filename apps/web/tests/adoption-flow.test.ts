import assert from "node:assert/strict";
import { test } from "node:test";
import { parseApplicationInput, parseHomeVisitInput, resolveHomeVisitDraft } from "../lib/application-input";

test("adoption applications trim valid motivation and reject invalid lengths", () => {
    assert.deepEqual(parseApplicationInput({ animalId: "01ABC", motivationalNotes: "  Vorrei accogliere Luna e posso dedicarle tempo.  " }), {
      data: { animalId: "01ABC", motivationalNotes: "Vorrei accogliere Luna e posso dedicarle tempo." },
    });
    assert.ok("error" in parseApplicationInput({ animalId: "01ABC", motivationalNotes: "Troppo breve" }));
    assert.ok("error" in parseApplicationInput({ animalId: "01ABC", motivationalNotes: "x".repeat(5001) }));
    assert.ok("error" in parseApplicationInput(null));
});

test("home visits require a named evaluator and a future date", () => {
    const now = new Date("2030-01-01T12:00:00.000Z");
    assert.deepEqual(parseHomeVisitInput({ evaluatorName: "  Ada Rossi ", scheduledAt: "2030-01-02T12:00:00.000Z" }, now), {
      data: { evaluatorName: "Ada Rossi", scheduledAt: new Date("2030-01-02T12:00:00.000Z") },
    });
    assert.ok("error" in parseHomeVisitInput({ evaluatorName: "Ada", scheduledAt: "2030-01-01T12:00:00.000Z" }, now));
    assert.ok("error" in parseHomeVisitInput({ evaluatorName: "", scheduledAt: "not-a-date" }, now));
});

test("an unchanged scheduled visit keeps its existing values when saving status", () => {
  assert.deepEqual(resolveHomeVisitDraft(undefined, { evaluatorName: "Ada Rossi", scheduledAt: "2030-01-02T13:00" }), {
    evaluatorName: "Ada Rossi",
    scheduledAt: "2030-01-02T13:00",
  });
  assert.deepEqual(resolveHomeVisitDraft({ evaluatorName: "Luca Bianchi" }, { evaluatorName: "Ada Rossi", scheduledAt: "2030-01-02T13:00" }), {
    evaluatorName: "Luca Bianchi",
    scheduledAt: "2030-01-02T13:00",
  });
});
