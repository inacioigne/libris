import { createHash, randomBytes } from "node:crypto";

const DEFAULT_LOCAL_ISSUER = "http://keycloak.localhost:8081/realms/libris";
const DEFAULT_LOCAL_ORIGIN = "http://localhost:3000";

export const OIDC_TRANSACTION_TTL_SECONDS = 10 * 60;

export type OidcLoginConfiguration = {
  clientId: string;
  issuer: URL;
  origin: URL;
  scopes: string;
};

function requiredInProduction(name: string, localDefault: string): string {
  const value = process.env[name]?.trim();

  if (value) {
    return value;
  }

  if (process.env.NODE_ENV !== "production") {
    return localDefault;
  }

  throw new Error(`A variavel de ambiente ${name} e obrigatoria.`);
}

function parseHttpUrl(name: string, value: string): URL {
  const url = new URL(value);

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error(`${name} deve usar HTTP ou HTTPS.`);
  }

  return url;
}

export function getOidcLoginConfiguration(): OidcLoginConfiguration {
  const issuer = parseHttpUrl(
    "WEB_OIDC_ISSUER",
    requiredInProduction("WEB_OIDC_ISSUER", DEFAULT_LOCAL_ISSUER),
  );
  const origin = parseHttpUrl(
    "WEB_ORIGIN",
    requiredInProduction("WEB_ORIGIN", DEFAULT_LOCAL_ORIGIN),
  );
  const configuredScopes = process.env.WEB_OIDC_SCOPES?.trim() || "openid profile";
  const scopes = new Set(configuredScopes.split(/\s+/).filter(Boolean));
  scopes.add("openid");

  issuer.pathname = issuer.pathname.replace(/\/$/, "");
  origin.pathname = "";
  origin.search = "";
  origin.hash = "";

  return {
    clientId: process.env.WEB_OIDC_CLIENT_ID?.trim() || "libris-web",
    issuer,
    origin,
    scopes: [...scopes].join(" "),
  };
}

export function createOidcTransaction() {
  const state = randomBytes(32).toString("base64url");
  const nonce = randomBytes(32).toString("base64url");
  const verifier = randomBytes(64).toString("base64url");
  const challenge = createHash("sha256").update(verifier).digest("base64url");

  return { challenge, nonce, state, verifier };
}

export function safeReturnTo(value: FormDataEntryValue | null): string {
  if (typeof value !== "string") {
    return "/admin";
  }

  const candidate = value.trim();

  if (!candidate.startsWith("/") || candidate.startsWith("//")) {
    return "/admin";
  }

  try {
    const parsed = new URL(candidate, "http://libris.invalid");
    return parsed.origin === "http://libris.invalid"
      ? `${parsed.pathname}${parsed.search}${parsed.hash}`
      : "/admin";
  } catch {
    return "/admin";
  }
}

export function buildAuthorizationUrl(
  config: OidcLoginConfiguration,
  transaction: ReturnType<typeof createOidcTransaction>,
): URL {
  const authorizationUrl = new URL(
    `${config.issuer.toString().replace(/\/$/, "")}/protocol/openid-connect/auth`,
  );

  authorizationUrl.search = new URLSearchParams({
    client_id: config.clientId,
    code_challenge: transaction.challenge,
    code_challenge_method: "S256",
    nonce: transaction.nonce,
    redirect_uri: new URL("/oidc/callback", config.origin).toString(),
    response_type: "code",
    scope: config.scopes,
    state: transaction.state,
  }).toString();

  return authorizationUrl;
}
