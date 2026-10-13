import "server-only";
import type { Identity, IdentityResult } from "../auth/service";
import { satisfiesPermissions, shellRequirement, type PermissionRequirement } from "./navigation";

export type AdminAccess =
  | { status: "authorized"; identity: Identity; csrf: string }
  | { status: "access_denied"; reason: "api_forbidden" | "insufficient_permissions"; identity?: Identity; csrf?: string }
  | { status: "login_required" | "session_expired" | "service_unavailable"; csrf?: string };

export function evaluateAdminAccess(result: IdentityResult, requirement = shellRequirement): AdminAccess {
  switch (result.status) {
    case "authenticated":
      return satisfiesPermissions(result.identity.permissions, requirement)
        ? { status: "authorized", identity: result.identity, csrf: result.csrf }
        : { status: "access_denied", reason: "insufficient_permissions", identity: result.identity, csrf: result.csrf };
    case "forbidden": return { status: "access_denied", reason: "api_forbidden", csrf: result.csrf };
    case "anonymous": return { status: "login_required" };
    case "expired": return { status: "session_expired" };
    case "unavailable": return { status: "service_unavailable", csrf: result.csrf };
  }
}

// Invoke protected work only after checking the server-resolved identity. Future
// pages must use their own requirement, even when a layout also checks access.
export async function guardAdminContent<T>(
  resolveIdentity: () => Promise<IdentityResult>,
  renderAuthorized: (access: Extract<AdminAccess, { status: "authorized" }>) => T | Promise<T>,
  renderBlocked: (access: Exclude<AdminAccess, { status: "authorized" }>) => T | Promise<T>,
  requirement: PermissionRequirement = shellRequirement,
): Promise<T> {
  let result: IdentityResult;
  try { result = await resolveIdentity(); }
  catch { result = { status: "unavailable" }; }
  const access = evaluateAdminAccess(result, requirement);
  return access.status === "authorized" ? renderAuthorized(access) : renderBlocked(access);
}
