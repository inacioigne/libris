import { randomBytes } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import { trustedUrl } from "./auth/config";

export interface HttpPolicy { origin: string; production: boolean; httpsTerminated: boolean; providerOrigin?: string }
export function httpPolicy(env: Readonly<Record<string, string | undefined>> = process.env): HttpPolicy {
  if (!["local", "production"].includes(env.WEB_AUTH_ENV ?? "")) throw new Error("HTTP environment required");
  const production = env.WEB_AUTH_ENV === "production";
  const raw = env.WEB_ORIGIN ?? "";
  const origin = trustedUrl(raw, !production);
  if (raw !== origin.origin) throw new Error("Exact public origin required");
  // Explicit deployment assertion: TLS proxy is the only public ingress; it preserves Host.
  const httpsTerminated = env.WEB_HTTPS_TERMINATED === "1";
  if (production && !httpsTerminated) throw new Error("Trusted HTTPS ingress required");
  const issuer = env.WEB_OIDC_ISSUER;
  const providerOrigin = issuer ? trustedUrl(issuer, !production).origin : undefined;
  return { origin: origin.origin, production, httpsTerminated, providerOrigin };
}
export function contentSecurityPolicy(nonce: string, development: boolean, https: boolean, providerOrigin?: string): string {
  return [
    "default-src 'self'", `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${development ? " 'unsafe-eval'" : ""}`,
    development ? "style-src 'self' 'unsafe-inline'" : `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' data:", "font-src 'self'", `connect-src 'self'${development ? " ws: wss:" : ""}`,
    "object-src 'none'", "base-uri 'none'", `form-action 'self'${providerOrigin ? " " + providerOrigin : ""}`, "frame-ancestors 'none'",
    ...(https ? ["upgrade-insecure-requests"] : []),
  ].join("; ");
}
export function secureProxy(request: NextRequest, env: Readonly<Record<string, string | undefined>> = process.env): NextResponse {
  let policy: HttpPolicy;
  try { policy = httpPolicy(env); }
  catch {
    const failed = new NextResponse(null, { status: 503 });
    failed.headers.set("Cache-Control", "no-store, private");
    failed.headers.set("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
    failed.headers.set("X-Content-Type-Options", "nosniff");
    failed.headers.set("Referrer-Policy", "same-origin");
    failed.headers.set("Pragma", "no-cache");
    failed.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
    failed.headers.set("X-Frame-Options", "DENY");
    return failed;
  }
  const nonce = randomBytes(32).toString("base64");
  const csp = contentSecurityPolicy(nonce, !policy.production && env.NODE_ENV === "development", policy.production, policy.providerOrigin);
  const headers = new Headers(request.headers);
  // Replace client-supplied nonce/CSP before SSR. Next extracts this nonce for its scripts.
  headers.set("x-nonce", nonce);
  headers.set("Content-Security-Policy", csp);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", request.nextUrl.pathname.startsWith("/oidc/") ? "no-referrer" : "same-origin");
  response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("Cache-Control", "no-store, private");
  response.headers.set("Pragma", "no-cache");
  if (policy.production && policy.httpsTerminated && request.headers.get("host") === new URL(policy.origin).host) {
    response.headers.set("Strict-Transport-Security", "max-age=31536000");
  }
  return response;
}
