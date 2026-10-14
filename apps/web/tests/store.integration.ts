import assert from "node:assert/strict";
import { test } from "node:test";
import { migrateDatabase } from "./migrations";
import { Pool } from "pg";
import { config, json } from "./helpers";
import { PostgresAuthStore, type Session } from "../src/server/auth/store";
import { SecurityAudit, serializeSecurityEvent, type SecurityEvent } from "../src/server/security-audit";
import { AuthService } from "../src/server/auth/service";
import type { OidcProvider } from "../src/server/auth/oidc";
import { digest, randomId } from "../src/server/auth/security";

test("isolated PostgreSQL: explicit migration, encryption, atomic transactions, refresh/logout across workers", {
  skip: !process.env.TEST_WEB_DATABASE_URL ? "TEST_WEB_DATABASE_URL missing: no persistence evidence" : false,
}, async () => {
  assert.equal(process.env.TEST_WEB_ISOLATED, "1", "Dedicated disposable database required");
  assert.notEqual(process.env.TEST_WEB_DATABASE_URL, process.env.WEB_SESSION_DATABASE_URL);
  const connectionString = process.env.TEST_WEB_DATABASE_URL!;
  assert.ok(["postgres:", "postgresql:"].includes(new URL(connectionString).protocol));
  const pool = new Pool({ connectionString, max: 8 });
  const cfg = { ...config(), databaseUrl: connectionString };
  try {
    assert.equal((await pool.query("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")).rows[0].count, "0",
      "Database must start empty; never touch working data");
    await pool.query("CREATE TABLE public.legacy_probe (value text); INSERT INTO public.legacy_probe VALUES ('preserved')");
    await migrateDatabase(connectionString);
    const first = new PostgresAuthStore(pool, cfg), second = new PostgresAuthStore(pool, cfg);
    const state = randomId(), browser = randomId(), transaction = { verifier: randomId(), nonce: randomId(), returnTo: "/en?original=1" };
    await first.putTransaction(state, browser, transaction, Date.now() + 300000);
    assert.equal(await second.consumeTransaction(state, randomId(), Date.now()), null);
    const persisted = await pool.query("SELECT * FROM libris_web.auth_transactions");
    assert.equal(persisted.rows[0].state_hash, digest(state));
    assert.ok(!JSON.stringify(persisted.rows).includes(transaction.verifier));
    const outcomes = await Promise.all(Array.from({ length: 8 }, (_, i) => (i % 2 ? first : second)
      .consumeTransaction(state, browser, Date.now())));
    assert.equal(outcomes.filter(Boolean).length, 1);
    await first.putTransaction(state, browser, transaction, 1);
    assert.equal(await second.consumeTransaction(state, browser, Date.now()), null);
    await pool.query("DELETE FROM libris_web.auth_transactions WHERE expires_at < $1", [Date.now()]);
    const id = randomId(), now = Date.now();
    const session: Session = { accessToken: "expired-secret-access", accessExpiresAt: now - 1,
      refreshToken: "original-secret-refresh", refreshExpiresAt: now + 3600000,
      subject: "test-subject", csrf: randomId(), expiresAt: now + 3600000 };
    await first.createSession(id, session);
    const rows = await pool.query("SELECT * FROM libris_web.sessions");
    assert.equal(rows.rows[0].id_hash, digest(id));
    assert.ok(!JSON.stringify(rows.rows).includes(session.accessToken));
    assert.ok(!JSON.stringify(rows.rows).includes(session.refreshToken!));
    let refreshes = 0;
    const provider: OidcProvider = {
      authorize: async () => { throw new Error("Unused"); },
      exchange: async () => { throw new Error("Unused"); },
      refresh: async (current) => {
        refreshes++;
        assert.equal(current.refreshToken, "original-secret-refresh");
        return { ...current, accessToken: "fresh-secret-access", refreshToken: "rotated-secret-refresh", accessExpiresAt: Date.now() + 120000 };
      },
      logout: async () => { throw new Error("Provider offline"); },
    };
    const api = async (_url: string | URL, init?: RequestInit) => {
      assert.equal(new Headers(init?.headers).get("Authorization"), "Bearer fresh-secret-access");
      return json({ actor_id: "oidc:sha256:test", roles: [], permissions: [] });
    };
    const events: SecurityEvent[] = [];
    const audit = new SecurityAudit({ emit(event) { events.push(event); } });
    const a = new AuthService(cfg, first, provider, Date.now, api, audit), b = new AuthService(cfg, second, provider, Date.now, api, audit);
    const results = await Promise.all(Array.from({ length: 10 }, (_, i) => (i % 2 ? a : b).identity(id)));
    assert.ok(results.every((result) => result.status === "authenticated"));
    assert.equal(refreshes, 1);
    assert.equal(events.filter((event) => event.event_type === "session.refreshed").length, 1);
    const fresh = await second.withSession(id, async (handle) => handle.value);
    assert.equal(fresh?.refreshToken, "rotated-secret-refresh");
    // Rollback does not accidentally commit revocation.
    await assert.rejects(first.withSession(id, async (handle) => { await handle.revoke(); throw new Error("rollback"); }));
    assert.ok(await second.withSession(id, async (handle) => handle.value));
    // Hold an API call, issue logout concurrently on another store, then release:
    // logout commits after the active request, and no later request can reuse it.
    let entered!: () => void, release!: () => void;
    const inside = new Promise<void>((resolve) => { entered = resolve; });
    const released = new Promise<void>((resolve) => { release = resolve; });
    const slow = new AuthService(cfg, first, provider, Date.now, async (...args) => { entered(); await released; return api(args[0], args[1]); });
    const request = slow.identity(id);
    await inside;
    const logout = b.logout(id, session.csrf, "/en");
    release();
    assert.equal((await request).status, "authenticated");
    assert.equal((await logout).href, cfg.origin + "/en"); // local logout survives provider outage
    assert.equal((await a.identity(id)).status, "expired");
    assert.equal((await b.identity(id)).status, "expired");
    await assert.rejects(a.logout(id, session.csrf, "/en"));
    const confirmedLogout = events.filter((event) => event.event_type === "session.logout" && event.outcome === "success");
    assert.equal(confirmedLogout.length, 1);
    assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions WHERE id_hash=$1", [digest(id)])).rows[0].count, "0");
    const logs = events.map(serializeSecurityEvent).join("\n");
    for (const secret of [id, session.csrf, session.subject, session.accessToken, session.refreshToken!])
      assert.ok(!logs.includes(secret));
    // Ciphertext corruption/deleted keys fail closed and remove unusable sessions.
    await first.createSession(id, session);
    await pool.query("UPDATE libris_web.sessions SET payload='corrupt'");
    assert.equal(await second.withSession(id, async (handle) => handle.value), null);
    assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions")).rows[0].count, "0");
    // Independent pools model replicas, with PostgreSQL clock/atomic row updates.
    const otherPool = new Pool({ connectionString, max: 4 });
    try {
      const replica = new PostgresAuthStore(otherPool, cfg);
      const policy = { windowSeconds: 60, limits: { login: 5, callback: 10, logout: 10 } };
      const quotas = await Promise.all(Array.from({ length: 20 }, (_, i) =>
        (i % 2 ? first : replica).takeQuota("login", policy)));
      assert.equal(quotas.filter((q) => q.allowed).length, 5);
      assert.ok(quotas.every((q) => q.retryAfter > 0 && q.retryAfter <= 60));
      assert.equal((await replica.takeQuota("callback", policy)).allowed, true);
      // Advance persisted window explicitly; no wall-clock sleeps.
      await pool.query("UPDATE libris_web.auth_quotas SET window_started=statement_timestamp()-interval '61 seconds' WHERE route='login'");
      assert.equal((await replica.takeQuota("login", policy)).allowed, true);
      await first.createSession(id, session);
      await pool.query("ALTER TABLE libris_web.auth_quotas RENAME TO unavailable_auth_quotas");
      assert.ok(await replica.withSession(id, async (handle) => handle.value));
      await assert.rejects(replica.takeQuota("login", policy));
      assert.equal((await pool.query("SELECT value FROM public.legacy_probe")).rows[0].value, "preserved");
      await pool.query("ALTER TABLE libris_web.unavailable_auth_quotas RENAME TO auth_quotas");
      assert.equal((await replica.takeQuota("login", policy)).allowed, true);
    } finally { await otherPool.end(); }
    await migrateDatabase(connectionString); // Alembic head is idempotent.
    assert.equal((await pool.query("SELECT value FROM public.legacy_probe")).rows[0].value, "preserved");
  } finally { await pool.end(); }
});
