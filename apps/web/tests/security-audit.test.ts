import assert from "node:assert/strict";
import { test } from "node:test";
import { randomUUID } from "node:crypto";
import { NextRequest } from "next/server";
import { config, MemoryStore, oidcMock, json } from "./helpers";
import { AuthService } from "../src/server/auth/service";
import { OpenIdProvider } from "../src/server/auth/oidc";
import { randomId } from "../src/server/auth/security";
import { loginHandler, callbackHandler, logoutHandler } from "../src/server/auth/handlers";
import { guardAdminContent } from "../src/server/admin/access";
import { secureProxy } from "../src/server/http-security";
import {
  actorIdentifier, currentCorrelation, LoggingSecuritySink, safeCorrelation,
  SecurityAudit, serializeSecurityEvent, withCorrelation, type SecurityEvent,
} from "../src/server/security-audit";

async function fixture(options: Parameters<typeof oidcMock>[0] = {}, store = new MemoryStore()) {
  const cfg = config(), mock = oidcMock(options), events: SecurityEvent[] = [], apiIds: string[] = [];
  const audit = new SecurityAudit({ emit(event) { events.push(event); } });
  let now = Date.now();
  const actor = actorIdentifier(cfg.issuer, "subject-test");
  const service = new AuthService(cfg, store, new OpenIdProvider(cfg, mock.transport), () => now,
    async (_url, init) => {
      apiIds.push(new Headers(init?.headers).get("X-Request-ID")!);
      return json({ actor_id: actor, roles: ["libris-reader"], permissions: ["bibliographic:read"] });
    }, audit);
  const login = await service.start("/en");
  mock.setNonce(login.url.searchParams.get("nonce")!);
  const url = new URL(cfg.redirectUri);
  url.searchParams.set("state", login.state); url.searchParams.set("code", "CODE-SENTINEL");
  return { cfg, mock, events, apiIds, store, service, audit, actor, login, url,
    advance(ms: number) { now += ms; } };
}

for (const value of [undefined, "", "bad", "a".repeat(10000), "a\r\nInjected: true", randomUUID().toUpperCase()]) {
  test("unsafe correlation replaced with canonical UUID: " + String(value).slice(0, 30), () => {
    const id = safeCorrelation(value);
    assert.match(id, /^[0-9a-f-]{36}$/); assert.notEqual(id, value);
  });
}
test("native JSON log, UTC, fixed fields, opaque identity matching Python algorithm", () => {
  const audit = new SecurityAudit();
  const id = randomUUID();
  const event = withCorrelation(id, () => audit.event("authentication.failed", "callback", "denied"));
  assert.equal(event.correlation_id, id); assert.equal(event.actor_id, null);
  assert.match(event.occurred_at, /Z$/); assert.ok(Object.isFrozen(event));
  assert.equal(serializeSecurityEvent(event), serializeSecurityEvent(event));
  assert.equal(actorIdentifier("issuer", "subject"), "oidc:sha256:7344bb084ead65e0d8b7611539563213d31ff354d5018ba77612aaf8bcece4c2");
  const lines: string[] = [], previous = console.info;
  console.info = (line: string) => { lines.push(line); };
  try { new LoggingSecuritySink().emit(event); } finally { console.info = previous; }
  assert.deepEqual(JSON.parse(lines[0]), event);
  for (const field of ["Authorization", "Cookie", "Set-Cookie", "access_token", "refresh_token", "id_token",
    "password", "client_secret", "code", "code_verifier", "csrf", "session_id", "body", "query", "claims"]) {
    assert.throws(() => serializeSecurityEvent({ ...event, [field]: "SECRET" }));
  }
  for (const mutation of [{ occurred_at: "2026-10-14T00:00:00" }, { actor_id: "raw-subject" },
    { correlation_id: "a\r\nb" }, { event_type: "arbitrary" }, { outcome: "arbitrary" }, { reason: "SECRET" }]) {
    assert.throws(() => serializeSecurityEvent({ ...event, ...mutation } as SecurityEvent));
  }
});
test("created session is confirmed once with validated actor and no credentials in records", async () => {
  const f = await fixture();
  const { id } = await f.service.callback(f.url, f.login.browser);
  assert.ok(f.store.sessions.has(id));
  assert.equal(f.events.filter((e) => e.event_type === "session.created").length, 1);
  const created = f.events.at(-1)!;
  assert.equal(created.actor_id, f.actor); assert.equal(created.action, "callback"); assert.equal(created.outcome, "success");
  await assert.rejects(f.service.callback(f.url, f.login.browser));
  assert.equal(f.events.at(-1)?.actor_id, null);
  const logs = f.events.map(serializeSecurityEvent).join("\n");
  const session = f.store.sessions.get(id)!;
  for (const secret of [id, f.login.state, f.login.browser, session.csrf, "access-secret", "refresh-secret",
    "subject-test", "CODE-SENTINEL", "PASSWORD-SENTINEL", "COOKIE-SENTINEL"])
    assert.ok(!logs.includes(secret), secret);
});
for (const [name, options, outcome] of [
  ["invalid signature", { invalidSignature: true }, "denied"],
  ["provider unavailable", { tokenStatus: 503 }, "unavailable"],
] as const) {
  test("callback " + name + " records unknown actor and correct outcome", async () => {
    const f = await fixture(options);
    await assert.rejects(f.service.callback(f.url, f.login.browser));
    assert.equal(f.events.at(-1)?.outcome, outcome); assert.equal(f.events.at(-1)?.actor_id, null);
    assert.equal(f.store.sessions.size, 0);
  });
}
test("session creation storage failure cannot produce confirmation", async () => {
  class FailedCreate extends MemoryStore {
    override async createSession() { throw new Error("STORAGE-SECRET"); }
  }
  const f = await fixture({}, new FailedCreate());
  await assert.rejects(f.service.callback(f.url, f.login.browser));
  assert.ok(!f.events.some((e) => e.event_type === "session.created"));
  assert.equal(f.events.at(-1)?.outcome, "unavailable");
  assert.equal(f.events.at(-1)?.reason, "storage_unavailable");
});
test("rotation observes old revocation and new creation under one correlation", async () => {
  const f = await fixture();
  const first = await f.service.callback(f.url, f.login.browser);
  const second = await f.service.start("/en");
  f.mock.setNonce(second.url.searchParams.get("nonce")!); f.url.searchParams.set("state", second.state);
  const correlation = randomUUID();
  await withCorrelation(correlation, () => f.service.callback(f.url, second.browser, first.id));
  assert.ok(!f.store.sessions.has(first.id));
  const events = f.events.filter((e) => e.correlation_id === correlation);
  assert.deepEqual(events.map((e) => e.event_type), ["session.revoked", "session.created"]);
});
for (const [mode, options, expected] of [
  ["success", {}, "session.refreshed"],
  ["invalid", { refreshStatus: 400 }, "session.refresh_failed"],
  ["temporary", { refreshStatus: 503 }, "session.refresh_failed"],
  ["expired", {}, "session.expired"],
] as const) {
  test("observable refresh/expiration " + mode, async () => {
    const f = await fixture(options);
    const { id } = await f.service.callback(f.url, f.login.browser);
    f.advance(mode === "expired" ? 28800001 : 121000);
    const correlation = randomUUID();
    await withCorrelation(correlation, () => f.service.identity(id));
    const events = f.events.filter((e) => e.correlation_id === correlation);
    assert.equal(events[0].event_type, expected); assert.equal(events[0].actor_id, f.actor);
    if (mode === "temporary") assert.equal(events[0].outcome, "unavailable");
    if (mode === "invalid") {
      assert.equal(events[0].outcome, "denied"); assert.equal(events[1].event_type, "session.revoked");
    }
    if (mode === "success") assert.equal(f.apiIds.at(-1), correlation);
  });
}
test("commit failure discards session confirmations", async () => {
  class CommitFailure extends MemoryStore {
    fail = false;
    override async withSession<T>(id: string, operation: Parameters<MemoryStore["withSession"]>[1]): Promise<T> {
      const result = await super.withSession(id, operation);
      if (this.fail) throw new Error("COMMIT-SECRET");
      return result as T;
    }
  }
  const store = new CommitFailure(), f = await fixture({}, store);
  const { id } = await f.service.callback(f.url, f.login.browser);
  f.advance(121000); store.fail = true; const before = f.events.length;
  assert.equal((await f.service.identity(id)).status, "unavailable");
  assert.deepEqual(f.events.slice(before).map((e) => e.outcome), ["unavailable"]);
  assert.ok(!f.events.slice(before).some((e) => e.event_type === "session.refreshed"));
});
test("effective logout, failed CSRF, and failed storage have distinct outcomes", async () => {
  const f = await fixture();
  const { id } = await f.service.callback(f.url, f.login.browser);
  const csrf = f.store.sessions.get(id)!.csrf;
  await assert.rejects(f.service.logout(id, randomId(), "/en"));
  assert.equal(f.events.at(-1)?.outcome, "denied"); assert.equal(f.events.at(-1)?.actor_id, null);
  const original = f.store.withSession;
  f.store.withSession = async () => { throw new Error("STORAGE-SECRET"); };
  await assert.rejects(f.service.logout(id, csrf, "/en"));
  assert.equal(f.events.at(-1)?.outcome, "unavailable");
  f.store.withSession = original;
  await f.service.logout(id, csrf, "/en");
  assert.equal(f.events.at(-1)?.event_type, "session.logout");
  assert.equal(f.events.at(-1)?.actor_id, f.actor); assert.ok(!f.store.sessions.has(id));
});
test("concurrent requests isolate correlation and emit a single committed refresh", async () => {
  const f = await fixture(); const { id } = await f.service.callback(f.url, f.login.browser);
  f.advance(121000); const ids: string[] = Array.from({ length: 8 }, () => randomUUID());
  await Promise.all(ids.map((value) => withCorrelation(value, async () => {
    assert.equal(currentCorrelation(), value);
    assert.equal((await f.service.identity(id)).status, "authenticated");
    assert.equal(currentCorrelation(), value);
  })));
  assert.deepEqual(f.apiIds, ids);
  assert.equal(f.events.filter((e) => e.event_type === "session.refreshed").length, 1);
  assert.equal(f.events.at(-1)?.correlation_id, ids[0]);
  assert.ok(!ids.includes(currentCorrelation()));
});
test("quota and malformed handlers preserve status and correlate records with responses", async () => {
  const f = await fixture();
  const request = new NextRequest(f.cfg.origin + "/oidc/login", { method: "POST", headers: {
    Origin: f.cfg.origin, Host: "localhost:3000", "Content-Type": "application/x-www-form-urlencoded",
    "X-Request-ID": "UNSAFE-SECRET", Cookie: "COOKIE-SENTINEL",
  }, body: "returnTo=%2Fen" });
  f.store.takeQuota = async () => ({ allowed: false, retryAfter: 10 });
  const response = await loginHandler(request, f.service);
  assert.equal(response.status, 429); assert.equal(response.headers.get("Retry-After"), "10");
  assert.equal(f.events.at(-1)?.event_type, "access.quota_exceeded");
  assert.equal(f.events.at(-1)?.correlation_id, response.headers.get("X-Request-ID"));
  const rejected = await callbackHandler(new NextRequest(f.cfg.redirectUri + "?code=" + "x".repeat(20000)), f.service);
  assert.equal(rejected.status, 413); assert.equal(f.events.at(-1)?.actor_id, null);
  const logout = await logoutHandler(new NextRequest(f.cfg.origin + "/oidc/logout", { method: "POST" }), f.service);
  assert.equal(logout.status, 403); assert.equal(f.events.at(-1)?.event_type, "session.logout");
});
test("admin denial retains trustworthy actor only and never renders authorized content", async () => {
  const f = await fixture(), correlation = randomUUID();
  const result = await withCorrelation(correlation, () => guardAdminContent(
    async () => ({ status: "authenticated", identity: { actor_id: f.actor, roles: [], permissions: [] }, csrf: "CSRF-SENTINEL" }),
    () => { throw new Error("Must not render"); }, () => "blocked", undefined, f.audit));
  assert.equal(result, "blocked"); assert.equal(f.events.at(-1)?.actor_id, f.actor);
  assert.equal(f.events.at(-1)?.correlation_id, correlation);
  assert.ok(!f.events.map(serializeSecurityEvent).join("").includes("CSRF-SENTINEL"));
});
test("audit sink failure preserves session creation and rejected callback", async () => {
  const f = await fixture(), warnings: string[] = [], previous = console.warn;
  const audit = new SecurityAudit({ emit() { throw new Error("SINK-SECRET"); } });
  const service = new AuthService(f.cfg, f.store, new OpenIdProvider(f.cfg, f.mock.transport), Date.now, undefined, audit);
  console.warn = (message: string) => { warnings.push(message); };
  try {
    const result = await service.callback(f.url, f.login.browser); assert.ok(f.store.sessions.has(result.id));
    await assert.rejects(service.callback(f.url, f.login.browser));
  } finally { console.warn = previous; }
  assert.deepEqual(warnings, ["security_audit_sink_unavailable", "security_audit_sink_unavailable"]);
});
test("proxy replaces client correlation before SSR and includes ID on failure", () => {
  const request = new NextRequest("http://localhost:3000/en", { headers: { "X-Request-ID": "SECRET-ID" } });
  const response = secureProxy(request, { WEB_AUTH_ENV: "local", WEB_ORIGIN: "http://localhost:3000" });
  const id = response.headers.get("X-Request-ID"); assert.match(id!, /^[0-9a-f-]{36}$/);
  assert.equal(response.headers.get("x-middleware-request-x-request-id"), id);
  assert.match(secureProxy(request, {}).headers.get("X-Request-ID")!, /^[0-9a-f-]{36}$/);
});

test("actual BFF native output excludes tokens, subject and opaque session credentials", async () => {
  const f = await fixture(), lines: string[] = [], previous = console.info;
  const service = new AuthService(f.cfg, f.store, new OpenIdProvider(f.cfg, f.mock.transport));
  console.info = (line: string) => { lines.push(line); };
  let id = "";
  try {
    ({ id } = await service.callback(f.url, f.login.browser));
    const csrf = f.store.sessions.get(id)!.csrf;
    await service.logout(id, csrf, "/en");
    await assert.rejects(service.callback(f.url, f.login.browser));
  } finally { console.info = previous; }
  const logs = lines.join("\n");
  for (const secret of [id, f.login.state, f.login.browser, "access-secret", "refresh-secret", "subject-test", "CODE-SENTINEL"])
    assert.ok(!logs.includes(secret));
  assert.deepEqual(lines.map((line) => JSON.parse(line).event_type), ["session.created", "session.logout", "authentication.failed"]);
});
for (const status of ["forbidden", "anonymous", "expired", "unavailable"] as const) {
  test("admin " + status + " records unknown actor without access", async () => {
    const events: SecurityEvent[] = [], audit = new SecurityAudit({ emit(event) { events.push(event); } });
    const result = await guardAdminContent(async () => ({ status }), () => "allowed", () => "blocked", undefined, audit);
    assert.equal(result, "blocked"); assert.equal(events[0].actor_id, null);
    assert.equal(events[0].outcome, status === "unavailable" ? "unavailable" : "denied");
  });
}

test("uncertain network refresh is an operational error while revocation commits", async () => {
  const f = await fixture(), { id } = await f.service.callback(f.url, f.login.browser);
  f.service.provider.refresh = async () => { throw new TypeError("NETWORK-SECRET"); };
  f.advance(121000); const before = f.events.length;
  assert.equal((await f.service.identity(id)).status, "expired");
  const events = f.events.slice(before);
  assert.equal(events[0].event_type, "session.refresh_failed"); assert.equal(events[0].outcome, "error");
  assert.equal(events[1].event_type, "session.revoked"); assert.equal(events[1].outcome, "success");
  assert.ok(!f.store.sessions.has(id));
  assert.ok(!events.map(serializeSecurityEvent).join("").includes("NETWORK-SECRET"));
});
