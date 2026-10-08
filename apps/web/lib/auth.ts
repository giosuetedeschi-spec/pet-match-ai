import { createHash, randomBytes } from "node:crypto";
import { cookies } from "next/headers";
import { prisma } from "@/lib/prisma";

export const sessionCookieName = "petmatch-session";
export const adopterCookieName = "petmatch-adopter";
const sessionDays = 30;

type BunPassword = {
  hash(password: string, options: { algorithm: "argon2id" }): Promise<string>;
  verify(password: string, hash: string): Promise<boolean>;
};

function bunPassword() {
  const runtime = (globalThis as typeof globalThis & { Bun?: { password: BunPassword } }).Bun;
  if (!runtime?.password) throw new Error("PetMatch account actions require the Bun runtime.");
  return runtime.password;
}

export const hashToken = (token: string) => createHash("sha256").update(token).digest("hex");
export const createOpaqueToken = () => randomBytes(32).toString("hex");
export const createRecordId = () => randomBytes(13).toString("hex");
export const hashPassword = (password: string) => bunPassword().hash(password, { algorithm: "argon2id" });
export const verifyPassword = (password: string, hash: string) => bunPassword().verify(password, hash);

export async function createSession(userId: string) {
  const token = createOpaqueToken();
  const expiresAt = new Date(Date.now() + sessionDays * 24 * 60 * 60 * 1000);
  const session = await prisma.session.create({
    data: { id: createRecordId(), userId, tokenHash: hashToken(token), expiresAt },
  });
  return { token, expiresAt: session.expiresAt };
}

export async function getUserSession(token: string | undefined) {
  if (!token) return null;
  return prisma.session.findFirst({
    where: {
      tokenHash: hashToken(token),
      expiresAt: { gt: new Date() },
      user: { is: { status: "active", deletedAt: null, emailVerifiedAt: { not: null } } },
    },
    select: {
      id: true,
      expiresAt: true,
      user: { select: { id: true, email: true, fullName: true, locale: true, role: true } },
    },
  });
}

export async function getRequestSession(request: Request) {
  const cookieHeader = request.headers.get("cookie") ?? "";
  const token = cookieHeader.match(/(?:^|;\s*)petmatch-session=([^;]+)/)?.[1];
  return getUserSession(token ? decodeURIComponent(token) : undefined);
}

export async function getCurrentUserSession() {
  const cookieStore = await cookies();
  return getUserSession(cookieStore.get(sessionCookieName)?.value);
}

export function attachSessionCookie(response: Response, token: string, expiresAt: Date) {
  const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
  response.headers.append(
    "Set-Cookie",
    `${sessionCookieName}=${encodeURIComponent(token)}; Path=/; HttpOnly; SameSite=Lax; Expires=${expiresAt.toUTCString()}${secure}`,
  );
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export function clearSessionCookie(response: Response) {
  response.headers.append("Set-Cookie", `${sessionCookieName}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`);
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export function clearAdopterCookie(response: Response) {
  response.headers.append("Set-Cookie", `${adopterCookieName}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`);
  return response;
}
