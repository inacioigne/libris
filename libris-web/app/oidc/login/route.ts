import { NextResponse, type NextRequest } from "next/server";

import {
  buildAuthorizationUrl,
  createOidcTransaction,
  getOidcLoginConfiguration,
  OIDC_COOKIE_PREFIX,
  OIDC_TRANSACTION_TTL_SECONDS,
  safeReturnTo,
} from "@/lib/auth/oidc";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    return startLogin(formData.get("returnTo"));
  } catch (error) {
    return loginUnavailable(error);
  }
}

export async function GET(request: NextRequest) {
  try {
    return startLogin(request.nextUrl.searchParams.get("returnTo"));
  } catch (error) {
    return loginUnavailable(error);
  }
}

function startLogin(returnToValue: FormDataEntryValue | null) {
  const config = getOidcLoginConfiguration();
  const returnTo = safeReturnTo(returnToValue);
  const transaction = createOidcTransaction();
  const authorizationUrl = buildAuthorizationUrl(config, transaction);
  const response = NextResponse.redirect(authorizationUrl, 303);
  const secure = config.origin.protocol === "https:";
  const cookieOptions = {
    httpOnly: true,
    maxAge: OIDC_TRANSACTION_TTL_SECONDS,
    path: "/oidc",
    sameSite: "lax" as const,
    secure,
  };

  response.cookies.set(
    `${OIDC_COOKIE_PREFIX}.state`,
    transaction.state,
    cookieOptions,
  );
  response.cookies.set(
    `${OIDC_COOKIE_PREFIX}.nonce`,
    transaction.nonce,
    cookieOptions,
  );
  response.cookies.set(
    `${OIDC_COOKIE_PREFIX}.verifier`,
    transaction.verifier,
    cookieOptions,
  );
  response.cookies.set(
    `${OIDC_COOKIE_PREFIX}.return-to`,
    returnTo,
    cookieOptions,
  );
  response.headers.set("Cache-Control", "no-store");

  return response;
}

function loginUnavailable(error: unknown) {
  console.error("Falha ao iniciar autenticacao OIDC.", error);

  return NextResponse.json(
    { detail: "Nao foi possivel iniciar a autenticacao." },
    {
      status: 503,
      headers: { "Cache-Control": "no-store" },
    },
  );
}
