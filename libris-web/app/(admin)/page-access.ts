import "server-only";

import { redirect, unstable_rethrow } from "next/navigation";

import { requestIdentity } from "@/lib/auth/request";
import type { Identity } from "@/types/identity";

export const adminPermission = {
  bibliographicCreate: "bibliographic:create",
  systemAdmin: "system:admin",
} as const;

type AdminPermission = (typeof adminPermission)[keyof typeof adminPermission];

export type PermissionRequirement =
  | { allOf: readonly AdminPermission[]; anyOf?: never }
  | { allOf?: never; anyOf: readonly AdminPermission[] };

export type AuthorizedAdminAccess = {
  identity: Identity;
  status: "authorized";
};

function hasRequiredPermissions(
  identity: Identity,
  requirement: PermissionRequirement,
): boolean {
  if (requirement.allOf) {
    return requirement.allOf.every((permission) =>
      identity.permissions.includes(permission),
    );
  }

  return requirement.anyOf.some((permission) =>
    identity.permissions.includes(permission),
  );
}

export async function requireAdminPageAccess(
  requirement: PermissionRequirement,
  returnTo: string,
): Promise<AuthorizedAdminAccess> {
  let identity: Identity | null;

  try {
    identity = await requestIdentity();
  } catch (error) {
    // Preserve prerender and navigation control-flow errors owned by Next.js.
    unstable_rethrow(error);
    console.error("Falha ao verificar acesso administrativo.", error);
    redirect("/unavailable");
  }

  if (!identity) {
    const loginUrl = new URL("/oidc/login", "http://libris.internal");
    loginUrl.searchParams.set("returnTo", returnTo);
    redirect(`${loginUrl.pathname}${loginUrl.search}`);
  }

  if (!hasRequiredPermissions(identity, requirement)) {
    redirect("/forbidden");
  }

  return { identity, status: "authorized" };
}
