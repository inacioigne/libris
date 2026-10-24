import "server-only";

import { cookies } from "next/headers";
import { connection } from "next/server";

import {
  getOidcLoginConfiguration,
  refreshAccessToken,
} from "@/lib/auth/oidc";
import {
  destroySession,
  getAccessToken,
  SESSION_COOKIE_NAME,
} from "@/lib/auth/session";
import { Identity } from "@/types/identity";

const DEFAULT_LOCAL_API_ORIGIN = "http://localhost:8000";

type IdentityPayload = {
  actor_id: string;
  display_name: string | null;
  picture_url: string | null;
  permissions: string[];
  roles: string[];
};

// export type Identity = {
//   actorId: string;
//   displayName: string | null;
//   pictureUrl: string | null;
//   permissions: string[];
//   roles: string[];
// };

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

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function parseIdentity(value: unknown): Identity {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("A API retornou uma identidade invalida.");
  }

  const payload = value as Partial<IdentityPayload>;
  if (
    typeof payload.actor_id !== "string" ||
    payload.actor_id.length === 0 ||
    !isNullableString(payload.display_name) ||
    !isNullableString(payload.picture_url) ||
    !isStringArray(payload.roles) ||
    !isStringArray(payload.permissions)
  ) {
    throw new Error("A API retornou uma identidade invalida.");
  }

  return {
    actorId: payload.actor_id,
    displayName: payload.display_name,
    pictureUrl: payload.picture_url,
    roles: payload.roles,
    permissions: payload.permissions,
  };
}

/** Loads the current identity without exposing the access token to the browser. */
export async function requestIdentity(): Promise<Identity | null> {
  await connection();
  const cookieStore = await cookies();
  const sessionId = cookieStore.get(SESSION_COOKIE_NAME)?.value;

  if (!sessionId) {
    return null;
  }

  const config = getOidcLoginConfiguration();
  const accessToken = await getAccessToken(sessionId, (refreshToken) =>
    refreshAccessToken(config, refreshToken),
  );
  if (!accessToken) return null;

  const response = await fetch(new URL("/api/v1/identity/me", getApiOrigin()), {
    cache: "no-store",
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (response.status === 401) {
    destroySession(sessionId);
    return null;
  }

  if (!response.ok) {
    throw new Error(`A API de identidade retornou ${response.status}.`);
  }

  return parseIdentity(await response.json());
}
