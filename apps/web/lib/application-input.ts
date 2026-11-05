export function parseApplicationInput(value: unknown) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return { error: "Richiesta non valida." } as const;
  const input = value as Record<string, unknown>;
  const animalId = typeof input.animalId === "string" ? input.animalId.trim() : "";
  const motivationalNotes = typeof input.motivationalNotes === "string" ? input.motivationalNotes.trim() : "";
  if (!animalId || animalId.length > 26 || motivationalNotes.length < 20 || motivationalNotes.length > 5000) {
    return { error: "Indica l'animale e scrivi una motivazione da 20 a 5.000 caratteri." } as const;
  }
  return { data: { animalId, motivationalNotes } } as const;
}

export function parseHomeVisitInput(value: unknown, now = new Date()) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return { error: "Indica operatore e data futura." } as const;
  const input = value as Record<string, unknown>;
  const evaluatorName = typeof input.evaluatorName === "string" ? input.evaluatorName.trim() : "";
  const scheduledAt = typeof input.scheduledAt === "string" ? new Date(input.scheduledAt) : null;
  if (!evaluatorName || evaluatorName.length > 150 || !scheduledAt || Number.isNaN(scheduledAt.getTime()) || scheduledAt <= now) {
    return { error: "Per programmare la visita indica un operatore e una data futura." } as const;
  }
  return { data: { evaluatorName, scheduledAt } } as const;
}

export function resolveHomeVisitDraft(edited: { evaluatorName?: string; scheduledAt?: string } | undefined, existing: { evaluatorName: string; scheduledAt: string } | null) {
  return {
    evaluatorName: edited?.evaluatorName ?? existing?.evaluatorName ?? "",
    scheduledAt: edited?.scheduledAt ?? existing?.scheduledAt ?? "",
  };
}
