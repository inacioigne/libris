import { NextResponse, type NextRequest } from "next/server";

import {
  getOidcLoginConfiguration,
  revokeOidcSession,
} from "@/lib/auth/oidc";
import { destroySession, SESSION_COOKIE_NAME } from "@/lib/auth/session";

export async function POST(request: NextRequest) {
  const sessionId = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const tokens = sessionId ? destroySession(sessionId) : null;

  if (tokens?.refreshToken) {
    try {
      await revokeOidcSession(getOidcLoginConfiguration(), tokens.refreshToken);
    } catch (error) {
      console.error("Falha ao encerrar a sessao no provedor OIDC.", error);
    }
  }

  const response = NextResponse.redirect(new URL("/", request.url), 303);
  response.cookies.set(SESSION_COOKIE_NAME, "", {
    httpOnly: true,
    maxAge: 0,
    path: "/",
    sameSite: "lax",
    secure: request.nextUrl.protocol === "https:",
  });
  for (const name of [
    "libris.session.access-token",
    "libris.session.id-token",
    "libris.session.refresh-token",
  ]) {
    response.cookies.set(name, "", {
      httpOnly: true,
      maxAge: 0,
      path: "/",
      sameSite: "lax",
      secure: request.nextUrl.protocol === "https:",
    });
  }
  response.headers.set("Cache-Control", "no-store");
  return response;
}
