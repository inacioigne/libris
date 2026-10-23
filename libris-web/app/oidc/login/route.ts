import { NextResponse, type NextRequest } from "next/server";

import {
  buildAuthorizationUrl,
  createOidcTransaction,
  getOidcLoginConfiguration,
  OIDC_TRANSACTION_TTL_SECONDS,
  safeReturnTo,
} from "@/lib/auth/oidc";

const COOKIE_PREFIX = "libris.oidc";

export async function POST(request: NextRequest) {
  try {
    const config = getOidcLoginConfiguration();
    const formData = await request.formData();
    const returnTo = safeReturnTo(formData.get("returnTo"));
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

    response.cookies.set(`${COOKIE_PREFIX}.state`, transaction.state, cookieOptions);
    response.cookies.set(`${COOKIE_PREFIX}.nonce`, transaction.nonce, cookieOptions);
    response.cookies.set(`${COOKIE_PREFIX}.verifier`, transaction.verifier, cookieOptions);
    response.cookies.set(`${COOKIE_PREFIX}.return-to`, returnTo, cookieOptions);
    response.headers.set("Cache-Control", "no-store");

    return response;
  } catch (error) {
    console.error("Falha ao iniciar autenticacao OIDC.", error);

    return NextResponse.json(
      { detail: "Nao foi possivel iniciar a autenticacao." },
      {
        status: 503,
        headers: { "Cache-Control": "no-store" },
      },
    );
  }
}
