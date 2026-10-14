import "server-only";
import { headers } from "next/headers";
import { authService } from "./runtime";
import { sessionCookie, uniqueCookie } from "./security";
import type { IdentityResult } from "./service";

export async function requestIdentity(): Promise<IdentityResult> {
  try {
    const service = authService();
    return await service.identity(
      uniqueCookie(await headers(), sessionCookie(service.config)),
    );
  } catch {
    return { status: "unavailable" };
  }
}
