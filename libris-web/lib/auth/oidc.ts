import {
  createHash,
  createPublicKey,
  randomBytes,
  timingSafeEqual,
  verify,
} from "node:crypto";

const DEFAULT_LOCAL_ISSUER = "http://keycloak.localhost:8081/realms/libris";
const DEFAULT_LOCAL_ORIGIN = "http://localhost:3000";

export const OIDC_TRANSACTION_TTL_SECONDS = 10 * 60;
export const OIDC_COOKIE_PREFIX = "libris.oidc";
export const SESSION_COOKIE_PREFIX = "libris.session";

const JWT_CLOCK_SKEW_SECONDS = 30;

export type OidcLoginConfiguration = {
  clientId: string;
  issuer: URL;
  origin: URL;
  scopes: string;
};

export type OidcTokenSet = {
  accessToken: string;
  expiresIn: number;
  idToken: string;
  refreshExpiresIn?: number;
  refreshToken?: string;
};

type JsonObject = Record<string, unknown>;

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

export function matchesOidcState(actual: string, expected: string): boolean {
  const actualBytes = Buffer.from(actual);
  const expectedBytes = Buffer.from(expected);

  return (
    actualBytes.length === expectedBytes.length &&
    timingSafeEqual(actualBytes, expectedBytes)
  );
}

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function positiveInteger(value: unknown): number | undefined {
  return typeof value === "number" && Number.isInteger(value) && value > 0
    ? value
    : undefined;
}

export async function exchangeAuthorizationCode(
  config: OidcLoginConfiguration,
  code: string,
  verifier: string,
): Promise<OidcTokenSet> {
  const tokenEndpoint = new URL(
    `${config.issuer.toString().replace(/\/$/, "")}/protocol/openid-connect/token`,
  );
  const response = await fetch(tokenEndpoint, {
    body: new URLSearchParams({
      client_id: config.clientId,
      code,
      code_verifier: verifier,
      grant_type: "authorization_code",
      redirect_uri: new URL("/oidc/callback", config.origin).toString(),
    }),
    cache: "no-store",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`OIDC token endpoint returned ${response.status}.`);
  }

  const payload: unknown = await response.json();
  if (!isJsonObject(payload)) {
    throw new Error("OIDC token endpoint returned an invalid payload.");
  }

  const accessToken = payload.access_token;
  const idToken = payload.id_token;
  const expiresIn = positiveInteger(payload.expires_in);
  const refreshToken = payload.refresh_token;
  const refreshExpiresIn = positiveInteger(payload.refresh_expires_in);

  if (
    typeof accessToken !== "string" ||
    typeof idToken !== "string" ||
    expiresIn === undefined ||
    (refreshToken !== undefined && typeof refreshToken !== "string")
  ) {
    throw new Error("OIDC token endpoint omitted required token fields.");
  }

  return {
    accessToken,
    expiresIn,
    idToken,
    refreshExpiresIn,
    refreshToken,
  };
}

function decodeJwtPart(value: string): JsonObject {
  let decoded: unknown;

  try {
    decoded = JSON.parse(Buffer.from(value, "base64url").toString("utf8"));
  } catch {
    throw new Error("OIDC provider returned a malformed ID token.");
  }

  if (!isJsonObject(decoded)) {
    throw new Error("OIDC provider returned a malformed ID token.");
  }

  return decoded;
}

function hasAudience(value: unknown, clientId: string): boolean {
  return (
    value === clientId ||
    (Array.isArray(value) && value.some((item) => item === clientId))
  );
}

export async function validateIdToken(
  config: OidcLoginConfiguration,
  idToken: string,
  expectedNonce: string,
): Promise<void> {
  const parts = idToken.split(".");
  if (parts.length !== 3) {
    throw new Error("OIDC provider returned a malformed ID token.");
  }

  const [encodedHeader, encodedPayload, encodedSignature] = parts;
  const header = decodeJwtPart(encodedHeader);
  const claims = decodeJwtPart(encodedPayload);
  if (header.alg !== "RS256" || typeof header.kid !== "string") {
    throw new Error("OIDC provider returned an unsupported ID token.");
  }

  const jwksUrl = new URL(
    `${config.issuer.toString().replace(/\/$/, "")}/protocol/openid-connect/certs`,
  );
  const jwksResponse = await fetch(jwksUrl, { cache: "no-store" });
  if (!jwksResponse.ok) {
    throw new Error(`OIDC JWKS endpoint returned ${jwksResponse.status}.`);
  }

  const jwks: unknown = await jwksResponse.json();
  if (!isJsonObject(jwks) || !Array.isArray(jwks.keys)) {
    throw new Error("OIDC JWKS endpoint returned an invalid payload.");
  }

  const signingKey = jwks.keys.find(
    (key): key is JsonObject & JsonWebKey =>
      isJsonObject(key) && key.kid === header.kid && key.kty === "RSA",
  );
  if (!signingKey) {
    throw new Error("OIDC signing key was not found.");
  }

  const signatureValid = verify(
    "RSA-SHA256",
    Buffer.from(`${encodedHeader}.${encodedPayload}`),
    createPublicKey({ format: "jwk", key: signingKey }),
    Buffer.from(encodedSignature, "base64url"),
  );
  if (!signatureValid) {
    throw new Error("OIDC ID token signature is invalid.");
  }

  const now = Math.floor(Date.now() / 1000);
  const issuer = config.issuer.toString().replace(/\/$/, "");
  if (
    claims.iss !== issuer ||
    !hasAudience(claims.aud, config.clientId) ||
    claims.nonce !== expectedNonce ||
    typeof claims.sub !== "string" ||
    typeof claims.exp !== "number" ||
    claims.exp < now - JWT_CLOCK_SKEW_SECONDS ||
    (typeof claims.nbf === "number" && claims.nbf > now + JWT_CLOCK_SKEW_SECONDS)
  ) {
    throw new Error("OIDC ID token claims are invalid.");
  }

  if (
    Array.isArray(claims.aud) &&
    claims.aud.length > 1 &&
    claims.azp !== config.clientId
  ) {
    throw new Error("OIDC ID token authorized party is invalid.");
  }
}
