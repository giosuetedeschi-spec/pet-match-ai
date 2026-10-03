import { PrismaClient } from "@prisma/client";

const createPrismaClient = () => new PrismaClient();

declare global {
  // eslint-disable-next-line no-var
  var petMatchPrisma: ReturnType<typeof createPrismaClient> | undefined;
}

export const prisma = globalThis.petMatchPrisma ?? createPrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalThis.petMatchPrisma = prisma;
}
