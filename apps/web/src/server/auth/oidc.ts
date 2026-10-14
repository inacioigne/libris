import "server-only";
import * as oidc from "openid-client";
import type { AuthConfig } from "./config";
import { trustedUrl } from "./config";
import type { LoginTransaction, Session } from "./store";
import { randomId } from "./security";

export class ProviderTemporaryError extends Error {}
export class ProviderRejectedError extends Error {
  constructor(readonly auditOutcome: "denied" | "error" = "denied") { super("Provider rejected"); }
}
export function providerFailureOutcome(error: unknown): "denied" | "error" | "unavailable" {
  let cause: unknown = error;
  for (let depth = 0; depth < 5 && cause instanceof Error; depth++) {
    if (cause instanceof ProviderTemporaryError) return "unavailable";
    if (cause instanceof ProviderRejectedError) return cause.auditOutcome;
    if (cause instanceof oidc.ResponseBodyError || cause instanceof oidc.AuthorizationResponseError) return "denied";
    if (cause instanceof oidc.ClientError) {
      if (cause.code === "OAUTH_TIMEOUT" || cause.code === "OAUTH_ABORT") return "error";
      // Continue into a nested transport failure before classifying a validation error.
      if (!(cause.cause instanceof Error)) return "denied";
    }
    if (cause instanceof TypeError || cause.name === "TimeoutError" || cause.name === "AbortError") return "error";
    cause = cause.cause;
  }
  return error instanceof oidc.ClientError ? "denied" : "error";
}
export interface OidcProvider {
  authorize(state: string, nonce: string, verifier: string): Promise<URL>;
  exchange(url: URL, state: string, transaction: LoginTransaction, now: number): Promise<Session>;
  refresh(session: Session, now: number): Promise<Session>;
  logout(returnTo: string): Promise<URL | null>;
}
export async function boundedFetch(url: string | URL, init: RequestInit = {}, limit = 1_048_576): Promise<Response> {
  const timeout = AbortSignal.timeout(5000);
  const signal = init.signal ? AbortSignal.any([init.signal, timeout]) : timeout;
  const response = await fetch(url, { ...init, redirect: "error", cache: "no-store", signal });
  const reader = response.body?.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  if (reader) {
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > limit) throw new Error("Provider response limit exceeded");
        chunks.push(value);
      }
    } finally { await reader.cancel(); }
  }
  return new Response(Buffer.concat(chunks), { status: response.status, statusText: response.statusText,
    headers: response.headers });
}
type TokenResponse = Awaited<ReturnType<typeof oidc.authorizationCodeGrant>>;
function tokenSession(tokens: TokenResponse, config: AuthConfig, now: number, previous?: Session): Session {
  if (tokens.token_type.toLowerCase() !== "bearer" || !tokens.access_token ||
      tokens.access_token.length > 16384 || !Number.isFinite(tokens.expires_in) ||
      !tokens.expires_in || tokens.expires_in <= 0 ||
      (tokens.refresh_token && tokens.refresh_token.length > 16384)) throw new ProviderRejectedError();
  const subject = tokens.claims()?.sub ?? previous?.subject;
  if (!subject || (previous && subject !== previous.subject)) throw new ProviderRejectedError();
  const refreshExpires = tokens.refresh_expires_in;
  if (refreshExpires !== undefined && (typeof refreshExpires !== "number" ||
      !Number.isFinite(refreshExpires) || refreshExpires < 0)) throw new ProviderRejectedError();
  return {
    accessToken: tokens.access_token, accessExpiresAt: now + tokens.expires_in * 1000,
    refreshToken: tokens.refresh_token ?? previous?.refreshToken,
    // Keycloak supplies refresh_expires_in. Zero denotes provider-controlled/offline
    // lifetime, still capped by the absolute application session expiry.
    refreshExpiresAt: typeof refreshExpires === "number" && refreshExpires > 0 ?
      now + refreshExpires * 1000 : previous?.refreshExpiresAt,
    subject, csrf: previous?.csrf ?? randomId(), expiresAt: previous?.expiresAt ?? now + config.sessionSeconds * 1000,
  };
}
export class OpenIdProvider implements OidcProvider {
  private configuration?: Promise<oidc.Configuration>;
  private retryAfter = 0;
  constructor(private readonly config: AuthConfig, private readonly transport: typeof boundedFetch = boundedFetch,
    private readonly clock: () => number = Date.now) {}
  private async load(): Promise<oidc.Configuration> {
    // Only configured issuer-origin endpoints can be contacted, including discovery and JWKS.
    const issuerOrigin = new URL(this.config.issuer).origin;
    const transport: oidc.CustomFetch = async (url, init) => {
      const trusted = trustedUrl(String(url), this.config.localHttp);
      if (trusted.origin !== issuerOrigin) throw new ProviderRejectedError();
      const body = init.body instanceof Uint8Array ? new Uint8Array(init.body).buffer : init.body;
      const response = await this.transport(trusted, { ...init, body });
      if (response.status === 429 || response.status >= 500) throw new ProviderTemporaryError();
      return response;
    };
    const config = await oidc.discovery(new URL(this.config.issuer), this.config.clientId,
      { id_token_signed_response_alg: "RS256" }, oidc.None(), {
        timeout: 5, [oidc.customFetch]: transport,
        execute: this.config.localHttp ? [oidc.allowInsecureRequests, oidc.enableNonRepudiationChecks] :
          [oidc.enableNonRepudiationChecks],
      });
    const metadata = config.serverMetadata();
    if (metadata.issuer !== this.config.issuer ||
        !metadata.code_challenge_methods_supported?.includes("S256")) throw new ProviderRejectedError();
    for (const endpoint of [metadata.authorization_endpoint, metadata.token_endpoint, metadata.jwks_uri]) {
      if (!endpoint || trustedUrl(endpoint, this.config.localHttp).origin !== issuerOrigin) throw new ProviderRejectedError();
    }
    if (metadata.end_session_endpoint &&
        trustedUrl(metadata.end_session_endpoint, this.config.localHttp).origin !== issuerOrigin) throw new ProviderRejectedError();
    return config;
  }
  private getConfiguration(): Promise<oidc.Configuration> {
    if (!this.configuration && this.clock() < this.retryAfter) return Promise.reject(new ProviderTemporaryError());
    this.configuration ??= this.load().catch((error: unknown) => {
      this.configuration = undefined;
      this.retryAfter = this.clock() + 10000;
      throw error;
    });
    return this.configuration;
  }
  async authorize(state: string, nonce: string, verifier: string): Promise<URL> {
    return oidc.buildAuthorizationUrl(await this.getConfiguration(), {
      redirect_uri: this.config.redirectUri, scope: this.config.scopes, state, nonce,
      code_challenge: await oidc.calculatePKCECodeChallenge(verifier), code_challenge_method: "S256",
      response_type: "code", response_mode: "query",
    });
  }
  async exchange(url: URL, state: string, transaction: LoginTransaction, now: number): Promise<Session> {
    const tokens = await oidc.authorizationCodeGrant(await this.getConfiguration(), url, {
      expectedState: state, expectedNonce: transaction.nonce, pkceCodeVerifier: transaction.verifier,
      idTokenExpected: true,
    });
    return tokenSession(tokens, this.config, now);
  }
  async refresh(session: Session, now: number): Promise<Session> {
    if (!session.refreshToken) throw new ProviderRejectedError();
    try {
      return tokenSession(await oidc.refreshTokenGrant(await this.getConfiguration(), session.refreshToken),
        this.config, now, session);
    } catch (error) {
      // A definite 5xx/429 response is retryable. Timeouts/network errors can occur
      // after rotation: discard the session rather than replay an uncertain refresh.
      let cause: unknown = error;
      for (let depth = 0; depth < 5 && cause instanceof Error; depth++) {
        if (cause instanceof ProviderTemporaryError) throw cause;
        cause = cause.cause;
      }
      throw new ProviderRejectedError(providerFailureOutcome(error) === "denied" ? "denied" : "error");
    }
  }
  async logout(returnTo: string): Promise<URL | null> {
    const config = await this.getConfiguration();
    if (!config.serverMetadata().end_session_endpoint) return null;
    // client_id avoids disclosing an ID token in a browser URL. Provider may ask
    // the user to confirm; local revocation has already committed.
    return oidc.buildEndSessionUrl(config, { client_id: this.config.clientId,
      post_logout_redirect_uri: new URL(returnTo, this.config.origin).href });
  }
}
