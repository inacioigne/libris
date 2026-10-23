import { NextResponse, type NextRequest } from "next/server";

import {
  exchangeAuthorizationCode,
  getOidcLoginConfiguration,
  matchesOidcState,
  OIDC_COOKIE_PREFIX,
  safeReturnTo,
  SESSION_COOKIE_PREFIX,
  validateIdToken,
} from "@/lib/auth/oidc";

const TRANSACTION_COOKIE_NAMES = ["state", "nonce", "verifier", "return-to"];

function clearTransactionCookies(response: NextResponse) {
  for (const name of TRANSACTION_COOKIE_NAMES) {
    response.cookies.set(`${OIDC_COOKIE_PREFIX}.${name}`, "", {
      httpOnly: true,
      maxAge: 0,
      path: "/oidc",
      sameSite: "lax",
    });
  }
}

function loginFailure(request: NextRequest, reason: string): NextResponse {
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("error", reason);
  const response = NextResponse.redirect(loginUrl, 303);
  clearTransactionCookies(response);
  response.headers.set("Cache-Control", "no-store");
  return response;
}

export async function GET(request: NextRequest) {
  const providerError = request.nextUrl.searchParams.get("error");
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  const expectedState = request.cookies.get(`${OIDC_COOKIE_PREFIX}.state`)?.value;
  const nonce = request.cookies.get(`${OIDC_COOKIE_PREFIX}.nonce`)?.value;
  const verifier = request.cookies.get(`${OIDC_COOKIE_PREFIX}.verifier`)?.value;
  const returnTo = safeReturnTo(
    request.cookies.get(`${OIDC_COOKIE_PREFIX}.return-to`)?.value ?? null,
  );

  if (
    providerError &&
    state &&
    expectedState &&
    matchesOidcState(state, expectedState)
  ) {
    return loginFailure(request, "access_denied");
  }

  if (
    providerError ||
    !code ||
    !state ||
    !expectedState ||
    !nonce ||
    !verifier ||
    !matchesOidcState(state, expectedState)
  ) {
    return loginFailure(request, "invalid_callback");
  }

  try {
    const config = getOidcLoginConfiguration();
    const tokens = await exchangeAuthorizationCode(config, code, verifier);
    await validateIdToken(config, tokens.idToken, nonce);

    const response = NextResponse.redirect(new URL(returnTo, config.origin), 303);
    const cookieOptions = {
      httpOnly: true,
      path: "/",
      sameSite: "lax" as const,
      secure: config.origin.protocol === "https:",
    };

    response.cookies.set(
      `${SESSION_COOKIE_PREFIX}.access-token`,
      tokens.accessToken,
      { ...cookieOptions, maxAge: tokens.expiresIn },
    );
    response.cookies.set(`${SESSION_COOKIE_PREFIX}.id-token`, tokens.idToken, {
      ...cookieOptions,
      maxAge: tokens.expiresIn,
    });
    if (tokens.refreshToken) {
      response.cookies.set(
        `${SESSION_COOKIE_PREFIX}.refresh-token`,
        tokens.refreshToken,
        {
          ...cookieOptions,
          maxAge: tokens.refreshExpiresIn ?? tokens.expiresIn,
        },
      );
    }

    clearTransactionCookies(response);
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch (error) {
    console.error("Falha ao concluir autenticacao OIDC.", error);
    return loginFailure(request, "authentication_failed");
  }
}
