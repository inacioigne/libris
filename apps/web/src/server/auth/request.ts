import "server-only";
import { withCorrelation } from "../security-audit";
import { headers } from "next/headers";
import { authService } from "./runtime";
import { sessionCookie, uniqueCookie } from "./security";
import type { IdentityResult } from "./service";

export async function requestIdentity(): Promise<IdentityResult> {
  try {
    const service = authService();
    const incoming = await headers();
    return await withCorrelation(incoming.get("x-request-id"), () => service.identity(
      uniqueCookie(incoming, sessionCookie(service.config)),
    ));
  } catch {
    return { status: "unavailable" };
  }
}
