import assert from "node:assert/strict";
import { test } from "node:test";
import { spawn, type ChildProcess } from "node:child_process";
import { createServer, type Server } from "node:http";
import { migrateDatabase } from "./migrations";
import { randomBytes } from "node:crypto";
import { setTimeout as delay } from "node:timers/promises";
import { Pool } from "pg";
import { jwt, jwk } from "./helpers";
import { readConfig } from "../src/server/auth/config";
import { PostgresAuthStore } from "../src/server/auth/store";
import { randomId } from "../src/server/auth/security";

async function listen(server: Server): Promise<number> {
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  return address.port;
}
async function freePort() {
  const server = createServer(); const port = await listen(server);
  await new Promise<void>((resolve) => server.close(() => resolve()));
  return port;
}
async function stop(child: ChildProcess | undefined) {
  if (!child || child.exitCode !== null) return;
  child.kill("SIGTERM");
  await new Promise<void>((resolve) => child.once("exit", () => resolve()));
}
async function ready(url: string, child: ChildProcess) {
  for (let attempt = 0; attempt < 200; attempt++) {
    try { if ((await fetch(url, { signal: AbortSignal.timeout(1000) })).ok) return; } catch { /* startup */ }
    if (child.exitCode !== null) break;
    await delay(100);
  }
  throw new Error("Test server did not start");
}

test("admin SSR -> encrypted PostgreSQL session -> real FastAPI JWT/JWKS/RBAC; simulated issuer, not Keycloak", {
  skip: !process.env.TEST_ADMIN_API_DATABASE_URL ? "Isolated admin/API database absent: real FastAPI chain not verified" : false,
}, async () => {
  assert.equal(process.env.TEST_WEB_ISOLATED, "1");
  const connection = process.env.TEST_ADMIN_API_DATABASE_URL!;
  assert.notEqual(connection, process.env.WEB_SESSION_DATABASE_URL);
  assert.notEqual(connection, process.env.TEST_WEB_HTTP_DATABASE_URL);
  const pool = new Pool({ connectionString: connection });
  let issuer = "", logs = "";
  let api: ChildProcess | undefined, web: ChildProcess | undefined;
  const issuedTokens: string[] = [];
  let authorizedId = "";
  const upstream = createServer((request, response) => {
    response.setHeader("Content-Type", "application/json");
    if (request.url?.endsWith("openid-configuration")) return response.end(JSON.stringify({ issuer, jwks_uri: issuer + "/jwks" }));
    if (request.url === "/jwks") return response.end(JSON.stringify({ keys: [jwk] }));
    response.statusCode = 404; response.end("{}");
  });
  issuer = `http://127.0.0.1:${await listen(upstream)}`;
  const apiPort = await freePort(), apiUrl = `http://127.0.0.1:${apiPort}`;
  const webPort = await freePort(), origin = `http://127.0.0.1:${webPort}`;
  const env = { ...process.env, WEB_AUTH_ENV: "local", WEB_ORIGIN: origin, WEB_OIDC_ISSUER: issuer,
    WEB_OIDC_CLIENT_ID: "libris-web", WEB_SESSION_DATABASE_URL: connection,
    WEB_SESSION_KEYS: JSON.stringify({ admin: randomBytes(32).toString("base64") }), WEB_SESSION_ACTIVE_KEY: "admin", API_INTERNAL_URL: apiUrl };
  const store = new PostgresAuthStore(pool, readConfig(env));
  const capture = (child: ChildProcess) => {
    child.stdout?.on("data", (data: Buffer) => { logs += data.toString(); });
    child.stderr?.on("data", (data: Buffer) => { logs += data.toString(); });
  };
  const fetchWeb = (path: string, cookie = "") => fetch(origin + path, {
    headers: { Cookie: cookie, "X-Permissions": "system:admin", "X-Actor-Id": "forged" }, redirect: "manual",
  });
  try {
    assert.equal((await pool.query("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")).rows[0].count, "0");
    await migrateDatabase(connection);
    api = spawn(new URL("../../api/.venv/bin/python", import.meta.url).pathname, [
      "-m", "uvicorn", "libris.main:app", "--host", "127.0.0.1", "--port", String(apiPort), "--no-access-log",
    ], { cwd: new URL("../../api", import.meta.url), env: { ...process.env, APP_ENV: "development",
      DATABASE_URL: connection.replace(/^postgres(?:ql)?:/, "postgresql+asyncpg:"), OIDC_ENABLED: "true",
      OIDC_ISSUER_URL: issuer, OIDC_AUDIENCE: "libris-api", OIDC_ROLE_SOURCE: "client", OIDC_ROLE_CLIENT: "libris-api",
    }, stdio: ["ignore", "pipe", "pipe"] });
    capture(api); await ready(apiUrl + "/health", api);
    assert.equal((await fetch(apiUrl + "/api/v1/identity/me")).status, 401);
    web = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", String(webPort)], {
      cwd: new URL("..", import.meta.url), env, stdio: ["ignore", "pipe", "pipe"],
    });
    capture(web); await ready(origin + "/en", web);
    for (const [role, expected, absent] of [
      ["libris-reader", undefined, "cataloging"],
      ["unknown-admin", undefined, "system"],
      ["libris-cataloger", "cataloging", "authorities"],
      ["libris-authority-manager", "authorities", "cataloging"],
      ["libris-reviewer", "editorial", "system"],
      ["libris-publisher", "editorial", "cataloging"],
      ["libris-admin", "system", undefined],
    ] as const) {
      const now = Math.floor(Date.now() / 1000);
      const accessToken = jwt({ iss: issuer, aud: "libris-api", sub: "synthetic-admin-probe", azp: "libris-web", typ: "Bearer", iat: now, exp: now + 300,
        resource_access: { "libris-api": { roles: [role] } } });
      issuedTokens.push(accessToken);
      const id = randomId();
      if (expected) authorizedId = id;
      await store.createSession(id, { accessToken, accessExpiresAt: Date.now() + 300000, expiresAt: Date.now() + 300000,
        subject: "synthetic-admin-probe", csrf: randomId() });
      for (const locale of ["pt", "en"]) {
        const response = await fetchWeb(`/${locale}/admin?permissions=system:admin&roles=libris-admin`, `libris-session=${id}`);
        assert.equal(response.status, 200);
        assert.match(response.headers.get("Cache-Control")!, /private.*no-store|no-store.*private/);
        assert.equal(response.headers.get("Referrer-Policy"), "same-origin");
        const html = await response.text();
        assert.doesNotMatch(html, /synthetic-admin-probe|forged/); assert.ok(!html.includes(accessToken));
        if (expected) assert.match(html, new RegExp(`id="${expected}"`));
        else {
          assert.match(html, locale === "pt" ? /Acesso não autorizado/ : /Access denied/);
          assert.doesNotMatch(html, /id="capabilities-title"/);
        }
        if (absent) assert.doesNotMatch(html, new RegExp(`id="${absent}"`));
      }
      assert.equal((await store.withSession(id, async (handle) => handle.value !== null)), true);
    }
    const invalidId = randomId();
    await store.createSession(invalidId, { accessToken: "invalid-signature", accessExpiresAt: Date.now() + 300000,
      expiresAt: Date.now() + 300000, subject: "test", csrf: randomId() });
    assert.match(await (await fetchWeb("/en/admin", `libris-session=${invalidId}`)).text(), /Session expired/);
    assert.equal(await store.withSession(invalidId, async (handle) => handle.value), null);
    await stop(api); api = undefined;
    const response = await fetchWeb("/en/admin", `libris-session=${authorizedId}`);
    const unavailableHtml = await response.text();
    assert.match(unavailableHtml, /Service unavailable/);
    assert.doesNotMatch(unavailableHtml, /id="capabilities-title"/);
    assert.ok(issuedTokens.every((token) => !logs.includes(token)), "Logs leaked an access token");
  } finally {
    await stop(web); await stop(api);
    await new Promise<void>((resolve) => upstream.close(() => resolve()));
    await pool.end();
  }
});
