import "server-only";
import type { AuthConfig } from "./config";
import {
  boundedFetch,
  ProviderTemporaryError,
  type OidcProvider,
} from "./oidc";
import { boundedCallback, randomId, returnPath, validId } from "./security";
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
  constructor(readonly returnTo = "/pt") {
    super("Callback rejected");
  }
}
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
  ) {}

  async start(
    destination: string,
  ): Promise<{ url: URL; state: string; browser: string }> {
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
    return { url, state, browser };
  }
  
  async callback(url: URL, browser: string | undefined, oldSession?: string) {
    boundedCallback(url);
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
      const session = await this.provider.exchange(
        url,
        state,
        transaction,
        this.clock(),
      );
      const id = randomId();
      // Reauthentication rotates the opaque ID and revokes the former local session.
      if (validId(oldSession))
        await this.store.withSession(oldSession, (handle) => handle.revoke());
      await this.store.createSession(id, session);
      return { id, returnTo: transaction.returnTo };
    } catch (error) {
      if (error instanceof LoginCancelled) throw error;
      throw new CallbackRejected(transaction.returnTo);
    }
  }
  private async identityLocked(handle: SessionHandle): Promise<IdentityResult> {
    let session = handle.value;
    const now = this.clock();
    if (!session) return { status: "expired" };
    if (session.expiresAt <= now) {
      await handle.revoke();
      return { status: "expired" };
    }
    if (session.accessExpiresAt <= now + 30000) {
      if (
        !session.refreshToken ||
        (session.refreshExpiresAt !== undefined &&
          session.refreshExpiresAt <= now)
      ) {
        await handle.revoke();
        return { status: "expired" };
      }
      if ((session.retryAfter ?? 0) > now)
        return { status: "unavailable", csrf: session.csrf };
      try {
        session = await this.provider.refresh(session, now);
        if (session.accessExpiresAt <= this.clock())
          throw new Error("Expired access token");
        await handle.save(session);
      } catch (error) {
        if (error instanceof ProviderTemporaryError) {
          await handle.save({ ...session, retryAfter: now + 10000 });
          return { status: "unavailable", csrf: session.csrf };
        }
        await handle.revoke();
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
        { headers: { Authorization: `Bearer ${session.accessToken}` } },
        65536,
      );
      if (response.status === 401) {
        await handle.revoke();
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
    if (!validId(id)) return { status: "anonymous" };
    try {
      return await this.store.withSession(id, (handle) =>
        this.identityLocked(handle),
      );
    } catch {
      return { status: "unavailable" };
    }
  }
  async logout(id: string, csrf: string, destination: string): Promise<URL> {
    const returnTo = returnPath(destination);
    const { equalSecret } = await import("./security");
    if (!validId(id) || !validId(csrf)) throw new Error("Logout rejected");
    const revoked = await this.store.withSession(id, async (handle) => {
      if (!handle.value || !equalSecret(handle.value.csrf, csrf)) return false;
      await handle.revoke();
      return true;
    });
    if (!revoked) throw new Error("Logout rejected");
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
