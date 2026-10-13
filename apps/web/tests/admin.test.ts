import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile } from "node:fs/promises";
import { NextRequest } from "next/server";
import { adminNavigation, administrativePermissions, satisfiesPermissions, shellRequirement } from "../src/server/admin/navigation";
import { evaluateAdminAccess, guardAdminContent } from "../src/server/admin/access";
import { AuthService, type IdentityResult } from "../src/server/auth/service";
import { OpenIdProvider } from "../src/server/auth/oidc";
import { returnPath, randomId, transactionCookie } from "../src/server/auth/security";
import { loginHandler, callbackHandler } from "../src/server/auth/handlers";
import { config, MemoryStore, oidcMock, json } from "./helpers";
import { messages } from "../src/i18n/messages";

const identity = (permissions: string[], roles = ["libris-admin"]): IdentityResult => ({
  status: "authenticated", identity: { actor_id: "oidc:sha256:synthetic", roles, permissions }, csrf: randomId(),
});
const cases: { name: string; permissions: string[]; expected: string[] }[] = [
  { name: "empty", permissions: [], expected: [] },
  { name: "reader", permissions: ["bibliographic:read", "authority:read"], expected: [] },
  { name: "cataloger", permissions: ["bibliographic:create", "bibliographic:update", "metadata_revision:create", "metadata_revision:read", "editorial:submit"], expected: ["cataloging", "history", "editorial"] },
  { name: "authority manager", permissions: ["authority:manage"], expected: ["authorities"] },
  { name: "reviewer", permissions: ["metadata_revision:read", "metadata_audit:read", "editorial:approve", "editorial:return"], expected: ["history", "editorial"] },
  { name: "publisher", permissions: ["metadata_revision:read", "metadata_audit:read", "editorial:publish", "editorial:withdraw", "editorial:republish", "editorial:archive"], expected: ["history", "editorial"] },
  { name: "administrator", permissions: [...administrativePermissions], expected: ["cataloging", "authorities", "history", "editorial", "system"] },
  { name: "system permission alone", permissions: ["system:admin"], expected: ["system"] },
  { name: "combined", permissions: ["authority:manage", "editorial:publish", "bibliographic:update"], expected: ["cataloging", "authorities", "editorial"] },
  { name: "unknown", permissions: ["admin:*", "system:root", "BIBLIOGRAPHIC:CREATE"], expected: [] },
];
for (const { name, permissions, expected } of cases) {
  test(`shell and deterministic navigation: ${name}; roles never grant access`, () => {
    assert.equal(evaluateAdminAccess(identity(permissions)).status, expected.length ? "authorized" : "access_denied");
    for (const locale of ["pt", "en"] as const) {
      const items = adminNavigation(permissions, locale);
      assert.deepEqual(items.map((item) => item.id), expected);
      for (const item of items) {
        assert.equal(item.href, `/${locale}/admin#${item.id}`);
        assert.equal(item.label, messages[locale][item.id]);
        assert.equal(item.mode, "any");
      }
    }
  });
}
test("all/any explicit; empty requirements fail closed and system:admin is no bypass", () => {
  const requiredPermissions = ["bibliographic:update", "metadata_revision:create"] as const;
  assert.equal(satisfiesPermissions(["bibliographic:update"], { mode: "all", requiredPermissions }), false);
  assert.equal(satisfiesPermissions(["bibliographic:update"], { mode: "any", requiredPermissions }), true);
  assert.equal(satisfiesPermissions([...requiredPermissions], { mode: "all", requiredPermissions }), true);
  assert.equal(satisfiesPermissions(["system:admin"], { mode: "any", requiredPermissions }), false);
  for (const mode of ["any", "all"] as const) assert.equal(satisfiesPermissions(["system:admin"], { mode, requiredPermissions: [] }), false);
});
test("UI permission requirements agree with the backend enum, excluding public read", async () => {
  const source = await readFile(new URL("../../api/src/libris/modules/identity/domain/permissions.py", import.meta.url), "utf8");
  const values = [...source.matchAll(/= "([a-z_]+:[a-z_]+)"/g)].map((match) => match[1]);
  assert.deepEqual([...administrativePermissions].sort(), values.filter((p) => !["bibliographic:read", "authority:read"].includes(p)).sort());
});
test("insufficient permissions preserve authenticated identity and CSRF; API forbidden is distinct", () => {
  const input = identity([]);
  const access = evaluateAdminAccess(input);
  assert.equal(access.status, "access_denied");
  if (access.status !== "access_denied" || input.status !== "authenticated") throw new Error("wrong status");
  assert.equal(access.identity, input.identity);
  assert.equal(access.csrf, input.csrf);
  assert.equal(access.reason, "insufficient_permissions");
  const forbidden = evaluateAdminAccess({ status: "forbidden", csrf: input.csrf });
  assert.equal(forbidden.status, "access_denied");
  if (forbidden.status !== "access_denied") throw new Error("wrong status");
  assert.equal(forbidden.reason, "api_forbidden");
  assert.equal(forbidden.identity, undefined);
});
for (const [status, expected] of [["anonymous", "login_required"], ["expired", "session_expired"], ["forbidden", "access_denied"], ["unavailable", "service_unavailable"]] as const) {
  test(`guard never invokes protected work for ${status}`, async () => {
    let calls = 0;
    const rendered = await guardAdminContent(async () => ({ status }), () => { calls++; return "protected"; }, (access) => access.status);
    assert.equal(rendered, expected);
    assert.equal(calls, 0);
  });
}
test("guard blocks missing permission, resolver failure, and stricter future page requirement", async () => {
  const protectedRender = () => { throw new Error("Protected code was invoked"); };
  assert.equal(await guardAdminContent(async () => identity([]), protectedRender, (access) => access.status), "access_denied");
  assert.equal(await guardAdminContent(async () => { throw new Error("database secret"); }, protectedRender, (access) => access.status), "service_unavailable");
  assert.equal(await guardAdminContent(async () => identity(["system:admin"]), protectedRender, (access) => access.status,
    { mode: "all", requiredPermissions: ["authority:manage"] }), "access_denied");
  assert.equal(await guardAdminContent(async () => identity(["authority:manage"]), (access) => access.status, () => "blocked", shellRequirement), "authorized");
});
test("AuthService and guard use only API effective permissions and retain insufficient session", async () => {
  const cfg = config(), store = new MemoryStore(), mock = oidcMock();
  const id = randomId();
  store.sessions.set(id, { accessToken: "server-secret", accessExpiresAt: Date.now() + 120000, expiresAt: Date.now() + 300000, subject: "test", csrf: randomId() });
  let permissions: string[] = ["bibliographic:read"];
  let status = 200;
  const service = new AuthService(cfg, store, new OpenIdProvider(cfg, mock.transport), Date.now, async (_url, init) => {
    assert.equal(new Headers(init?.headers).get("authorization"), "Bearer server-secret");
    return json({ actor_id: "oidc:sha256:test", roles: ["libris-admin"], permissions }, status);
  });
  const check = () => guardAdminContent(() => service.identity(id), () => "protected", (access) => access.status);
  assert.equal(await check(), "access_denied"); assert.equal(store.sessions.size, 1);
  permissions = ["authority:manage"];
  assert.equal(await check(), "protected");
  status = 503; assert.equal(await check(), "service_unavailable");
  status = 403; assert.equal(await check(), "access_denied"); assert.equal(store.sessions.size, 1);
  status = 401; assert.equal(await check(), "session_expired"); assert.equal(store.sessions.size, 0);
});
for (const locale of ["pt", "en"] as const) {
  test(`login callback returns to trusted ${locale} admin and rejects tampering`, async () => {
    const cfg = config(), store = new MemoryStore(), mock = oidcMock();
    const service = new AuthService(cfg, store, new OpenIdProvider(cfg, mock.transport));
    const destination = `/${locale}/admin`;
    assert.equal(returnPath(destination), destination);
    const login = await loginHandler(new NextRequest(cfg.origin + "/oidc/login", {
      method: "POST", headers: { Origin: cfg.origin, Host: "localhost:3000", "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ returnTo: destination }),
    }), service);
    const url = new URL(login.headers.get("location")!);
    mock.setNonce(url.searchParams.get("nonce")!);
    const state = url.searchParams.get("state")!;
    const binding = login.cookies.get(transactionCookie(state))!;
    const callback = new URL(cfg.redirectUri);
    callback.searchParams.set("state", state); callback.searchParams.set("code", "test");
    const headers = { Cookie: `${binding.name}=${binding.value}` };
    assert.equal((await callbackHandler(new NextRequest(callback, { headers }), service)).headers.get("location"), cfg.origin + destination);
    assert.equal((await callbackHandler(new NextRequest(callback, { headers }), service)).headers.get("location"), cfg.origin + "/pt?auth=error");
    const second = await service.start(destination);
    callback.searchParams.set("state", second.state);
    callback.searchParams.set("returnTo", "https://evil.invalid");
    const rejected = await callbackHandler(new NextRequest(callback, { headers: { Cookie: `${transactionCookie(second.state)}=${second.browser}` } }), service);
    assert.equal(rejected.headers.get("location"), cfg.origin + destination + "?auth=error");
    assert.equal(store.sessions.size, 1);
  });
}
for (const path of ["/pt/admin/users", "/en/other", "/en/", "/en/%61dmin", "/en/admin/..", "/pt/./admin", "/pt/admin%2f", "/pt/admin%252f", "/pt/admin\\evil", "/pt/admin\u0000", "/pt/admin#evil", "/pt/admin?x=\u0000", "/pt/admin?x=\u007f", "//evil.invalid/en/admin", "https://evil.invalid/pt/admin"]) {
  test(`admin return rejects unauthorized path: ${JSON.stringify(path)}`, () => assert.throws(() => returnPath(path)));
}
test("no logging of auth internals; pt/en messages complete and server shell has no token properties", async () => {
  assert.deepEqual(Object.keys(messages.pt).sort(), Object.keys(messages.en).sort());
  for (const name of ["handlers.ts", "runtime.ts", "config.ts", "panel.tsx"]) {
    const source = await readFile(new URL(`../src/server/auth/${name}`, import.meta.url), "utf8");
    assert.doesNotMatch(source, /console\.(log|error|debug)/);
  }
  const source = await readFile(new URL("../src/server/admin/shell.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(source, /accessToken|refreshToken|id_token|localStorage|sessionStorage|use client/);
});

test("baseline text and focus colors meet WCAG contrast ratios; manual browser audit still required", async () => {
  const luminance = (hex: string) => {
    const rgb = hex.match(/[0-9a-f]{2}/gi)!.map((value) => {
      const channel = parseInt(value, 16) / 255;
      return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  };
  const contrast = (foreground: string, background: string) => {
    const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
    return (values[0] + 0.05) / (values[1] + 0.05);
  };
  const css = await readFile(new URL("../src/app/globals.css", import.meta.url), "utf8");
  assert.match(css, /background: #f6f8f7; color: #172d29/);
  assert.match(css, /:focus-visible \{ outline: 3px solid #0f766e/);
  for (const background of ["ffffff", "f6f8f7"]) {
    assert.ok(contrast("172d29", background) >= 4.5);
    assert.ok(contrast("0f766e", background) >= 3);
  }
});
