import assert from "node:assert/strict";
import { test } from "node:test";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { NextRequest } from "next/server";
import { config, MemoryStore, oidcMock, json } from "./helpers";
import { OpenIdProvider, boundedFetch } from "../src/server/auth/oidc";
import { AuthService, LoginCancelled } from "../src/server/auth/service";
import { TokenCipher } from "../src/server/auth/crypto";
import { readConfig, trustedUrl } from "../src/server/auth/config";
import { cookieOptions, returnPath, randomId, sessionCookie, transactionCookie } from "../src/server/auth/security";
import { loginHandler, callbackHandler, logoutHandler } from "../src/server/auth/handlers";
import { messages } from "../src/i18n/messages";

async function fixture(options: Parameters<typeof oidcMock>[0] = {}) {
  const cfg = config(), store = new MemoryStore(), mock = oidcMock(options);
  const provider = new OpenIdProvider(cfg, mock.transport);
  let time = Date.now();
  let apiStatus = 200;
  let apiCalls = 0;
  const service = new AuthService(cfg, store, provider, () => time, async (url, init) => {
    apiCalls++;
    assert.equal(String(url), cfg.apiUrl + "/api/v1/identity/me");
    assert.match(new Headers(init?.headers).get("Authorization") ?? "", /^Bearer (access-secret|refreshed-access-secret)$/);
    assert.equal(new Headers(init?.headers).get("Cookie"), null);
    return json({ actor_id: "oidc:sha256:test", roles: ["libris-reader"], permissions: ["bibliographic:read"] }, apiStatus);
  });
  const login = await service.start("/en?view=original");
  mock.setNonce(login.url.searchParams.get("nonce") ?? "");
  const callback = new URL(cfg.redirectUri);
  callback.searchParams.set("state", login.state);
  callback.searchParams.set("code", "code-test");
  return { cfg, store, mock, service, login, callback,
    advance(ms: number) { time += ms; }, status(value: number) { apiStatus = value; }, get apiCalls() { return apiCalls; } };
}
test("valid signed OIDC flow, PKCE S256, opaque session and API Bearer only on server", async () => {
  const f = await fixture();
  const result = await f.service.callback(f.callback, f.login.browser);
  assert.equal(result.returnTo, "/en?view=original");
  assert.equal(f.login.url.searchParams.get("code_challenge_method"), "S256");
  assert.equal(f.login.url.searchParams.get("code_challenge"),
    createHash("sha256").update(f.mock.verifier).digest("base64url"));
  assert.match(result.id, /^[a-zA-Z0-9_-]{43}$/);
  assert.equal((await f.service.identity(result.id)).status, "authenticated");
  assert.equal(f.store.sessions.size, 1);
  await assert.rejects(f.service.callback(f.callback, f.login.browser));
});
for (const mode of ["missing-state", "wrong-state", "wrong-browser", "expired", "duplicate-state",
  "duplicate-code", "missing-code", "mixed-error-code", "wrong-issuer", "unknown-param"] as const) {
  test(`callback rejects ${mode} without creating session`, async () => {
    const f = await fixture();
    let browser = f.login.browser;
    if (mode === "missing-state") f.callback.searchParams.delete("state");
    if (mode === "wrong-state") f.callback.searchParams.set("state", randomId());
    if (mode === "wrong-browser") browser = randomId();
    if (mode === "expired") f.advance(300001);
    if (mode === "duplicate-state") f.callback.searchParams.append("state", f.login.state);
    if (mode === "duplicate-code") f.callback.searchParams.append("code", "evil");
    if (mode === "missing-code") f.callback.searchParams.delete("code");
    if (mode === "mixed-error-code") f.callback.searchParams.set("error", "access_denied");
    if (mode === "wrong-issuer") f.callback.searchParams.set("iss", "https://evil.invalid");
    if (mode === "unknown-param") f.callback.searchParams.set("redirect_uri", "https://evil.invalid");
    await assert.rejects(f.service.callback(f.callback, browser));
    assert.equal(f.store.sessions.size, 0);
    if (mode === "wrong-browser") assert.equal(f.store.transactions.size, 1);
  });
}
for (const [name, options] of [
  ["nonce mismatch", { claims: { nonce: "incorrect" } }],
  ["wrong audience", { claims: { aud: "libris-api" } }],
  ["wrong issuer", { claims: { iss: "https://evil.invalid" } }],
  ["expired ID token", { claims: { exp: 1 } }],
  ["invalid signature", { invalidSignature: true }],
  ["invalid code", { tokenStatus: 400 }],
  ["provider unavailable", { tokenStatus: 503 }],
] as const) {
  test(`OIDC library rejects ${name}; failed exchange cannot replay`, async () => {
    const f = await fixture(options);
    await assert.rejects(f.service.callback(f.callback, f.login.browser));
    assert.equal(f.store.sessions.size, 0);
    await assert.rejects(f.service.callback(f.callback, f.login.browser));
  });
}
test("cancelled login retains trusted original language and destination", async () => {
  const f = await fixture();
  f.callback.searchParams.delete("code");
  f.callback.searchParams.set("error", "access_denied");
  await assert.rejects(f.service.callback(f.callback, f.login.browser),
    (e: unknown) => e instanceof LoginCancelled && e.returnTo === "/en?view=original");
});
test("independent transactions in the same browser do not mix", async () => {
  const f = await fixture();
  const second = await f.service.start("/pt");
  const url = new URL(f.cfg.redirectUri);
  url.searchParams.set("state", second.state); url.searchParams.set("code", "second-code");
  await assert.rejects(f.service.callback(url, f.login.browser));
  f.mock.setNonce(second.url.searchParams.get("nonce") ?? "");
  assert.equal((await f.service.callback(url, second.browser)).returnTo, "/pt");
});
test("session fixation prevented by ID rotation and old session revocation", async () => {
  const f = await fixture();
  const first = await f.service.callback(f.callback, f.login.browser);
  const login = await f.service.start("/en");
  f.mock.setNonce(login.url.searchParams.get("nonce") ?? "");
  f.callback.searchParams.set("state", login.state);
  const second = await f.service.callback(f.callback, login.browser, first.id);
  assert.notEqual(first.id, second.id);
  assert.equal((await f.service.identity(first.id)).status, "expired");
});
test("expired access token refreshes once for concurrent requests and persists rotated refresh", async () => {
  const f = await fixture();
  const { id } = await f.service.callback(f.callback, f.login.browser);
  f.advance(121000);
  const results = await Promise.all(Array.from({ length: 6 }, () => f.service.identity(id)));
  assert.ok(results.every((r) => r.status === "authenticated"));
  assert.equal(f.mock.refreshes, 1);
  assert.equal(f.store.sessions.get(id)?.refreshToken, "rotated-refresh-secret");
});
for (const mode of ["invalid-refresh", "no-refresh", "refresh-expired", "session-expired"] as const) {
  test(`${mode} revokes session before contacting API`, async () => {
    const f = await fixture(mode === "invalid-refresh" ? { refreshStatus: 400 } : {});
    const { id } = await f.service.callback(f.callback, f.login.browser);
    const session = f.store.sessions.get(id)!;
    if (mode === "no-refresh") delete session.refreshToken;
    if (mode === "refresh-expired") session.refreshExpiresAt = 1;
    f.advance(mode === "session-expired" ? 28800001 : 121000);
    assert.equal((await f.service.identity(id)).status, "expired");
    assert.equal(f.apiCalls, 0);
    assert.equal(f.store.sessions.size, 0);
  });
}
test("provider definite 503 fails closed with shared backoff and no expired access use", async () => {
  const f = await fixture({ refreshStatus: 503 });
  const { id } = await f.service.callback(f.callback, f.login.browser);
  f.advance(121000);
  assert.equal((await f.service.identity(id)).status, "unavailable");
  assert.equal((await f.service.identity(id)).status, "unavailable");
  assert.equal(f.mock.refreshes, 1);
  assert.equal(f.apiCalls, 0);
  assert.equal(f.store.sessions.size, 1);
});
test("API 401 revokes; 403 preserves session without claiming API authorization; 503 operational", async () => {
  for (const [status, expected] of [[401, "expired"], [403, "forbidden"], [503, "unavailable"]] as const) {
    const f = await fixture();
    const { id } = await f.service.callback(f.callback, f.login.browser);
    f.status(status);
    assert.equal((await f.service.identity(id)).status, expected);
    assert.equal(f.store.sessions.size, status === 401 ? 0 : 1);
  }
});
test("anonymous cannot contact protected API", async () => {
  const f = await fixture();
  assert.equal((await f.service.identity(undefined)).status, "anonymous");
  assert.equal(f.apiCalls, 0);
});
test("logout revokes and cannot replay; RP logout URL contains no token", async () => {
  const f = await fixture();
  const { id } = await f.service.callback(f.callback, f.login.browser);
  const csrf = f.store.sessions.get(id)!.csrf;
  await assert.rejects(f.service.logout(id, randomId(), "/en"));
  const destination = await f.service.logout(id, csrf, "/en");
  assert.equal(destination.searchParams.get("client_id"), "libris-web");
  assert.equal(destination.searchParams.get("id_token_hint"), null);
  assert.equal(destination.searchParams.get("post_logout_redirect_uri"), "http://localhost:3000/en");
  assert.equal((await f.service.identity(id)).status, "expired");
  await assert.rejects(f.service.logout(id, csrf, "/en"));
});
function post(path: string, data: URLSearchParams, cookie = "", origin = "http://localhost:3000") {
  return new NextRequest("http://localhost:3000" + path, { method: "POST",
    headers: { Origin: origin, Host: "localhost:3000", Cookie: cookie,
      "Content-Type": "application/x-www-form-urlencoded" }, body: data });
}
test("handlers: CSRF Origin/Host, cookie attributes, callback no-store and no tokens in responses", async () => {
  const f = await fixture();
  assert.equal((await loginHandler(post("/oidc/login", new URLSearchParams(), "", "https://evil.invalid"), f.service)).status, 403);
  const loginResponse = await loginHandler(post("/oidc/login", new URLSearchParams({ returnTo: "/en" })), f.service);
  assert.equal(loginResponse.status, 303);
  const url = new URL(loginResponse.headers.get("location")!);
  f.mock.setNonce(url.searchParams.get("nonce")!);
  const state = url.searchParams.get("state")!;
  const binding = loginResponse.cookies.get(transactionCookie(state))!;
  assert.equal(binding.httpOnly, true); assert.equal(binding.sameSite, "lax");
  const callback = new URL(f.cfg.redirectUri); callback.searchParams.set("state", state); callback.searchParams.set("code", "code");
  const response = await callbackHandler(new NextRequest(callback, {
    headers: { Cookie: `${binding.name}=${binding.value}` },
  }), f.service);
  const session = response.cookies.get(sessionCookie(f.cfg))!;
  assert.equal(session.httpOnly, true); assert.equal(session.path, "/"); assert.equal(session.secure, false);
  assert.equal(response.headers.get("Cache-Control"), "no-store, private");
  assert.equal(response.headers.get("Referrer-Policy"), "no-referrer");
  assert.equal(await response.text(), "");
  assert.ok(!JSON.stringify([...response.headers]).includes("access-secret"));
  assert.ok(!JSON.stringify([...response.headers]).includes("refresh-secret"));
  const cookie = `${session.name}=${session.value}`;
  const csrf = f.store.sessions.get(session.value)!.csrf;
  assert.equal((await logoutHandler(post("/oidc/logout", new URLSearchParams({ csrf, returnTo: "/en" }),
    cookie, "https://evil.invalid"), f.service)).status, 403);
  assert.equal((await logoutHandler(post("/oidc/logout", new URLSearchParams({ csrf: randomId(), returnTo: "/en" }),
    cookie), f.service)).status, 403);
  const logout = await logoutHandler(post("/oidc/logout", new URLSearchParams({ csrf, returnTo: "/en" }), cookie), f.service);
  assert.equal(logout.status, 303); assert.equal(logout.cookies.get(session.name)?.maxAge, 0);
});
test("tampered callback feedback preserves consumed trusted locale and clears transaction cookie", async () => {
  const f = await fixture();
  f.callback.searchParams.append("state", f.login.state);
  const response = await callbackHandler(new NextRequest(f.callback, { headers: {
    Cookie: `${transactionCookie(f.login.state)}=${f.login.browser}`,
  } }), f.service);
  assert.equal(new URL(response.headers.get("location")!).pathname, "/en");
  assert.equal(response.cookies.get(transactionCookie(f.login.state))?.maxAge, 0);
});
for (const path of ["https://evil.invalid", "//evil.invalid", "/en/../oidc/callback", "/en\\evil",
  "/en/%2f%2fevil", "/en/%252fevil", "/en/%0aevil", "/en#evil", "/evil", "/en/./evil"]) {
  test(`open redirect/encoded unsafe path rejected: ${path}`, () => assert.throws(() => returnPath(path)));
}
test("configuration explicit fail-closed, production HTTPS, keyring, origin and ID token audience separation", () => {
  assert.throws(() => readConfig({}));
  assert.throws(() => trustedUrl("http://example.com", true));
  assert.throws(() => trustedUrl("http://localhost:3000", false));
  assert.throws(() => trustedUrl("https://user:pass@example.com", false));
  assert.equal(config().clientId, "libris-web");
  assert.equal(cookieOptions({ ...config(), origin: "https://libris.example" }, 300).secure, true);
  assert.equal(sessionCookie({ ...config(), origin: "https://libris.example" }), "__Host-libris-session");
});
for (const discovery of [{ issuer: "https://evil.invalid" }, { token_endpoint: "https://evil.invalid/token" },
  { jwks_uri: "https://evil.invalid/keys" }, { end_session_endpoint: "https://evil.invalid/logout" },
  { code_challenge_methods_supported: ["plain"] }]) {
  test("discovery metadata/endpoint cannot change configured trust root", async () => {
    const mock = oidcMock({ discovery });
    await assert.rejects(new OpenIdProvider(config(), mock.transport).authorize(randomId(), randomId(), randomId()));
  });
}
test("encryption authenticated, context bound, key rotation allows old reads with new writes", () => {
  const cfg = config(), cipher = new TokenCipher(cfg);
  const payload = cipher.seal({ token: "secret" }, "session:one");
  assert.ok(!payload.includes("secret"));
  assert.deepEqual(cipher.open(payload, "session:one"), { token: "secret" });
  assert.throws(() => cipher.open(payload, "session:two"));
  assert.throws(() => cipher.open(payload.slice(0, -8) + "AAAAAAAA", "session:one"));
  const rotated = new TokenCipher({ activeKey: "next", keys: new Map([...cfg.keys, ["next", Buffer.alloc(32, 8)]]) });
  assert.deepEqual(rotated.open(payload, "session:one"), { token: "secret" });
  assert.ok(rotated.seal({ token: "secret" }, "session:one").startsWith("next."));
  assert.throws(() => new TokenCipher({ activeKey: "next", keys: new Map([["next", Buffer.alloc(32, 8)]]) }).open(payload, "session:one"));
});
test("pt/en vocabulary and server panel expose only API identity/CSRF, semantic native forms", async () => {
  assert.deepEqual(Object.keys(messages.pt).sort(), Object.keys(messages.en).sort());
  const source = await readFile(new URL("../src/server/auth/panel.tsx", import.meta.url), "utf8");
  assert.match(source, /<button type="submit"/);
  assert.match(source, /role="status"/);
  assert.match(source, /aria-labelledby/);
  assert.doesNotMatch(source, /accessToken|refreshToken|id_token|localStorage|sessionStorage|use client/);
  const css = await readFile(new URL("../src/app/globals.css", import.meta.url), "utf8");
  assert.match(css, /:focus-visible/);
});
test("HTTPS login binding cookie uses __Host-, Secure, HttpOnly, root path and no Domain", async () => {
  const f = await fixture();
  const cfg = { ...f.cfg, origin: "https://libris.example", localHttp: false };
  const service = new AuthService(cfg, f.store, new OpenIdProvider(f.cfg, f.mock.transport));
  const response = await loginHandler(new NextRequest("https://libris.example/oidc/login", {
    method: "POST", headers: { Origin: cfg.origin, Host: "libris.example",
      "Content-Type": "application/x-www-form-urlencoded" }, body: "returnTo=%2Fen",
  }), service);
  assert.equal(response.status, 303);
  const cookie = response.cookies.getAll()[0];
  assert.ok(cookie.name.startsWith("__Host-"));
  assert.equal(cookie.secure, true); assert.equal(cookie.httpOnly, true);
  assert.equal(cookie.path, "/"); assert.equal(cookie.domain, undefined);
});
test("logout rejects absent CSRF, mismatched Host, and duplicate form values", async () => {
  const f = await fixture();
  const { id } = await f.service.callback(f.callback, f.login.browser);
  const cookie = `libris-session=${id}`;
  assert.equal((await logoutHandler(post("/oidc/logout", new URLSearchParams(), cookie), f.service)).status, 403);
  const csrf = f.store.sessions.get(id)!.csrf;
  const duplicate = new URLSearchParams({ csrf }); duplicate.append("csrf", csrf);
  assert.equal((await logoutHandler(post("/oidc/logout", duplicate, cookie), f.service)).status, 403);
  const request = post("/oidc/logout", new URLSearchParams({ csrf }), cookie);
  request.headers.set("host", "evil.invalid");
  assert.equal((await logoutHandler(request, f.service)).status, 403);
  assert.equal(f.store.sessions.size, 1);
});
test("bounded HTTP rejects redirects, oversized streaming bodies and aborted requests", async () => {
  const { createServer } = await import("node:http");
  let redirectedCalls = 0;
  const server = createServer((request, response) => {
    if (request.url === "/redirect") {
      response.writeHead(302, { Location: "/target" }); return response.end();
    }
    if (request.url === "/target") redirectedCalls++;
    response.end("x".repeat(100));
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  const origin = `http://127.0.0.1:${address.port}`;
  try {
    await assert.rejects(boundedFetch(origin + "/redirect"));
    assert.equal(redirectedCalls, 0);
    await assert.rejects(boundedFetch(origin, {}, 10));
    const abort = new AbortController(); abort.abort();
    await assert.rejects(boundedFetch(origin, { signal: abort.signal }));
  } finally { await new Promise<void>((resolve) => server.close(() => resolve())); }
});
