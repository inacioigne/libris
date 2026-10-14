import "server-only";
import { actorIdentifier, currentCorrelation, SecurityAudit, type SecurityEvent, type Reason, type Outcome, withCorrelation } from "../security-audit";
import type { AuthConfig } from "./config";
import {
  boundedFetch,
  ProviderTemporaryError,
  providerFailureOutcome,
  type OidcProvider,
} from "./oidc";
import { boundedCallback, PayloadTooLarge, randomId, returnPath, validId } from "./security";
import type { AuthStore, SessionHandle } from "./store";

export interface Identity {
  actor_id: string;
  roles: string[];
  permissions: string[];
}
export type IdentityResult =
  | { status: "authenticated"; identity: Identity; csrf: string }
  | {
      status: "anonymous" | "expired" | "forbidden" | "unavailable";
      csrf?: string;
    };
export class CallbackRejected extends Error {
  constructor(readonly returnTo = "/pt", readonly auditReason: Reason = "callback_rejected", readonly auditOutcome: Outcome = "denied") {
    super("Callback rejected");
  }
}
class LogoutRejected extends Error {}

export class LoginCancelled extends Error {
  constructor(readonly returnTo: string) {
    super("Login cancelled");
  }
}
function identityResponse(value: unknown): Identity {
  if (!value || typeof value !== "object")
    throw new Error("Invalid API response");
  const data = value as Record<string, unknown>;
  if (
    Object.keys(data).sort().join(",") !== "actor_id,permissions,roles" ||
    typeof data.actor_id !== "string" ||
    !Array.isArray(data.roles) ||
    !Array.isArray(data.permissions) ||
    !data.roles.every((role: unknown) => typeof role === "string") ||
    !data.permissions.every(
      (permission: unknown) => typeof permission === "string",
    )
  )
    throw new Error("Invalid API identity");
  return {
    actor_id: data.actor_id,
    roles: data.roles,
    permissions: data.permissions,
  };
}
export class AuthService {
  constructor(
    readonly config: AuthConfig,
    readonly store: AuthStore,
    readonly provider: OidcProvider,
    private readonly clock: () => number = Date.now,
    private readonly apiFetch: typeof boundedFetch = boundedFetch,
    readonly audit: SecurityAudit = new SecurityAudit(),
  ) {}

  async start(destination: string): Promise<{ url: URL; state: string; browser: string }> {
    return withCorrelation(currentCorrelation(), () => this.startCorrelated(destination));
  }
  private async startCorrelated(destination: string): Promise<{ url: URL; state: string; browser: string }> {
    const returnTo = returnPath(destination);
    const state = randomId(),
      browser = randomId(),
      verifier = randomId(),
      nonce = randomId();
    const url = await this.provider.authorize(state, nonce, verifier);
    await this.store.putTransaction(
      state,
      browser,
      { verifier, nonce, returnTo },
      this.clock() + 300000,
    );
    this.audit.record("authentication.started", "login", "success");
    return { url, state, browser };
  }
  
  async callback(url: URL, browser: string | undefined, oldSession?: string) {
    return withCorrelation(currentCorrelation(), () => this.callbackCorrelated(url, browser, oldSession));
  }
  private async callbackCorrelated(url: URL, browser: string | undefined, oldSession?: string) {
    try {
      return await this.callbackAccepted(url, browser, oldSession);
    } catch (error) {
      this.audit.record("authentication.failed", "callback",
        error instanceof CallbackRejected ? error.auditOutcome : error instanceof LoginCancelled || error instanceof PayloadTooLarge ? "denied" : "unavailable",
        error instanceof LoginCancelled ? "cancelled" : error instanceof CallbackRejected ? error.auditReason : error instanceof PayloadTooLarge ? "invalid_request" : "storage_unavailable");
      throw error;
    }
  }

  private async callbackAccepted(url: URL, browser: string | undefined, oldSession?: string) {
    boundedCallback(url);
    const redirect = new URL(this.config.redirectUri);
    // Enforce the registered callback at the application boundary before consuming
    // state or attempting a non-idempotent grant with a derived redirect URI.
    if (url.origin !== redirect.origin || url.pathname !== redirect.pathname ||
        url.username || url.password || url.hash) throw new CallbackRejected();
    const params = url.searchParams;
    const state = params.get("state") ?? undefined;
    if (!validId(state) || !validId(browser)) throw new CallbackRejected();
    // Consume before evaluating provider errors/code; no replay after failed exchange.
    const transaction = await this.store.consumeTransaction(
      state,
      browser,
      this.clock(),
    );
    if (!transaction) throw new CallbackRejected();
    let phase: "validation" | "provider" | "storage" = "validation";
    try {
      const allowed = new Set([
        "state",
        "code",
        "error",
        "error_description",
        "error_uri",
        "session_state",
        "iss",
      ]);
      for (const name of params.keys()) {
        if (!allowed.has(name) || params.getAll(name).length !== 1)
          throw new CallbackRejected();
      }
      if (params.has("iss") && params.get("iss") !== this.config.issuer)
        throw new CallbackRejected();
      if (params.has("error")) {
        if (params.has("code")) throw new CallbackRejected();
        if (params.get("error") === "access_denied")
          throw new LoginCancelled(transaction.returnTo);
        throw new CallbackRejected();
      }
      const code = params.get("code");
      if (
        !code ||
        code.length > 4096 ||
        params.has("error_description") ||
        params.has("error_uri")
      )
        throw new CallbackRejected();
      phase = "provider";
      const session = await this.provider.exchange(
        url,
        state,
        transaction,
        this.clock(),
      );
      phase = "storage";
      const id = randomId();
      // Reauthentication rotates the opaque ID and revokes the former local session.
      if (validId(oldSession)) {
        const oldActor = await this.store.withSession(oldSession, async (handle) => {
          const actor = handle.value ? actorIdentifier(this.config.issuer, handle.value.subject) : null;
          await handle.revoke();
          return actor;
        });
        if (oldActor) this.audit.record("session.revoked", "reauthenticate", "success", "none", oldActor);
      }
      await this.store.createSession(id, session);
      this.audit.record("session.created", validId(oldSession) ? "reauthenticate" : "callback", "success",
        "none", actorIdentifier(this.config.issuer, session.subject));
      return { id, returnTo: transaction.returnTo };
    } catch (error) {
      if (error instanceof LoginCancelled) throw error;
      // Provider and storage failures share the existing public callback rejection.
      // No external exception is included in the envelope.
      const outcome = phase === "storage" ? "unavailable" : phase === "validation" ? "denied" : providerFailureOutcome(error);
      throw new CallbackRejected(transaction.returnTo,
        phase === "storage" ? "storage_unavailable" : outcome === "unavailable" || outcome === "error"
          ? "provider_unavailable" : "callback_rejected", outcome);
    }
  }
  private async identityLocked(handle: SessionHandle, events: SecurityEvent[]): Promise<IdentityResult> {
    let session = handle.value;
    const now = this.clock();
    if (!session) return { status: "expired" };
    const actor = actorIdentifier(this.config.issuer, session.subject);
    if (session.expiresAt <= now) {
      await handle.revoke();
      events.push(this.audit.event("session.expired", "identity", "success", "session_expired", actor));
      return { status: "expired" };
    }
    if (session.accessExpiresAt <= now + 30000) {
      if (
        !session.refreshToken ||
        (session.refreshExpiresAt !== undefined &&
          session.refreshExpiresAt <= now)
      ) {
        await handle.revoke();
        events.push(this.audit.event("session.expired", "identity", "success", "session_expired", actor));
        return { status: "expired" };
      }
      if ((session.retryAfter ?? 0) > now)
        return { status: "unavailable", csrf: session.csrf };
      let refreshAccepted = false;
      try {
        session = await this.provider.refresh(session, now);
        if (session.accessExpiresAt <= this.clock())
          throw new Error("Expired access token");
        refreshAccepted = true;
        await handle.save(session);
        events.push(this.audit.event("session.refreshed", "refresh", "success", "none", actor));
      } catch (error) {
        if (error instanceof ProviderTemporaryError) {
          await handle.save({ ...session, retryAfter: now + 10000 });
          events.push(this.audit.event("session.refresh_failed", "refresh", "unavailable", "provider_unavailable", actor));
          return { status: "unavailable", csrf: session.csrf };
        }
        await handle.revoke();
        events.push(this.audit.event("session.refresh_failed", "refresh", refreshAccepted ? "unavailable" : providerFailureOutcome(error),
          refreshAccepted ? "storage_unavailable" : "refresh_rejected", actor));
        events.push(this.audit.event("session.revoked", "refresh", "success", "refresh_rejected", actor));
        return { status: "expired" };
      }
    }
    // Refresh and API request share the row lock; logout waits for active requests,
    // then prevents every subsequent authenticated call across all replicas.
    if (session.accessExpiresAt <= this.clock())
      return { status: "unavailable" };
    try {
      const response = await this.apiFetch(
        new URL("/api/v1/identity/me", this.config.apiUrl),
        { headers: { Authorization: `Bearer ${session.accessToken}`, "X-Request-ID": currentCorrelation() } },
        65536,
      );
      if (response.status === 401) {
        await handle.revoke();
        events.push(this.audit.event("session.revoked", "identity", "success", "api_rejected", actor));
        return { status: "expired" };
      }
      if (response.status === 403)
        return { status: "forbidden", csrf: session.csrf };
      if (!response.ok) return { status: "unavailable", csrf: session.csrf };
      return {
        status: "authenticated",
        identity: identityResponse((await response.json()) as unknown),
        csrf: session.csrf,
      };
    } catch {
      return { status: "unavailable", csrf: session.csrf };
    }
  }
  async identity(id: string | undefined): Promise<IdentityResult> {
    return withCorrelation(currentCorrelation(), () => this.identityCorrelated(id));
  }
  private async identityCorrelated(id: string | undefined): Promise<IdentityResult> {
    if (!validId(id)) return { status: "anonymous" };
    try {
      const events: SecurityEvent[] = [];
      const result = await this.store.withSession(id, (handle) =>
        this.identityLocked(handle, events),
      );
      // withSession returns only after COMMIT. Rollback discards confirmations.
      for (const event of events) this.audit.emit(event);
      return result;
    } catch {
      this.audit.record("authentication.failed", "identity", "unavailable", "storage_unavailable");
      return { status: "unavailable" };
    }
  }
  async logout(id: string, csrf: string, destination: string): Promise<URL> {
    return withCorrelation(currentCorrelation(), () => this.logoutCorrelated(id, csrf, destination));
  }
  private async logoutCorrelated(id: string, csrf: string, destination: string): Promise<URL> {
    try { return await this.logoutAccepted(id, csrf, destination); }
    catch (error) {
      this.audit.record("session.logout", "logout", error instanceof LogoutRejected ? "denied" : "unavailable",
        error instanceof LogoutRejected ? "invalid_request" : "storage_unavailable");
      throw error;
    }
  }
  private async logoutAccepted(id: string, csrf: string, destination: string): Promise<URL> {
    let returnTo: string;
    try { returnTo = returnPath(destination); } catch { throw new LogoutRejected(); }
    const { equalSecret } = await import("./security");
    if (!validId(id) || !validId(csrf)) throw new LogoutRejected();
    const revoked = await this.store.withSession(id, async (handle) => {
      if (!handle.value || !equalSecret(handle.value.csrf, csrf)) return null;
      const actor = actorIdentifier(this.config.issuer, handle.value.subject);
      await handle.revoke();
      return actor;
    });
    if (!revoked) throw new LogoutRejected();
    this.audit.record("session.logout", "logout", "success", "none", revoked);
    try {
      return (
        (await this.provider.logout(returnTo)) ??
        new URL(returnTo, this.config.origin)
      );
    } catch {
      return new URL(returnTo, this.config.origin);
    }
  }
}
