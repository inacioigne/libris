import assert from "node:assert/strict";
import { test } from "node:test";
import { NextRequest } from "next/server";
import { config, MemoryStore, oidcMock } from "./helpers";
import { AuthService } from "../src/server/auth/service";
import { OpenIdProvider } from "../src/server/auth/oidc";
import { callbackHandler, loginHandler, logoutHandler } from "../src/server/auth/handlers";
import { assertSameOrigin, boundedCallback, randomId, transactionCookie, uniqueCookie } from "../src/server/auth/security";
import { contentSecurityPolicy, httpPolicy, secureProxy } from "../src/server/http-security";

function fixture() {
  const cfg = config(), store = new MemoryStore(), mock = oidcMock();
  const service = new AuthService(cfg, store, new OpenIdProvider(cfg, mock.transport));
  return { cfg, store, mock, service };
}
function post(path = "login", body = "returnTo=%2Fen", cookie = "") {
  return new NextRequest(`http://localhost:3000/oidc/${path}`, { method: "POST", body,
    headers: { Host: "localhost:3000", Origin: "http://localhost:3000", Cookie: cookie,
      "Content-Type": "application/x-www-form-urlencoded" } });
}
const local = { WEB_AUTH_ENV: "local", WEB_ORIGIN: "http://localhost:3000", NODE_ENV: "production",
  WEB_OIDC_ISSUER: "http://keycloak.localhost:8081/realms/libris" };
const production = { WEB_AUTH_ENV: "production", WEB_ORIGIN: "https://libris.example", WEB_HTTPS_TERMINATED: "1",
  WEB_OIDC_ISSUER: "https://identity.example/realms/libris", NODE_ENV: "production" };

test("production CSP has unique SSR nonces, no eval/inline, exact OIDC form destination and private cache", () => {
  const request = new NextRequest("https://libris.example/en", { headers: { Host: "libris.example",
    "x-nonce": "attacker", "Content-Security-Policy": "script-src *" } });
  const first = secureProxy(request, production), second = secureProxy(request, production);
  const csp = first.headers.get("content-security-policy")!;
  assert.doesNotMatch(csp, /unsafe-inline|unsafe-eval|attacker/);
  assert.match(csp, /script-src 'self' 'nonce-[A-Za-z0-9+/=]+' 'strict-dynamic'/);
  assert.match(csp, /form-action 'self' https:\/\/identity.example/);
  assert.notEqual(csp, second.headers.get("content-security-policy"));
  const nonce = csp.match(/'nonce-([^']+)'/)![1];
  assert.equal(first.headers.get("x-middleware-request-x-nonce"), nonce);
  assert.equal(first.headers.get("x-middleware-request-content-security-policy"), csp);
  assert.equal(first.headers.get("strict-transport-security"), "max-age=31536000");
  assert.equal(first.headers.get("x-content-type-options"), "nosniff");
  assert.equal(first.headers.get("referrer-policy"), "same-origin");
  assert.equal(first.headers.get("x-frame-options"), "DENY");
  assert.match(first.headers.get("permissions-policy")!, /camera=\(\)/);
  assert.equal(first.headers.get("cache-control"), "no-store, private");
});
test("local production build has strict CSP without upgrading localhost/HSTS; dev allows framework debugging", () => {
  const request = new NextRequest("http://localhost:3000/pt", { headers: { Host: "localhost:3000", "X-Forwarded-Proto": "https" } });
  const response = secureProxy(request, local);
  assert.equal(response.headers.get("strict-transport-security"), null);
  assert.doesNotMatch(response.headers.get("content-security-policy")!, /unsafe-inline|unsafe-eval|upgrade-insecure/);
  assert.match(contentSecurityPolicy("test", true, false), /unsafe-eval/);
  assert.match(contentSecurityPolicy("test", true, false), /style-src 'self' 'unsafe-inline'/);
  const wrongHost = new NextRequest("https://libris.example/pt", { headers: { Host: "attacker" } });
  assert.equal(secureProxy(wrongHost, production).headers.get("strict-transport-security"), null);
});
for (const env of [{}, { ...production, WEB_HTTPS_TERMINATED: undefined }, { ...production, WEB_ORIGIN: local.WEB_ORIGIN },
  { ...local, WEB_ORIGIN: "http://external.example" }, { ...local, WEB_ORIGIN: "http://localhost:3000/" },
  { ...local, WEB_ORIGIN: "http://user:pass@localhost:3000" }, { ...production, WEB_OIDC_ISSUER: local.WEB_OIDC_ISSUER }]) {
  test("HTTP configuration fails closed without exposing configuration", async () => {
    assert.throws(() => httpPolicy(env));
    const response = secureProxy(new NextRequest("http://localhost:3000/en"), env);
    assert.equal(response.status, 503); assert.equal(await response.text(), "");
    assert.equal(response.headers.get("cache-control"), "no-store, private");
  });
}
for (const site of ["cross-site", "same-site", "unknown"]) {
  test(`POST rejects fetch metadata ${site} even with matching Origin`, async () => {
    const f = fixture(), request = post(); request.headers.set("Sec-Fetch-Site", site);
    assert.equal((await loginHandler(request, f.service)).status, 403);
    assert.equal(f.mock.requests.length, 0); assert.equal(f.store.quotas.size, 0);
  });
}
test("POST requires exact Origin/Host, allows absent fetch metadata and same-origin", () => {
  const f = fixture();
  for (const header of ["Origin", "Host"]) {
    const request = post(); request.headers.delete(header);
    assert.throws(() => assertSameOrigin(request, f.cfg));
  }
  const request = post(); request.headers.set("Sec-Fetch-Site", "same-origin");
  assert.doesNotThrow(() => assertSameOrigin(request, f.cfg));
});
for (const path of ["login", "logout"]) {
  test(`${path} rejects streamed oversized body with misleading Content-Length before database/provider`, async () => {
    const f = fixture(), request = post(path, "returnTo=" + "x".repeat(5000));
    request.headers.set("Content-Length", "1");
    const response = await (path === "login" ? loginHandler : logoutHandler)(request, f.service);
    assert.equal(response.status, 413); assert.equal(response.headers.get("cache-control"), "no-store, private");
    assert.equal(f.store.quotas.size, 0); assert.equal(f.mock.requests.length, 0);
  });
}
for (const query of ["code=" + "x".repeat(4097), "error_description=" + "x".repeat(9000),
  Array.from({ length: 9 }, (_, n) => `key${n}=a`).join("&")]) {
  test("callback rejects excessive lengths/count before quota, consumption or exchange", async () => {
    const f = fixture(), url = new URL(f.cfg.redirectUri + "?" + query);
    assert.throws(() => boundedCallback(url));
    assert.equal((await callbackHandler(new NextRequest(url), f.service)).status, 413);
    assert.equal(f.store.quotas.size, 0); assert.equal(f.mock.requests.length, 0);
  });
}
test("ambiguous binding/session cookies fail closed and cannot consume another tab's attempt", async () => {
  const f = fixture(), login = await f.service.start("/en");
  const url = new URL(f.cfg.redirectUri); url.searchParams.set("state", login.state); url.searchParams.set("code", "test");
  const name = transactionCookie(login.state);
  const response = await callbackHandler(new NextRequest(url, { headers: {
    Cookie: `${name}=${login.browser}; ${name}=${randomId()}`,
  } }), f.service);
  assert.equal(response.headers.get("location"), f.cfg.origin + "/pt/opac?auth=error");
  assert.equal(f.store.transactions.size, 1); assert.equal(f.store.sessions.size, 0);
  assert.throws(() => uniqueCookie(new Headers({ Cookie: "libris-session=a; libris-session=b" }), "libris-session"));
});
test("CSRF from a different valid session cannot revoke or logout victim", async () => {
  const f = fixture(), first = randomId(), second = randomId(), csrf = randomId();
  const session = { accessToken: "secret", accessExpiresAt: Date.now() + 60000, subject: "test", csrf, expiresAt: Date.now() + 60000 };
  await f.store.createSession(first, session); await f.store.createSession(second, { ...session, csrf: randomId() });
  assert.equal((await logoutHandler(post("logout", `csrf=${csrf}`, `libris-session=${second}`), f.service)).status, 403);
  assert.equal((await logoutHandler(post("logout", `csrf=${csrf}`, `libris-session=${first}; libris-session=${second}`), f.service)).status, 403);
  assert.equal(f.store.sessions.size, 2);
});
test("global quotas are separate by route, deterministic, concurrent, return 429 Retry-After, recover after window", async () => {
  const f = fixture(); let now = 1000; f.store.quotaClock = () => now;
  const service = new AuthService({ ...f.cfg, quotas: { windowSeconds: 60, limits: { login: 2, callback: 2, logout: 2 } } }, f.store, f.service.provider);
  const responses = await Promise.all(Array.from({ length: 8 }, () => loginHandler(post(), service)));
  assert.equal(responses.filter((r) => r.status === 303).length, 2);
  for (const response of responses.filter((r) => r.status === 429)) {
    assert.equal(response.headers.get("Retry-After"), "60");
    assert.equal(response.headers.get("cache-control"), "no-store, private");
    assert.equal(await response.text(), "");
  }
  const callback = () => callbackHandler(new NextRequest(f.cfg.redirectUri), service);
  assert.equal((await callback()).status, 303); assert.equal((await callback()).status, 303);
  assert.equal((await callback()).status, 429);
  // Forged proxy/client headers cannot create new quota keys or bypass the route quota.
  const forged = post(); forged.headers.set("X-Forwarded-For", "192.0.2.123");
  assert.equal((await loginHandler(forged, service)).status, 429);
  now += 60000;
  assert.equal((await loginHandler(post(), service)).status, 303);
});
for (const route of ["login", "callback", "logout"] as const) {
  test(`${route} quota storage unavailable fails closed with 503 and no secrets/provider call`, async () => {
    const f = fixture(); f.store.takeQuota = async () => { throw new Error("postgres://secret@database access-secret"); };
    const response = await (route === "callback" ? callbackHandler(new NextRequest(f.cfg.redirectUri), f.service) :
      (route === "login" ? loginHandler : logoutHandler)(post(route), f.service));
    assert.equal(response.status, 503); assert.equal(await response.text(), "");
    assert.doesNotMatch(JSON.stringify([...response.headers]), /secret|database/);
    assert.equal(f.mock.requests.length, 0);
  });
}
test("callback concurrent replay creates exactly one session and one token exchange", async () => {
  const f = fixture(), login = await f.service.start("/en");
  f.mock.setNonce(login.url.searchParams.get("nonce")!);
  const url = new URL(f.cfg.redirectUri); url.searchParams.set("state", login.state); url.searchParams.set("code", "test");
  const results = await Promise.allSettled(Array.from({ length: 8 }, () => f.service.callback(url, login.browser)));
  assert.equal(results.filter((r) => r.status === "fulfilled").length, 1);
  assert.equal(f.mock.requests.filter((r) => r.url.endsWith("/token")).length, 1);
  assert.equal(f.store.sessions.size, 1);
});

test("discovery failures use bounded backoff without retry loops or replaying token grants", async () => {
  let calls = 0, now = 1000;
  const provider = new OpenIdProvider(config(), async () => { calls++; throw new Error("provider-secret"); }, () => now);
  await assert.rejects(provider.authorize(randomId(), randomId(), randomId()));
  await assert.rejects(provider.authorize(randomId(), randomId(), randomId()));
  assert.equal(calls, 1);
  now += 10000;
  await assert.rejects(provider.authorize(randomId(), randomId(), randomId()));
  assert.equal(calls, 2);
});

test("provider timeout during uncertain refresh revokes session without retries or API calls", async () => {
  const f = fixture(), id = randomId(); let refreshes = 0;
  await f.store.createSession(id, { accessToken: "expired-private-access", accessExpiresAt: 1,
    refreshToken: "private-refresh", subject: "test", csrf: randomId(), expiresAt: Date.now() + 60000 });
  const provider = { ...f.service.provider,
    authorize: f.service.provider.authorize.bind(f.service.provider),
    exchange: f.service.provider.exchange.bind(f.service.provider),
    logout: f.service.provider.logout.bind(f.service.provider),
    refresh: async () => { refreshes++; throw new DOMException("private-refresh", "TimeoutError"); },
  };
  const service = new AuthService(f.cfg, f.store, provider, Date.now, async () => { throw new Error("API must not be called"); });
  assert.deepEqual(await service.identity(id), { status: "expired" });
  assert.deepEqual(await service.identity(id), { status: "expired" });
  assert.equal(refreshes, 1); assert.equal(f.store.sessions.size, 0);
});

test("OIDC routes retain no-referrer while document forms preserve same-origin", () => {
  const response = secureProxy(new NextRequest("http://localhost:3000/oidc/callback"), local);
  assert.equal(response.headers.get("Referrer-Policy"), "no-referrer");
});

test("WEB_AUTH_ENV production never allows development CSP exceptions", () => {
  const response = secureProxy(new NextRequest("https://libris.example/en"), { ...production, NODE_ENV: "development" });
  assert.doesNotMatch(response.headers.get("Content-Security-Policy")!, /unsafe-inline|unsafe-eval|ws:/);
});
