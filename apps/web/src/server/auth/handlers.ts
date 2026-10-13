import "server-only";
import { NextRequest, NextResponse } from "next/server";
import type { AuthService } from "./service";
import { CallbackRejected, LoginCancelled } from "./service";
import {
  assertSameOrigin,
  cookieOptions,
  returnPath,
  sessionCookie,
  transactionCookie,
  transactionCookiePath,
  validId,
} from "./security";

export function privateResponse(response: NextResponse): NextResponse {
  response.headers.set("Cache-Control", "no-store, private");
  response.headers.set("Pragma", "no-cache");
  response.headers.set("Referrer-Policy", "no-referrer");
  return response;
}
function rejected(status = 400): NextResponse {
  return privateResponse(new NextResponse(null, { status }));
}
async function form(request: Request): Promise<URLSearchParams> {
  if (
    !request.headers
      .get("content-type")
      ?.startsWith("application/x-www-form-urlencoded")
  )
    throw new Error("Form required");
  const reader = request.body?.getReader();
  if (!reader) throw new Error("Body required");
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 4096) throw new Error("Form too large");
      chunks.push(value);
    }
  } finally {
    await reader.cancel();
  }
  const params = new URLSearchParams(Buffer.concat(chunks).toString("utf8"));
  for (const key of params.keys())
    if (params.getAll(key).length !== 1)
      throw new Error("Duplicate form value");
  return params;
}

export async function loginHandler(
  request: NextRequest,
  service: AuthService,
): Promise<NextResponse> {
  let destination = "/pt";
  try {
    assertSameOrigin(request, service.config);
    const params = await form(request);
    destination = returnPath(params.get("returnTo") ?? "/pt");
  } catch {
    return rejected(403);
  }
  try {
    const login = await service.start(destination);
    const response = privateResponse(NextResponse.redirect(login.url, 303));
    response.cookies.set(
      transactionCookie(login.state, service.config),
      login.browser,
      cookieOptions(service.config, 300, transactionCookiePath(service.config)),
    );
    return response;
  } catch {
    const target = new URL(destination, service.config.origin);
    target.searchParams.set("auth", "error");
    return privateResponse(NextResponse.redirect(target, 303));
  }
}

export async function callbackHandler(
  request: NextRequest,
  service: AuthService,
): Promise<NextResponse> {
  const incoming = new URL(request.url);
  // Never derive redirect_uri or public origin from untrusted forwarded headers.
  const url = new URL(service.config.redirectUri);
  url.search = incoming.search;
  const state = incoming.searchParams.get("state") ?? undefined;
  const cookie = validId(state)
    ? transactionCookie(state, service.config)
    : undefined;
  let response: NextResponse;
  try {
    const result = await service.callback(
      url,
      cookie ? request.cookies.get(cookie)?.value : undefined,
      request.cookies.get(sessionCookie(service.config))?.value,
    );
    response = NextResponse.redirect(
      new URL(result.returnTo, service.config.origin),
      303,
    );
    response.cookies.set(
      sessionCookie(service.config),
      result.id,
      cookieOptions(service.config, service.config.sessionSeconds),
    );
  } catch (error) {
    const target = new URL(
      error instanceof LoginCancelled || error instanceof CallbackRejected
        ? error.returnTo
        : "/pt",
      service.config.origin,
    );
    // Recover locale/destination only from trusted, consumed transaction on cancellation.
    target.searchParams.set(
      "auth",
      error instanceof LoginCancelled ? "cancelled" : "error",
    );
    response = NextResponse.redirect(target, 303);
  }
  if (cookie)
    response.cookies.set(
      cookie,
      "",
      cookieOptions(service.config, 0, transactionCookiePath(service.config)),
    );
  return privateResponse(response);
}
export async function logoutHandler(
  request: NextRequest,
  service: AuthService,
): Promise<NextResponse> {
  try {
    assertSameOrigin(request, service.config);
    const params = await form(request);
    const id = request.cookies.get(sessionCookie(service.config))?.value ?? "";
    const target = await service.logout(
      id,
      params.get("csrf") ?? "",
      params.get("returnTo") ?? "/pt",
    );
    const response = privateResponse(NextResponse.redirect(target, 303));
    response.cookies.set(
      sessionCookie(service.config),
      "",
      cookieOptions(service.config, 0),
    );
    return response;
  } catch {
    return rejected(403);
  }
}
