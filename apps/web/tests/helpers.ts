import type { AuthRoute, QuotaPolicy } from "../src/server/auth/quotas";
import { readConfig } from "../src/server/auth/config";
import type { AuthStore, LoginTransaction, Session, SessionHandle } from "../src/server/auth/store";
import { createSign, generateKeyPairSync } from "node:crypto";
import type { boundedFetch } from "../src/server/auth/oidc";

export const config = () => readConfig({
  WEB_AUTH_ENV: "local", WEB_ORIGIN: "http://localhost:3000",
  WEB_OIDC_ISSUER: "http://keycloak.localhost:8081/realms/libris", WEB_OIDC_CLIENT_ID: "libris-web",
  WEB_SESSION_DATABASE_URL: "postgres://test@localhost/test",
  WEB_SESSION_KEYS: JSON.stringify({ test: Buffer.alloc(32, 7).toString("base64") }),
  WEB_SESSION_ACTIVE_KEY: "test", API_INTERNAL_URL: "http://localhost:8000",
});
export class MemoryStore implements AuthStore {
  quotaClock = Date.now;
  quotas = new Map<AuthRoute, { started: number; attempts: number }>();
  async takeQuota(route: AuthRoute, policy: QuotaPolicy) {
    const now = this.quotaClock();
    let row = this.quotas.get(route);
    if (!row || row.started + policy.windowSeconds * 1000 <= now) {
      row = { started: now, attempts: 0 }; this.quotas.set(route, row);
    }
    row.attempts++;
    return { allowed: row.attempts <= policy.limits[route],
      retryAfter: Math.max(1, Math.ceil((row.started + policy.windowSeconds * 1000 - now) / 1000)) };
  }
  transactions = new Map<string, { browser: string; value: LoginTransaction; expiresAt: number }>();
  sessions = new Map<string, Session>();
  locks = new Map<string, Promise<void>>();
  async putTransaction(state: string, browser: string, value: LoginTransaction, expiresAt: number) {
    this.transactions.set(state, { browser, value, expiresAt });
  }
  async consumeTransaction(state: string, browser: string, now: number) {
    const data = this.transactions.get(state);
    if (!data || data.browser !== browser || data.expiresAt <= now) return null;
    this.transactions.delete(state);
    return data.value;
  }
  async createSession(id: string, value: Session) { this.sessions.set(id, value); }
  async withSession<T>(id: string, operation: (handle: SessionHandle) => Promise<T>): Promise<T> {
    const preceding = this.locks.get(id) ?? Promise.resolve();
    let release!: () => void;
    const lock = new Promise<void>((resolve) => { release = resolve; });
    this.locks.set(id, preceding.then(() => lock));
    await preceding;
    try {
      const handle: SessionHandle = {
        value: this.sessions.get(id) ?? null,
        save: async (value) => { this.sessions.set(id, value); handle.value = value; },
        revoke: async () => { this.sessions.delete(id); handle.value = null; },
      };
      return await operation(handle);
    } finally { release(); }
  }
}
const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
export const jwk = { ...pair.publicKey.export({ format: "jwk" }), kid: "test", alg: "RS256", use: "sig" };
export function jwt(claims: Record<string, unknown>, invalidSignature = false): string {
  const encoded = [JSON.stringify({ alg: "RS256", kid: "test" }), JSON.stringify(claims)]
    .map((value) => Buffer.from(value).toString("base64url")).join(".");
  const signature = createSign("RSA-SHA256").update(encoded).sign(pair.privateKey);
  if (invalidSignature) signature[0] ^= 1;
  return encoded + "." + signature.toString("base64url");
}
export function json(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json" } });
}
export function oidcMock(options: {
  claims?: Record<string, unknown>; invalidSignature?: boolean; tokenStatus?: number; refreshStatus?: number;
  discovery?: Record<string, unknown>;
} = {}) {
  const cfg = config();
  let nonce = "";
  let verifier = "";
  let refreshes = 0;
  const requests: { url: string; init: RequestInit }[] = [];
  const transport: typeof boundedFetch = async (url, init = {}) => {
    requests.push({ url: String(url), init });
    if (String(url).endsWith("openid-configuration")) return json({
      issuer: cfg.issuer, authorization_endpoint: cfg.issuer + "/auth", token_endpoint: cfg.issuer + "/token",
      jwks_uri: cfg.issuer + "/jwks", end_session_endpoint: cfg.issuer + "/logout",
      response_types_supported: ["code"], subject_types_supported: ["public"],
      id_token_signing_alg_values_supported: ["RS256"], code_challenge_methods_supported: ["S256"],
      ...options.discovery,
    });
    if (String(url).endsWith("/jwks")) return json({ keys: [jwk] });
    const form = new URLSearchParams(String(init.body));
    const refresh = form.get("grant_type") === "refresh_token";
    if (refresh) refreshes++;
    else {
      verifier = form.get("code_verifier") ?? "";
      if (form.get("redirect_uri") !== cfg.redirectUri) throw new Error("Redirect mismatch");
    }
    const status = refresh ? options.refreshStatus : options.tokenStatus;
    if (status && status !== 200) return json({ error: status === 400 ? "invalid_grant" : "temporarily_unavailable" }, status);
    const time = Math.floor(Date.now() / 1000);
    return json({ access_token: refresh ? "refreshed-access-secret" : "access-secret",
      token_type: "Bearer", expires_in: 120, refresh_token: refresh ? "rotated-refresh-secret" : "refresh-secret",
      refresh_expires_in: 1800,
      id_token: jwt({ iss: cfg.issuer, aud: cfg.clientId, sub: "subject-test", iat: time,
        exp: time + 300, ...(refresh ? {} : { nonce }), ...options.claims }, options.invalidSignature) });
  };
  return { transport, requests, setNonce(value: string) { nonce = value; },
    get verifier() { return verifier; }, get refreshes() { return refreshes; } };
}
