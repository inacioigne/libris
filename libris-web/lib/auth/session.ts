import "server-only";

import { createHash, randomBytes } from "node:crypto";

import type { OidcTokenSet } from "@/lib/auth/oidc";

export const SESSION_COOKIE_NAME = "libris.session";

const DEFAULT_SESSION_SECONDS = 8 * 60 * 60;
const REFRESH_WINDOW_MS = 30_000;

type StoredSession = {
  absoluteExpiresAt: number;
  refreshInFlight?: Promise<StoredSession | null>;
  tokens: OidcTokenSet;
};

type SessionRegistry = Map<string, StoredSession>;

declare global {
  var librisSessionRegistry: SessionRegistry | undefined;
}

function sessionSeconds(): number {
  const value = Number(process.env.WEB_SESSION_SECONDS ?? DEFAULT_SESSION_SECONDS);
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error("WEB_SESSION_SECONDS deve ser um inteiro positivo.");
  }
  return value;
}

function registry(): SessionRegistry {
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "O armazenamento local de sessoes nao pode ser usado em producao. Configure um SessionStore compartilhado.",
    );
  }
  return (globalThis.librisSessionRegistry ??= new Map());
}

function sessionKey(sessionId: string): string | null {
  if (!/^[A-Za-z0-9_-]{43}$/.test(sessionId)) return null;
  return createHash("sha256").update(sessionId).digest("hex");
}

function lookup(sessionId: string): { key: string; session: StoredSession } | null {
  const key = sessionKey(sessionId);
  if (!key) return null;
  const sessions = registry();
  const session = sessions.get(key);
  if (!session) return null;
  if (session.absoluteExpiresAt <= Date.now()) {
    sessions.delete(key);
    return null;
  }
  return { key, session };
}

export function createSession(tokens: OidcTokenSet) {
  const sessionId = randomBytes(32).toString("base64url");
  const key = sessionKey(sessionId);
  if (!key) throw new Error("Falha ao gerar identificador de sessao.");
  const configuredExpiry = Date.now() + sessionSeconds() * 1000;
  const providerExpiry = tokens.refreshExpiresAt ?? tokens.accessExpiresAt;
  const absoluteExpiresAt = Math.min(configuredExpiry, providerExpiry);
  registry().set(key, { absoluteExpiresAt, tokens });
  return { expiresAt: absoluteExpiresAt, sessionId };
}

export async function getAccessToken(
  sessionId: string,
  refresh: (refreshToken: string) => Promise<OidcTokenSet>,
): Promise<string | null> {
  const found = lookup(sessionId);
  if (!found) return null;
  if (found.session.tokens.accessExpiresAt > Date.now() + REFRESH_WINDOW_MS) {
    return found.session.tokens.accessToken;
  }
  if (!found.session.tokens.refreshToken) return null;

  found.session.refreshInFlight ??= (async () => {
    try {
      const refreshed = await refresh(found.session.tokens.refreshToken!);
      const current = lookup(sessionId);
      if (!current) return null;
      current.session.tokens = refreshed;
      return current.session;
    } catch {
      registry().delete(found.key);
      return null;
    } finally {
      const current = registry().get(found.key);
      if (current) current.refreshInFlight = undefined;
    }
  })();

  const refreshed = await found.session.refreshInFlight;
  return refreshed?.tokens.accessToken ?? null;
}

export function destroySession(sessionId: string): OidcTokenSet | null {
  const found = lookup(sessionId);
  if (!found) return null;
  registry().delete(found.key);
  return found.session.tokens;
}

export function sessionCookieMaxAge(expiresAt: number): number {
  return Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
}
