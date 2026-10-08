import { NextRequest, NextResponse } from "next/server";
import { getUserSession, sessionCookieName } from "@/lib/auth";

export async function GET(request: NextRequest) {
  const session = await getUserSession(request.cookies.get(sessionCookieName)?.value);
  return NextResponse.json({
    authenticated: Boolean(session),
    user: session ? { email: session.user.email, fullName: session.user.fullName, locale: session.user.locale } : null,
  }, { headers: { "Cache-Control": "private, no-store" } });
}
