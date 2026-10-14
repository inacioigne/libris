import "server-only";
import { createHash, randomBytes, timingSafeEqual } from "node:crypto";
import type { AuthConfig } from "./config";

export const randomId = () => randomBytes(32).toString("base64url");
export const digest = (value: string) => createHash("sha256").update(value).digest("hex");
export const validId = (value: string | undefined): value is string => !!value && /^[A-Za-z0-9_-]{43}$/.test(value);
export function equalSecret(left: string, right: string): boolean {
  const a = Buffer.from(left), b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}
export function returnPath(value: string): string {
  // Deliberately narrow: only canonical locale-relative paths. Encoded separators,
  // control characters and double encoding are rejected before URL parsing.
  if (value.length > 2048 || /[\\\s#\u0000-\u001f\u007f]/.test(value) || /%(?:0[0-9a-f]|1[0-9a-f]|7f|2f|5c|25)/i.test(value) ||
      !/^\/(pt|en)(?:\/|\?|$)/.test(value)) throw new Error("Invalid return destination");
  const url = new URL(value, "https://libris.invalid");
  if (url.origin !== "https://libris.invalid" || url.pathname !== value.split("?")[0]) {
    throw new Error("Invalid return destination");
  }
  if (!/^\/(pt|en)(?:\/admin)?$/.test(url.pathname)) throw new Error("Invalid return destination");
  return value;
}
export function assertSameOrigin(request: Request, config: AuthConfig): void {
  if (request.headers.get("origin") !== config.origin ||
      request.headers.get("host") !== new URL(config.origin).host ||
      (request.headers.has("sec-fetch-site") &&
        !["same-origin", "none"].includes(request.headers.get("sec-fetch-site") ?? ""))) throw new Error("Request origin rejected");
}
export function cookieOptions(config: AuthConfig, maxAge: number, path = "/") {
  return { httpOnly: true, secure: new URL(config.origin).protocol === "https:",
    sameSite: "lax" as const, path, maxAge };
}
export function sessionCookie(config: AuthConfig): string {
  return new URL(config.origin).protocol === "https:" ? "__Host-libris-session" : "libris-session";
}
export const transactionCookie = (state: string, config?: AuthConfig) =>
  `${config && new URL(config.origin).protocol === "https:" ? "__Host-" : ""}libris-oidc-${digest(state).slice(0, 32)}`;
export const transactionCookiePath = (config: AuthConfig) =>
  new URL(config.origin).protocol === "https:" ? "/" : "/oidc/callback";

// Next's parsed cookie map collapses duplicates; inspect the original header instead.
export function uniqueCookie(headers: Headers, name: string): string | undefined {
  const values = (headers.get("cookie") ?? "").split(";").map((part) => part.trim())
    .filter((part) => part.includes("=") && part.slice(0, part.indexOf("=")) === name)
    .map((part) => part.slice(part.indexOf("=") + 1));
  if (values.length > 1) throw new Error("Ambiguous cookie");
  return values[0];
}
export class PayloadTooLarge extends Error {}
export function boundedCallback(url: URL): void {
  if (Buffer.byteLength(url.search, "utf8") > 8192) throw new PayloadTooLarge();
  const entries = [...url.searchParams];
  if (entries.length > 8 || entries.some(([key, value]) => key.length > 64 || value.length > 4096)) {
    throw new PayloadTooLarge();
  }
}
