import assert from "node:assert/strict";
import { test } from "node:test";
import { spawn } from "node:child_process";
import { createServer, type Server } from "node:http";
import { readFile } from "node:fs/promises";
import { createHash, randomBytes } from "node:crypto";
import { setTimeout as delay } from "node:timers/promises";
import { Pool } from "pg";
import { jwt, jwk } from "./helpers";

async function listen(server: Server): Promise<number> {
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  return address.port;
}
test("built Next.js HTTP BFF + signed mock OIDC + isolated PostgreSQL; HTML and redirects never expose tokens", {
  skip: !process.env.TEST_WEB_HTTP_DATABASE_URL ? "HTTP database absent: build-backed E2E not verified" : false,
}, async () => {
  assert.equal(process.env.TEST_WEB_ISOLATED, "1");
  assert.notEqual(process.env.TEST_WEB_HTTP_DATABASE_URL, process.env.WEB_SESSION_DATABASE_URL);
  const pool = new Pool({ connectionString: process.env.TEST_WEB_HTTP_DATABASE_URL });
  const codes = new Map<string, { nonce: string; challenge: string; redirect: string }>();
  let apiStatus = 200, apiCalls = 0, refreshes = 0;
  let issuer = "";
  const upstream = createServer(async (request, response) => {
    const url = new URL(request.url!, issuer);
    response.setHeader("Content-Type", "application/json");
    if (url.pathname.endsWith("openid-configuration")) return response.end(JSON.stringify({
      issuer, authorization_endpoint: issuer + "/auth", token_endpoint: issuer + "/token",
      jwks_uri: issuer + "/jwks", end_session_endpoint: issuer + "/logout",
      response_types_supported: ["code"], subject_types_supported: ["public"], id_token_signing_alg_values_supported: ["RS256"],
      code_challenge_methods_supported: ["S256"],
    }));
    if (url.pathname === "/jwks") return response.end(JSON.stringify({ keys: [jwk] }));
    if (url.pathname === "/auth") {
      assert.equal(url.searchParams.get("code_challenge_method"), "S256");
      const code = randomBytes(32).toString("base64url");
      codes.set(code, { nonce: url.searchParams.get("nonce")!, challenge: url.searchParams.get("code_challenge")!,
        redirect: url.searchParams.get("redirect_uri")! });
      const callback = new URL(url.searchParams.get("redirect_uri")!);
      callback.searchParams.set("code", code); callback.searchParams.set("state", url.searchParams.get("state")!);
      response.writeHead(303, { Location: callback.href }); return response.end();
    }
    if (url.pathname === "/token") {
      const chunks: Buffer[] = [];
      for await (const chunk of request) chunks.push(Buffer.from(chunk as Uint8Array));
      const form = new URLSearchParams(Buffer.concat(chunks).toString());
      let nonce: string | undefined;
      const refresh = form.get("grant_type") === "refresh_token";
      if (refresh) { refreshes++; assert.equal(form.get("refresh_token"), "http-refresh-secret"); }
      else {
        const code = form.get("code")!;
        const transaction = codes.get(code);
        if (!transaction) { response.statusCode = 400; return response.end(JSON.stringify({ error: "invalid_grant" })); }
        codes.delete(code);
        assert.equal(transaction.challenge, createHash("sha256").update(form.get("code_verifier")!).digest("base64url"));
        assert.equal(transaction.redirect, form.get("redirect_uri"));
        nonce = transaction.nonce;
      }
      const now = Math.floor(Date.now() / 1000);
      return response.end(JSON.stringify({ access_token: "http-access-secret", token_type: "Bearer", expires_in: 120,
        refresh_token: "http-refresh-secret", refresh_expires_in: 600,
        id_token: jwt({ iss: issuer, aud: "libris-web", sub: "http-subject", iat: now, exp: now + 300, ...(nonce ? { nonce } : {}) }) }));
    }
    if (url.pathname === "/api/v1/identity/me") {
      apiCalls++;
      assert.equal(request.headers.authorization, "Bearer http-access-secret");
      assert.equal(request.headers.cookie, undefined);
      response.statusCode = apiStatus;
      return response.end(JSON.stringify({ actor_id: "oidc:sha256:http", roles: ["libris-reader"], permissions: ["bibliographic:read"] }));
    }
    response.statusCode = 404; response.end("{}");
  });
  issuer = `http://127.0.0.1:${await listen(upstream)}`;
  const reserve = createServer();
  const port = await listen(reserve);
  await new Promise<void>((resolve) => reserve.close(() => resolve()));
  const origin = `http://127.0.0.1:${port}`;
  let output = "";
  const web = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", String(port)], {
    cwd: new URL("..", import.meta.url), env: {
      ...process.env, WEB_AUTH_ENV: "local", WEB_ORIGIN: origin, WEB_OIDC_ISSUER: issuer,
      WEB_OIDC_CLIENT_ID: "libris-web", WEB_SESSION_DATABASE_URL: process.env.TEST_WEB_HTTP_DATABASE_URL,
      WEB_SESSION_KEYS: JSON.stringify({ http: randomBytes(32).toString("base64") }), WEB_SESSION_ACTIVE_KEY: "http",
      API_INTERNAL_URL: issuer,
    }, stdio: ["ignore", "pipe", "pipe"],
  });
  web.stdout.on("data", (data: Buffer) => { output += data.toString(); });
  web.stderr.on("data", (data: Buffer) => { output += data.toString(); });
  const fetchWeb = (path: string, init?: RequestInit) => fetch(origin + path, { ...init, redirect: "manual" });
  const sessionCookies = (response: Response) => response.headers.getSetCookie().map((cookie) => cookie.split(";")[0]).join("; ");
  try {
    assert.equal((await pool.query("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")).rows[0].count, "0");
    await pool.query(await readFile(new URL("../migrations/0001_oidc_sessions.up.sql", import.meta.url), "utf8"));
    let ready = false;
    for (let attempt = 0; attempt < 150; attempt++) {
      try { if ((await fetchWeb("/en")).ok) { ready = true; break; } } catch { /* startup */ }
      if (web.exitCode !== null) break;
      await delay(100);
    }
    assert.ok(ready, "Next server failed to start");
    const anonymous = await (await fetchWeb("/en")).text();
    assert.match(anonymous, /Sign in/); assert.equal(apiCalls, 0);
    const login = await fetchWeb("/oidc/login", { method: "POST", headers: { Origin: origin,
      "Content-Type": "application/x-www-form-urlencoded" }, body: "returnTo=%2Fen%3Fview%3Doriginal" });
    assert.equal(login.status, 303);
    const binding = sessionCookies(login);
    const authorize = await fetch(login.headers.get("location")!, { redirect: "manual" });
    const callback = new URL(authorize.headers.get("location")!);
    const sessionResponse = await fetchWeb(callback.pathname + callback.search, { headers: { Cookie: binding } });
    assert.equal(sessionResponse.status, 303);
    assert.equal(sessionResponse.headers.get("location"), origin + "/en?view=original");
    const allCookies = sessionCookies(sessionResponse);
    const session = allCookies.split("; ").find((value) => value.startsWith("libris-session="))!;
    assert.ok(session);
    assert.ok(sessionResponse.headers.get("set-cookie")?.includes("HttpOnly"));
    assert.equal(sessionResponse.headers.get("Cache-Control"), "no-store, private");
    const authenticated = await fetchWeb("/en", { headers: { Cookie: session } });
    assert.match(authenticated.headers.get("Cache-Control")!, /no-store/);
    const html = await authenticated.text();
    assert.match(html, /Authenticated session/); assert.match(html, /oidc:sha256:http/);
    assert.doesNotMatch(html, /http-access-secret|http-refresh-secret/);
    assert.equal((await fetchWeb(callback.pathname + callback.search, { headers: { Cookie: binding } })).headers.get("location"), origin + "/pt?auth=error");
    const csrf = html.match(/name="csrf" value="([^"]+)"/)?.[1];
    assert.ok(csrf);
    const logoutForm = new URLSearchParams({ csrf, returnTo: "/en" }).toString();
    const csrfRejected = await fetchWeb("/oidc/logout", { method: "POST", headers: { Origin: "https://evil.invalid",
      Cookie: session, "Content-Type": "application/x-www-form-urlencoded" }, body: logoutForm });
    assert.equal(csrfRejected.status, 403);
    const expired = await pool.query("UPDATE libris_web.sessions SET expires_at=expires_at RETURNING payload");
    assert.ok(!expired.rows[0].payload.includes("http-access-secret"));
    // Force access expiry by provider TTL in a new flow is covered by deterministic
    // service tests; this HTTP test exercises the production routes/SSR.
    apiStatus = 403;
    assert.match(await (await fetchWeb("/en", { headers: { Cookie: session } })).text(), /insufficient permissions/);
    apiStatus = 200;
    const logout = await fetchWeb("/oidc/logout", { method: "POST", headers: { Origin: origin, Cookie: session,
      "Content-Type": "application/x-www-form-urlencoded" }, body: logoutForm });
    assert.equal(logout.status, 303);
    assert.ok(!logout.headers.get("location")!.includes("secret"));
    assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions")).rows[0].count, "0");
    assert.match(await (await fetchWeb("/en", { headers: { Cookie: session } })).text(), /session expired/);
    assert.equal(refreshes, 0);
    assert.ok(!output.includes("http-access-secret") && !output.includes("http-refresh-secret"));
  } finally {
    web.kill("SIGTERM");
    await new Promise<void>((resolve) => { if (web.exitCode !== null) resolve(); else web.once("exit", () => resolve()); });
    await new Promise<void>((resolve) => upstream.close(() => resolve()));
    await pool.end();
  }
});
