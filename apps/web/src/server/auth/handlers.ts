import "server-only";
import { currentCorrelation, withCorrelation } from "../security-audit";
import { NextRequest, NextResponse } from "next/server";
import type { AuthRoute } from "./quotas";
import type { AuthService } from "./service";
import { CallbackRejected, LoginCancelled } from "./service";
import {
  assertSameOrigin,
  boundedCallback,
  PayloadTooLarge,
  uniqueCookie,
  cookieOptions,
  returnPath,
  sessionCookie,
  transactionCookie,
  transactionCookiePath,
  validId,
} from "./security";

export function privateResponse(response: NextResponse): NextResponse {
  response.headers.set("X-Request-ID", currentCorrelation());
  response.headers.set("Cache-Control", "no-store, private");
  response.headers.set("Pragma", "no-cache");
  response.headers.set("Referrer-Policy", "no-referrer");
  return response;
}
function rejected(status = 400): NextResponse {
  return privateResponse(new NextResponse(null, { status }));
}
async function form(request: Request): Promise<URLSearchParams> {
  if (request.headers.get("content-type")?.split(";")[0].trim().toLowerCase() !==
      "application/x-www-form-urlencoded")
    throw new Error("Form required");
  const reader = request.body?.getReader();
  if (!reader) throw new Error("Body required");
  const chunks: Uint8Array[] = [];
  let size = 0;
  const deadline = AbortSignal.timeout(5000);
  const aborted = () => { void reader.cancel(); };
  deadline.addEventListener("abort", aborted, { once: true });
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (deadline.aborted) throw new Error("Form timeout");
      if (done) break;
      size += value.byteLength;
      if (size > 4096) throw new PayloadTooLarge();
      chunks.push(value);
    }
  } finally {
    deadline.removeEventListener("abort", aborted);
    await reader.cancel();
  }
  const params = new URLSearchParams(Buffer.concat(chunks).toString("utf8"));
  if ([...params].length > 8) throw new PayloadTooLarge();
  for (const key of params.keys())
    if (params.getAll(key).length !== 1)
      throw new Error("Duplicate form value");
  return params;
}

async function admission(service: AuthService, route: AuthRoute): Promise<NextResponse | undefined> {
  try {
    const quota = await service.store.takeQuota(route, service.config.quotas);
    if (!quota.allowed) {
      service.audit.record("access.quota_exceeded", route, "denied", "quota_exceeded");
      const response = rejected(429);
      response.headers.set("Retry-After", String(quota.retryAfter));
      return response;
    }
  } catch {
    service.audit.record("authentication.failed", route, "unavailable", "storage_unavailable");
    return rejected(503);
  }
}

async function loginHandlerCorrelated(
  request: NextRequest,
  service: AuthService,
): Promise<NextResponse> {
  let destination = "/pt/opac";
  try {
    assertSameOrigin(request, service.config);
    const params = await form(request);
    if ([...params.keys()].some((key) => key !== "returnTo")) throw new Error("Invalid form");
    destination = returnPath(params.get("returnTo") ?? "/pt/opac");
  } catch (error) {
    service.audit.record("authentication.failed", "login", "denied", "invalid_request");
    return rejected(error instanceof PayloadTooLarge ? 413 : 403);
  }
  const limited = await admission(service, "login");
  if (limited) return limited;
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
    service.audit.record("authentication.failed", "login", "unavailable", "provider_unavailable");
    const target = new URL(destination, service.config.origin);
    target.searchParams.set("auth", "error");
    return privateResponse(NextResponse.redirect(target, 303));
  }
}

async function callbackHandlerCorrelated(
  request: NextRequest,
  service: AuthService,
): Promise<NextResponse> {
  const incoming = new URL(request.url);
  try { boundedCallback(incoming); }
  catch {
    service.audit.record("authentication.failed", "callback", "denied", "invalid_request");
    return rejected(413);
  }
  const limited = await admission(service, "callback");
  if (limited) return limited;
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
      cookie ? uniqueCookie(request.headers, cookie) : undefined,
      uniqueCookie(request.headers, sessionCookie(service.config)),
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
        : "/pt/opac",
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
async function logoutHandlerCorrelated(
  request: NextRequest,
  service: AuthService,
): Promise<NextResponse> {
  let attempted = false;
  try {
    assertSameOrigin(request, service.config);
    const params = await form(request);
    if ([...params.keys()].some((key) => !["csrf", "returnTo"].includes(key))) throw new Error("Invalid form");
    const id = uniqueCookie(request.headers, sessionCookie(service.config)) ?? "";
    const limited = await admission(service, "logout");
    if (limited) return limited;
    attempted = true;
    const target = await service.logout(
      id,
      params.get("csrf") ?? "",
      params.get("returnTo") ?? "/pt/opac",
    );
    const response = privateResponse(NextResponse.redirect(target, 303));
    response.cookies.set(
      sessionCookie(service.config),
      "",
      cookieOptions(service.config, 0),
    );
    return response;
  } catch (error) {
    if (!attempted) service.audit.record("session.logout", "logout", "denied", "invalid_request");
    return rejected(error instanceof PayloadTooLarge ? 413 : 403);
  }
}

export function loginHandler(request: NextRequest, service: AuthService): Promise<NextResponse> {
  return withCorrelation(request.headers.get("x-request-id"), () => loginHandlerCorrelated(request, service));
}

export function callbackHandler(request: NextRequest, service: AuthService): Promise<NextResponse> {
  return withCorrelation(request.headers.get("x-request-id"), () => callbackHandlerCorrelated(request, service));
}

export function logoutHandler(request: NextRequest, service: AuthService): Promise<NextResponse> {
  return withCorrelation(request.headers.get("x-request-id"), () => logoutHandlerCorrelated(request, service));
}
