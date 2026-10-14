import assert from "node:assert/strict";
import { test } from "node:test";
import { execFile, spawn, type ChildProcess } from "node:child_process";
import { promisify } from "node:util";
import { randomBytes } from "node:crypto";
import { createServer } from "node:http";
import { migrateDatabase } from "./migrations";
import { setTimeout as delay } from "node:timers/promises";
import { Pool } from "pg";
import { TokenCipher } from "../src/server/auth/crypto";
import { parseSession } from "../src/server/auth/store";
import { probeBrowser } from "./browser";

async function freePort(): Promise<number> {
  const server = createServer();
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  const port = address.port;
  await new Promise<void>((resolve) => server.close(() => resolve()));
  return port;
}
async function stop(child: ChildProcess | undefined) {
  if (!child || child.exitCode !== null) return;
  child.kill("SIGTERM");
  await new Promise<void>((resolve) => child.once("exit", () => resolve()));
}
async function ready(url: string) {
  for (let count = 0; count < 1200; count++) {
    try { if ((await fetch(url, { signal: AbortSignal.timeout(1000) })).ok) return; } catch { /* startup only */ }
    await delay(100);
  }
  throw new Error("Isolated server did not become ready");
}
test("real isolated Keycloak -> built Next BFF -> PostgreSQL -> FastAPI; refresh, replay and local/RP logout", {
  skip: process.env.TEST_KEYCLOAK_WEB_ENABLED !== "1" ? "Real web Keycloak explicitly opt-in" : false,
}, async () => {
  assert.equal(process.env.TEST_WEB_ISOLATED, "1");
  const issuer = process.env.TEST_KEYCLOAK_WEB_ISSUER!;
  const origin = process.env.TEST_KEYCLOAK_WEB_ORIGIN!;
  const connection = process.env.TEST_KEYCLOAK_WEB_DATABASE_URL!;
  const username = process.env.TEST_KEYCLOAK_ADMIN_USERNAME!;
  const password = process.env.TEST_KEYCLOAK_ADMIN_PASSWORD!;
  assert.ok(issuer && origin && connection && username && password);
  assert.notEqual(connection, process.env.WEB_SESSION_DATABASE_URL);
  assert.ok(["localhost", "127.0.0.1"].includes(new URL(issuer).hostname));
  assert.equal(new URL(origin).hostname, "127.0.0.1");
  const pool = new Pool({ connectionString: connection });
  let userId: string | undefined, adminToken: string | undefined;
  let api: ChildProcess | undefined, web: ChildProcess | undefined;
  let logs = "";
  const webKey = randomBytes(32);
  const cipher = new TokenCipher({ activeKey: "real", keys: new Map([["real", webKey]]) });
  const account = "m0403-web-" + randomBytes(12).toString("hex");
  const accountPassword = randomBytes(32).toString("base64url");
  const adminBase = issuer.replace("/realms/libris", "/admin/realms/libris");
  const adminHeaders = () => ({ Authorization: `Bearer ${adminToken}`, "Content-Type": "application/json" });
  const cookies = (response: Response) => response.headers.getSetCookie().map((item) => item.split(";")[0]).join("; ");
  const fetchWeb = (path: string, init?: RequestInit) => fetch(origin + path, { ...init, redirect: "manual" });
  try {
    assert.equal((await pool.query("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")).rows[0].count, "0");
    await migrateDatabase(connection);
    await ready(issuer + "/.well-known/openid-configuration");
    const admin = await fetch(issuer.replace("/libris", "/master") + "/protocol/openid-connect/token", {
      method: "POST", body: new URLSearchParams({ client_id: "admin-cli", grant_type: "password", username, password }),
    });
    assert.equal(admin.status, 200, "Temporary administrator authentication");
    const tokens = await admin.json() as { access_token: string };
    adminToken = tokens.access_token;
    // This opt-in harness is exclusively for disposable realms: short access TTL
    // and rotation with no reuse make the real refresh assertion meaningful.
    assert.equal((await fetch(adminBase, { method: "PUT", headers: adminHeaders(),
      body: JSON.stringify({ accessTokenLifespan: 40, revokeRefreshToken: true, refreshTokenMaxReuse: 0 }),
    })).status, 204);
    const user = await fetch(adminBase + "/users", { method: "POST", headers: adminHeaders(), body: JSON.stringify({
      username: account, enabled: true, firstName: "Synthetic", lastName: "Probe", email: account + "@example.invalid",
      emailVerified: true, requiredActions: [], credentials: [{ type: "password", value: accountPassword, temporary: false }],
    }) });
    assert.equal(user.status, 201, "Create owned temporary user");
    userId = user.headers.get("location")!.split("/").at(-1)!;
    const clients = await (await fetch(adminBase + "/clients?clientId=libris-api", { headers: adminHeaders() })).json() as { id: string }[];
    assert.equal(clients.length, 1);
    const role = await (await fetch(adminBase + "/clients/" + clients[0].id + "/roles/libris-reader", { headers: adminHeaders() })).json() as unknown;
    assert.equal((await fetch(adminBase + "/users/" + userId + "/role-mappings/clients/" + clients[0].id, {
      method: "POST", headers: adminHeaders(), body: JSON.stringify([role]),
    })).status, 204);
    const apiPort = await freePort(), apiUrl = `http://127.0.0.1:${apiPort}`;
    api = spawn(new URL("../../api/.venv/bin/python", import.meta.url).pathname, [
      "-m", "uvicorn", "libris.main:app", "--host", "127.0.0.1", "--port", String(apiPort), "--no-access-log",
    ], { cwd: new URL("../../api", import.meta.url), env: { ...process.env, APP_ENV: "development",
      DATABASE_URL: connection.replace(/^postgres(?:ql)?:/, "postgresql+asyncpg:"),
      OIDC_ENABLED: "true", OIDC_ISSUER_URL: issuer, OIDC_AUDIENCE: "libris-api",
    }, stdio: ["ignore", "pipe", "pipe"] });
    api.stdout?.on("data", (data: Buffer) => { logs += data.toString(); });
    api.stderr?.on("data", (data: Buffer) => { logs += data.toString(); });
    await ready(apiUrl + "/health");
    assert.equal((await fetch(apiUrl + "/api/v1/identity/me")).status, 401);
    web = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1",
      "--port", new URL(origin).port], { cwd: new URL("..", import.meta.url), env: { ...process.env,
      WEB_AUTH_ENV: "local", WEB_ORIGIN: origin, WEB_OIDC_ISSUER: issuer, WEB_OIDC_CLIENT_ID: "libris-web",
      WEB_SESSION_DATABASE_URL: connection, WEB_SESSION_ACTIVE_KEY: "real",
      WEB_SESSION_KEYS: JSON.stringify({ real: webKey.toString("base64") }), API_INTERNAL_URL: apiUrl,
    }, stdio: ["ignore", "pipe", "pipe"] });
    web.stdout?.on("data", (data: Buffer) => { logs += data.toString(); });
    web.stderr?.on("data", (data: Buffer) => { logs += data.toString(); });
    await ready(origin + "/en");
    const login = await fetchWeb("/oidc/login", { method: "POST", headers: { Origin: origin },
      body: new URLSearchParams({ returnTo: "/en?view=original" }) });
    assert.equal(login.status, 303);
    const authorization = login.headers.get("location")!;
    assert.equal(new URL(authorization).searchParams.get("code_challenge_method"), "S256");
    const providerLogin = await fetch(authorization, { redirect: "manual" });
    assert.equal(providerLogin.status, 200);
    const html = await providerLogin.text();
    const action = html.match(/<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"/)?.[1]?.replaceAll("&amp;", "&");
    assert.ok(action, "Trusted Keycloak login form");
    assert.equal(new URL(action).origin, new URL(issuer).origin);
    // HTTP harness uses only cookies from this isolated provider in memory.
    // This does not alter product/browser cookie handling.
    const providerResponse = await fetch(action, { method: "POST", redirect: "manual", headers: {
      Cookie: cookies(providerLogin) }, body: new URLSearchParams({ username: account, password: accountPassword, credentialId: "" }),
    });
    assert.equal(providerResponse.status, 302, "Real provider login callback");
    const callback = new URL(providerResponse.headers.get("location")!);
    assert.equal(callback.origin, origin);
    assert.equal(callback.pathname, "/oidc/callback");
    const response = await fetchWeb(callback.pathname + callback.search, { headers: { Cookie: cookies(login) } });
    assert.equal(response.status, 303);
    assert.equal(response.headers.get("location"), origin + "/en?view=original");
    const session = cookies(response).split("; ").find((item) => item.startsWith("libris-session="))!;
    assert.ok(session, "Opaque application session created");
    const authenticated = await (await fetchWeb("/en", { headers: { Cookie: session } })).text();
    assert.match(authenticated, /Authenticated session/);
    assert.match(authenticated, /libris-reader/);
    assert.match(authenticated, /bibliographic:read/);
    assert.doesNotMatch(authenticated, /access_token|refresh_token|id_token/);
    assert.ok(!authenticated.includes(accountPassword));
    const csrf = authenticated.match(/name="csrf" value="([^"]+)"/)?.[1];
    assert.ok(csrf);
    assert.equal((await fetchWeb(callback.pathname + callback.search, { headers: { Cookie: cookies(login) } })).headers.get("location"),
      origin + "/pt?auth=error");
    // Private test realm has short access lifespan. Wait until the BFF's 30-second
    // refresh margin is reached. No tokens are decoded/exposed by this harness.
    const beforeRow = (await pool.query("SELECT id_hash,payload FROM libris_web.sessions")).rows[0] as { id_hash: string; payload: string };
    const beforeRefresh = beforeRow.payload;
    const beforeTokens = parseSession(cipher.open(beforeRefresh, `session:${beforeRow.id_hash}`));
    await delay(12000);
    const refreshResponse = await fetchWeb("/en", { headers: { Cookie: session, "X-Request-ID": "untrusted-sentinel" } });
    const correlation = refreshResponse.headers.get("x-request-id");
    assert.match(correlation ?? "", /^[0-9a-f-]{36}$/);
    const refreshed = await refreshResponse.text();
    assert.match(refreshed, /Authenticated session/);
    const loginPayload = (await pool.query("SELECT payload FROM libris_web.sessions")).rows[0].payload as string;
    await delay(100);
    const correlated = logs.split("\n").filter((line) => line.includes(correlation!));
    assert.ok(correlated.some((line) => line.includes('"component":"api"') && line.includes("authentication.succeeded")),
      "Real API authentication preserves SSR correlation");
    assert.ok(correlated.some((line) => line.includes('"component":"bff"') && line.includes("session.refreshed")),
      "Committed BFF refresh shares API correlation");
    assert.ok(!logs.includes("untrusted-sentinel"));
    assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions")).rows[0].count, "1");
    assert.notEqual(loginPayload, beforeRefresh, "Real refresh persisted new encrypted tokens");
    const afterTokens = parseSession(cipher.open(loginPayload, `session:${beforeRow.id_hash}`));
    assert.ok(afterTokens.refreshToken !== beforeTokens.refreshToken, "Real provider rotated refresh token");
    assert.ok(afterTokens.accessToken !== beforeTokens.accessToken, "Real provider issued fresh access token");
    assert.ok(!logs.includes(afterTokens.accessToken) && !logs.includes(afterTokens.refreshToken!));
    assert.equal((await fetchWeb("/oidc/logout", { method: "POST", headers: { Origin: "https://evil.invalid", Cookie: session },
      body: new URLSearchParams({ csrf, returnTo: "/en" }) })).status, 403);
    const logout = await fetchWeb("/oidc/logout", { method: "POST", headers: { Origin: origin, Cookie: session },
      body: new URLSearchParams({ csrf, returnTo: "/en" }) });
    assert.equal(logout.status, 303);
    const logoutUrl = new URL(logout.headers.get("location")!);
    assert.equal(logoutUrl.pathname, "/realms/libris/protocol/openid-connect/logout");
    assert.equal(logoutUrl.searchParams.get("id_token_hint"), null);
    assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions")).rows[0].count, "0");
    assert.match(await (await fetchWeb("/en", { headers: { Cookie: session } })).text(), /session expired/);
    const confirmation = await fetch(logoutUrl, { redirect: "manual", headers: { Cookie: cookies(providerResponse) } });
    assert.ok([200, 302, 303].includes(confirmation.status), "RP logout reached provider");
    assert.ok(!logs.includes(accountPassword) && !logs.includes(adminToken));
    if (process.env.TEST_WEB_BROWSER_ENABLED === "1") {
      // Reader authenticates but cannot enter the administrative shell.
      await probeBrowser(origin, "", { username: account, password: accountPassword, issuer, authorized: false });
      const cataloger = await (await fetch(adminBase + "/clients/" + clients[0].id + "/roles/libris-cataloger", {
        headers: adminHeaders(),
      })).json() as unknown;
      assert.equal((await fetch(adminBase + "/users/" + userId + "/role-mappings/clients/" + clients[0].id, {
        method: "POST", headers: adminHeaders(), body: JSON.stringify([cataloger]),
      })).status, 204);
      await probeBrowser(origin, "", { username: account, password: accountPassword, issuer, authorized: true });
      await probeBrowser(origin, "", { username: account, password: accountPassword, issuer, authorized: true,
        expireSession: async () => {
          const row = (await pool.query("SELECT id_hash,payload FROM libris_web.sessions")).rows[0] as { id_hash: string; payload: string };
          const value = parseSession(cipher.open(row.payload, `session:${row.id_hash}`));
          await pool.query("UPDATE libris_web.sessions SET payload = $1, expires_at = 1 WHERE id_hash = $2", [
            cipher.seal({ ...value, expiresAt: 1 }, `session:${row.id_hash}`), row.id_hash,
          ]);
        },
      });
      const container = process.env.TEST_KEYCLOAK_CONTAINER;
      if (container) {
        assert.match(container, /^libris-m0409-[0-9a-f]{16}-kc$/);
        const docker = promisify(execFile);
        const owner = (await docker("docker", ["inspect", "--format", '{{index .Config.Labels "libris.verification"}}', container])).stdout.trim();
        assert.equal(owner + "-kc", container, "Only the runner-owned disposable provider may be paused");
        await probeBrowser(origin, "", { username: account, password: accountPassword, issuer, authorized: true,
          providerUnavailable: async () => {
            const row = (await pool.query("SELECT id_hash,payload FROM libris_web.sessions")).rows[0] as { id_hash: string; payload: string };
            const value = parseSession(cipher.open(row.payload, `session:${row.id_hash}`));
            await pool.query("UPDATE libris_web.sessions SET payload = $1 WHERE id_hash = $2", [
              cipher.seal({ ...value, accessExpiresAt: 1 }, `session:${row.id_hash}`), row.id_hash,
            ]);
            await docker("docker", ["pause", container]);
            return async () => { await docker("docker", ["unpause", container]); };
          },
        });
      }
      assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions")).rows[0].count, "0");
    }
  } finally {
    await stop(web); await stop(api);
    if (userId && adminToken) assert.equal((await fetch(adminBase + "/users/" + userId, { method: "DELETE", headers: adminHeaders() })).status, 204);
    await pool.end();
  }
});
