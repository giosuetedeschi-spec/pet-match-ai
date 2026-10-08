import { NextRequest, NextResponse } from "next/server";
import { clearSessionCookie, hashToken, sessionCookieName } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  const token = request.cookies.get(sessionCookieName)?.value;
  if (token) await prisma.session.deleteMany({ where: { tokenHash: hashToken(token) } });
  return clearSessionCookie(NextResponse.json({ authenticated: false }));
}
