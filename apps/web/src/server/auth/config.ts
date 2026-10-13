import "server-only";

export interface AuthConfig {
  issuer: string;
  clientId: string;
  origin: string;
  redirectUri: string;
  scopes: string;
  localHttp: boolean;
  databaseUrl: string;
  apiUrl: string;
  keys: ReadonlyMap<string, Buffer>;
  activeKey: string;
  sessionSeconds: number;
}
function required(
  env: Readonly<Record<string, string | undefined>>,
  key: string,
): string {
  const value = env[key];
  if (!value) throw new Error("Authentication configuration unavailable");
  return value;
}
export function trustedUrl(value: string, localHttp: boolean): URL {
  const url = new URL(value);
  if (
    url.username ||
    url.password ||
    url.hash ||
    (url.protocol !== "https:" &&
      !(
        localHttp &&
        url.protocol === "http:" &&
        (url.hostname === "localhost" ||
          url.hostname === "127.0.0.1" ||
          url.hostname.endsWith(".localhost"))
      ))
  ) {
    throw new Error("Untrusted authentication URL");
  }
  return url;
}

export function readConfig(
  env: Readonly<Record<string, string | undefined>> = process.env,
): AuthConfig {
  const localHttp = env.WEB_AUTH_ENV === "local";
  if (!localHttp && env.WEB_AUTH_ENV !== "production")
    throw new Error("Authentication environment required");
  
  const origin = trustedUrl(required(env, "WEB_ORIGIN"), localHttp);
  
  if (origin.pathname !== "/" || origin.search)
    throw new Error("Invalid public origin");
  const issuer = required(env, "WEB_OIDC_ISSUER");
  const issuerUrl = trustedUrl(issuer, localHttp);
  if (issuerUrl.search) throw new Error("Invalid issuer");
  const databaseUrl = required(env, "WEB_SESSION_DATABASE_URL");
  const database = new URL(databaseUrl);
  if (!["postgres:", "postgresql:"].includes(database.protocol))
    throw new Error("PostgreSQL required");
  const api = new URL(required(env, "API_INTERNAL_URL"));
  if (
    api.username ||
    api.password ||
    api.search ||
    api.hash ||
    api.pathname !== "/" ||
    !["http:", "https:"].includes(api.protocol) ||
    (!localHttp && api.protocol !== "https:")
  ) {
    throw new Error("Invalid internal API URL");
  }
  const raw: unknown = JSON.parse(required(env, "WEB_SESSION_KEYS"));
  if (!raw || typeof raw !== "object" || Array.isArray(raw))
    throw new Error("Invalid keyring");
  const keys = new Map<string, Buffer>();
  for (const [id, value] of Object.entries(raw)) {
    if (
      !/^[a-zA-Z0-9_-]{1,32}$/.test(id) ||
      typeof value !== "string" ||
      !/^[A-Za-z0-9+/]{43}=$/.test(value)
    )
      throw new Error("Invalid encryption key");
    const key = Buffer.from(value, "base64");
    if (key.length !== 32) throw new Error("Invalid encryption key");
    keys.set(id, key);
  }
  const activeKey = required(env, "WEB_SESSION_ACTIVE_KEY");
  if (!keys.has(activeKey)) throw new Error("Active key unavailable");
  const sessionSeconds = Number(env.WEB_SESSION_SECONDS ?? "28800");
  if (
    !Number.isInteger(sessionSeconds) ||
    sessionSeconds < 60 ||
    sessionSeconds > 86400
  ) {
    throw new Error("Invalid session lifetime");
  }
  const scopes = env.WEB_OIDC_SCOPES ?? "openid profile";
  if (!scopes.split(" ").includes("openid") || scopes.length > 512)
    throw new Error("OpenID scope required");
  return {
    issuer,
    clientId: required(env, "WEB_OIDC_CLIENT_ID"),
    origin: origin.origin,
    redirectUri: new URL("/oidc/callback", origin).href,
    scopes,
    localHttp,
    databaseUrl,
    apiUrl: api.origin,
    keys,
    activeKey,
    sessionSeconds,
  };
}
