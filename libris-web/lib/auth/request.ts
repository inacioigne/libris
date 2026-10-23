import "server-only";

import { cookies } from "next/headers";

import { SESSION_COOKIE_PREFIX } from "@/lib/auth/oidc";

const DEFAULT_LOCAL_API_ORIGIN = "http://localhost:8000";

type IdentityPayload = {
  actor_id: string;
  permissions: string[];
  roles: string[];
};

export type Identity = {
  actorId: string;
  permissions: string[];
  roles: string[];
};

function getApiOrigin(): URL {
  const configuredOrigin = process.env.API_INTERNAL_URL?.trim();

  if (!configuredOrigin && process.env.NODE_ENV === "production") {
    throw new Error("A variavel de ambiente API_INTERNAL_URL e obrigatoria.");
  }

  const origin = new URL(configuredOrigin || DEFAULT_LOCAL_API_ORIGIN);
  if (origin.protocol !== "http:" && origin.protocol !== "https:") {
    throw new Error("API_INTERNAL_URL deve usar HTTP ou HTTPS.");
  }

  return origin;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function parseIdentity(value: unknown): Identity {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("A API retornou uma identidade invalida.");
  }

  const payload = value as Partial<IdentityPayload>;
  if (
    typeof payload.actor_id !== "string" ||
    payload.actor_id.length === 0 ||
    !isStringArray(payload.roles) ||
    !isStringArray(payload.permissions)
  ) {
    throw new Error("A API retornou uma identidade invalida.");
  }

  return {
    actorId: payload.actor_id,
    roles: payload.roles,
    permissions: payload.permissions,
  };
}

/** Loads the current identity without exposing the access token to the browser. */
export async function requestIdentity(): Promise<Identity | null> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(
    `${SESSION_COOKIE_PREFIX}.access-token`,
  )?.value;

  if (!accessToken) {
    return null;
  }

  const response = await fetch(new URL("/api/v1/identity/me", getApiOrigin()), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`A API de identidade retornou ${response.status}.`);
  }

  return parseIdentity(await response.json());
}
