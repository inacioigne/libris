import "server-only";
import { headers } from "next/headers";
import {
  currentCorrelation,
  SecurityAudit,
  withCorrelation,
} from "../security-audit";
import type { Identity, IdentityResult } from "../auth/service";
import {
  satisfiesPermissions,
  shellRequirement,
  type PermissionRequirement,
} from "./navigation";

export type AdminAccess =
  | { status: "authorized"; identity: Identity; csrf: string }
  | {
      status: "access_denied";
      reason: "api_forbidden" | "insufficient_permissions";
      identity?: Identity;
      csrf?: string;
    }
  | {
      status: "login_required" | "session_expired" | "service_unavailable";
      csrf?: string;
    };

export function evaluateAdminAccess(
  result: IdentityResult,
  requirement = shellRequirement,
): AdminAccess {
  switch (result.status) {
    case "authenticated":
      return satisfiesPermissions(result.identity.permissions, requirement)
        ? { status: "authorized", identity: result.identity, csrf: result.csrf }
        : {
            status: "access_denied",
            reason: "insufficient_permissions",
            identity: result.identity,
            csrf: result.csrf,
          };
    case "forbidden":
      return {
        status: "access_denied",
        reason: "api_forbidden",
        csrf: result.csrf,
      };
    case "anonymous":
      return { status: "login_required" };
    case "expired":
      return { status: "session_expired" };
    case "unavailable":
      return { status: "service_unavailable", csrf: result.csrf };
  }
}

// Invoke protected work only after checking the server-resolved identity. Future
// pages must use their own requirement, even when a layout also checks access.
export async function guardAdminContent<T>(

  resolveIdentity: () => Promise<IdentityResult>,

  renderAuthorized: (
    access: Extract<AdminAccess, { status: "authorized" }>,
  ) => T | Promise<T>,

  renderBlocked: (
    access: Exclude<AdminAccess, { status: "authorized" }>,
  ) => T | Promise<T>,

  requirement: PermissionRequirement = shellRequirement,

  audit: SecurityAudit = new SecurityAudit(),

): Promise<T> {

  let correlation: string | null = currentCorrelation();
  try {
    correlation = (await headers()).get("x-request-id");
  } catch {
    /* Internal callers have no HTTP context. */
  }

  return withCorrelation(correlation, async () => {

    let result: IdentityResult;
    try {
      result = await resolveIdentity();
    } catch {
      result = { status: "unavailable" };
    }

    const access = evaluateAdminAccess(result, requirement);

    
    // return access

    
    
    if (access.status !== "authorized") {
      const actor =
        result.status === "authenticated" &&
        /^oidc:sha256:[0-9a-f]{64}$/.test(result.identity.actor_id)
          ? result.identity.actor_id
          : null;
      audit.record(
        "access.administrative_denied",
        "admin.access",
        access.status === "service_unavailable" ? "unavailable" : "denied",
        access.status === "access_denied"
          ? "insufficient_permissions"
          : access.status === "service_unavailable"
            ? "provider_unavailable"
            : access.status === "session_expired"
              ? "session_expired"
              : "login_required",
        actor,
      );
    }
    return access.status === "authorized"
      ? renderAuthorized(access)
      : renderBlocked(access);
  });
}
