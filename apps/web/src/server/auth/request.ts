import "server-only";
import { cookies } from "next/headers";
import { authService } from "./runtime";
import { sessionCookie } from "./security";
import type { IdentityResult } from "./service";

export async function requestIdentity(): Promise<IdentityResult> {
  try {
    const service = authService();
    return await service.identity(
      (await cookies()).get(sessionCookie(service.config))?.value,
    );
  } catch {
    return { status: "unavailable" };
  }
}
