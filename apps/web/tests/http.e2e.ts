import assert from "node:assert/strict";
import { test } from "node:test";
import { spawn } from "node:child_process";
import { createServer, type Server } from "node:http";
import { migrateDatabase } from "./migrations";
import { createHash, randomBytes } from "node:crypto";
import { setTimeout as delay } from "node:timers/promises";
import { Pool } from "pg";
import { probeBrowser } from "./browser";
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
  let permissions = ["bibliographic:read"];
  let issuer = "", attackPolicy = "";
  const upstream = createServer(async (request, response) => {
    const url = new URL(request.url!, issuer);
    response.setHeader("Content-Type", "application/json");
    if (url.pathname === "/csp-attack") {
      response.setHeader("Content-Type", "text/html");
      response.setHeader("Content-Security-Policy", attackPolicy);
      return response.end("<!doctype html><html><body><script>window.injectionExecuted=true</script><p>CSP probe</p></body></html>");
    }
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
      if (apiStatus === 401) {
        response.setHeader("WWW-Authenticate", "Bearer");
        return response.end(JSON.stringify({ detail: "Autenticação necessária ou inválida." }));
      }
      if (apiStatus === 403) return response.end(JSON.stringify({ detail: "Permissão insuficiente." }));
      if (apiStatus >= 500) return response.end(JSON.stringify({ detail: "Service unavailable" }));
      return response.end(JSON.stringify({ actor_id: "oidc:sha256:http", roles: ["libris-reader"], permissions }));
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
    await migrateDatabase(process.env.TEST_WEB_HTTP_DATABASE_URL!);
    let ready = false;
    for (let attempt = 0; attempt < 150; attempt++) {
      try { if ((await fetchWeb("/en/opac")).ok) { ready = true; break; } } catch { /* startup */ }
      if (web.exitCode !== null) break;
      await delay(100);
    }
    assert.ok(ready, "Next server failed to start");
    for (const [path, target] of [["/", "/pt/opac"], ["/pt", "/pt/opac"], ["/en?auth=cancelled&tag=one&tag=two", "/en/opac?auth=cancelled&tag=one&tag=two"]]) {
      const response = await fetchWeb(path);
      assert.equal(response.status, 307);
      assert.equal(new URL(response.headers.get("location")!, origin).href, origin + target);
    }
    assert.equal((await fetchWeb("/fr")).status, 404);
    assert.equal((await fetchWeb("/fr/opac")).status, 404);
    const anonymousResponse = await fetchWeb("/en/opac");
    const csp = anonymousResponse.headers.get("Content-Security-Policy")!;
    assert.doesNotMatch(csp, /unsafe-inline|unsafe-eval|upgrade-insecure-requests/);
    attackPolicy = csp;
    const nonce = csp.match(/'nonce-([^']+)'/)?.[1];
    assert.ok(nonce);
    assert.equal(anonymousResponse.headers.get("X-Content-Type-Options"), "nosniff");
    assert.equal(anonymousResponse.headers.get("Strict-Transport-Security"), null);
    assert.equal(anonymousResponse.headers.get("X-Powered-By"), null);
    const anonymous = await anonymousResponse.text();
    const scripts = [...anonymous.matchAll(/<script\b([^>]*)>/g)];
    assert.ok(scripts.length > 0);
    for (const script of scripts) assert.ok(script[1].includes(`nonce="${nonce}"`), "Every SSR/hydration script must carry the response nonce");
    const nextPage = await fetchWeb("/pt/opac");
    assert.notEqual(nextPage.headers.get("Content-Security-Policy"), csp);
    const asset = anonymous.match(/<script[^>]+src="([^"]+)"/)?.[1];
    assert.ok(asset);
    const assetResponse = await fetchWeb(asset);
    assert.equal(assetResponse.status, 200);
    assert.match(assetResponse.headers.get("Cache-Control")!, /immutable/);
    assert.doesNotMatch(assetResponse.headers.get("Cache-Control")!, /no-store/);
    assert.match(anonymous, /Sign in/); assert.equal(apiCalls, 0);
    const checkPrivate = (response: Response) => {
      assert.match(response.headers.get("Cache-Control")!, /private/);
      assert.match(response.headers.get("Cache-Control")!, /no-store/);
      assert.equal(response.headers.get("Pragma"), "no-cache");
      assert.equal(response.headers.get("Referrer-Policy"), new URL(response.url).pathname.startsWith("/oidc/") ? "no-referrer" : "same-origin");
    };
    const blocked = (html: string) => {
      assert.doesNotMatch(html, /id="capabilities-title"|aria-label="Administrative navigation"|id="cataloging"/);
      assert.doesNotMatch(html, /http-access-secret|http-refresh-secret|http-subject/);
    };
    for (const locale of ["pt", "en"]) {
      const response = await fetchWeb(`/${locale}/admin?permissions=system:admin&actor_id=forged`, {
        headers: { "X-Permissions": "system:admin", "X-Actor-Id": "forged", Cookie: "permissions=system:admin; roles=libris-admin" },
      });
      checkPrivate(response);
      const html = await response.text(); blocked(html);
      assert.match(html, locale === "pt" ? /Autenticação necessária/ : /Sign in required/);
      assert.match(html, new RegExp(`name="returnTo" value="/${locale}/admin"`));
      assert.equal(apiCalls, 0);
    }
    const invalidCookie = await fetchWeb("/en/admin", { headers: { Cookie: `libris-session=${randomBytes(32).toString("base64url")}` } });
    checkPrivate(invalidCookie); const invalidHtml = await invalidCookie.text();
    assert.match(invalidHtml, /Session expired/); blocked(invalidHtml);
    for (const path of ["/fr/admin", "/en/admin/cataloging"]) {
      const response = await fetchWeb(path); assert.equal(response.status, 404); blocked(await response.text());
      if (path.startsWith("/en/admin/")) checkPrivate(response);
    }
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
    const authenticated = await fetchWeb("/en/opac", { headers: { Cookie: session } });
    assert.match(authenticated.headers.get("Cache-Control")!, /no-store/);
    const html = await authenticated.text();
    assert.match(html, /Authenticated session/); assert.match(html, /oidc:sha256:http/);
    assert.doesNotMatch(html, /http-access-secret|http-refresh-secret/);
    assert.equal((await fetchWeb(callback.pathname + callback.search, { headers: { Cookie: binding } })).headers.get("location"), origin + "/pt/opac?auth=error");
    const readOnly = await fetchWeb("/en/admin?permissions=system:admin", { headers: { Cookie: session, "X-Permissions": "system:admin" } });
    checkPrivate(readOnly); const deniedHtml = await readOnly.text();
    assert.match(deniedHtml, /Access denied/); assert.match(deniedHtml, /oidc:sha256:http/); blocked(deniedHtml);
    assert.match(deniedHtml, /action="\/oidc\/logout"/);
    assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions")).rows[0].count, "1");
    for (const [effective, expected, absent] of [
      [["bibliographic:update"], "cataloging", "authorities"],
      [["authority:manage"], "authorities", "cataloging"],
      [["editorial:approve", "metadata_revision:read"], "editorial", "system"],
      [["editorial:publish"], "editorial", "cataloging"],
      [["system:admin"], "system", "cataloging"],
    ] as const) {
      permissions = [...effective];
      for (const locale of ["pt", "en"]) {
        const response = await fetchWeb(`/${locale}/admin`, { headers: { Cookie: session } }); checkPrivate(response);
        const adminHtml = await response.text();
        assert.match(adminHtml, new RegExp(`id="${expected}"`));
        assert.doesNotMatch(adminHtml, new RegExp(`id="${absent}"`));
        assert.match(adminHtml, /id="capabilities-title"/);
        assert.match(adminHtml, /<main id="content" tabindex="-1"/);
        assert.match(adminHtml, /class="skip-link"/);
        assert.match(adminHtml, /aria-current="page"/);
        assert.equal((adminHtml.match(/<h1(?: |>)/g) ?? []).length, 1);
        assert.match(adminHtml, /<h2/); assert.match(adminHtml, /<h3/);
        assert.match(adminHtml, locale === "pt" ? /<html lang="pt-BR"/ : /<html lang="en"/);
        assert.doesNotMatch(adminHtml, /http-access-secret|http-refresh-secret|http-subject/);
      }
    }
    const uncachedAnonymous = await fetchWeb("/en/admin"); checkPrivate(uncachedAnonymous);
    const uncachedHtml = await uncachedAnonymous.text(); blocked(uncachedHtml); assert.match(uncachedHtml, /Sign in required/);
    const rscAnonymous = await fetchWeb("/en/admin", { headers: { RSC: "1" } }); checkPrivate(rscAnonymous); blocked(await rscAnonymous.text());
    permissions = ["made-up:admin"];
    blocked(await (await fetchWeb("/en/admin", { headers: { Cookie: session } })).text());
    for (const status of [403, 503]) {
      apiStatus = status;
      const response = await fetchWeb("/en/admin", { headers: { Cookie: session } }); checkPrivate(response);
      const html = await response.text(); blocked(html);
      assert.match(html, status === 403 ? /Access denied/ : /Service unavailable/);
    }
    apiStatus = 200;
    const csrf = html.match(/name="csrf" value="([^"]+)"/)?.[1];
    assert.ok(csrf);
    const logoutForm = new URLSearchParams({ csrf, returnTo: "/en/opac" }).toString();
    const csrfRejected = await fetchWeb("/oidc/logout", { method: "POST", headers: { Origin: "https://evil.invalid",
      Cookie: session, "Content-Type": "application/x-www-form-urlencoded" }, body: logoutForm });
    assert.equal(csrfRejected.status, 403);
    const expired = await pool.query("UPDATE libris_web.sessions SET expires_at=expires_at RETURNING payload");
    assert.ok(!expired.rows[0].payload.includes("http-access-secret"));
    // Force access expiry by provider TTL in a new flow is covered by deterministic
    // service tests; this HTTP test exercises the production routes/SSR.
    apiStatus = 403;
    assert.match(await (await fetchWeb("/en/opac", { headers: { Cookie: session } })).text(), /insufficient permissions/);
    apiStatus = 200;
    const logout = await fetchWeb("/oidc/logout", { method: "POST", headers: { Origin: origin, Cookie: session,
      "Content-Type": "application/x-www-form-urlencoded" }, body: logoutForm });
    assert.equal(logout.status, 303);
    assert.equal(new URL(logout.headers.get("location")!).searchParams.get("post_logout_redirect_uri"), origin + "/en/opac");
    assert.ok(!logout.headers.get("location")!.includes("secret"));
    assert.equal((await pool.query("SELECT count(*) FROM libris_web.sessions")).rows[0].count, "0");
    assert.match(await (await fetchWeb("/en/opac", { headers: { Cookie: session } })).text(), /session expired/);
    const expiredAdmin = await fetchWeb("/en/admin", { headers: { Cookie: session } }); checkPrivate(expiredAdmin);
    const expiredHtml = await expiredAdmin.text(); assert.match(expiredHtml, /Session expired/); blocked(expiredHtml);
    // Complete both admin login return flows through built production routes.
    for (const locale of ["pt", "en"]) {
      permissions = ["authority:manage"];
      const login = await fetchWeb("/oidc/login", { method: "POST", headers: { Origin: origin }, body: new URLSearchParams({ returnTo: `/${locale}/admin` }) });
      checkPrivate(login); assert.equal(login.status, 303);
      const auth = await fetch(login.headers.get("location")!, { redirect: "manual" });
      const callbackUrl = new URL(auth.headers.get("location")!);
      const callbackResponse = await fetchWeb(callbackUrl.pathname + callbackUrl.search, { headers: { Cookie: sessionCookies(login) } });
      checkPrivate(callbackResponse); assert.equal(callbackResponse.headers.get("location"), origin + `/${locale}/admin`);
      const cookie = sessionCookies(callbackResponse).split("; ").find((c) => c.startsWith("libris-session="))!;
      const page = await fetchWeb(`/${locale}/admin`, { headers: { Cookie: cookie } });
      assert.match(await page.text(), /id="authorities"/);
      apiStatus = 401;
      const expired = await fetchWeb(`/${locale}/admin`, { headers: { Cookie: cookie } }); checkPrivate(expired);
      const expiredHtml = await expired.text(); blocked(expiredHtml);
      assert.match(expiredHtml, locale === "pt" ? /Sessão expirada/ : /Session expired/);
      apiStatus = 200;
    }
    for (const returnTo of ["https://evil.invalid", "//evil.invalid", "/en/admin/users", "/en/admin%252f"]) {
      const response = await fetchWeb("/oidc/login", { method: "POST", headers: { Origin: origin }, body: new URLSearchParams({ returnTo }) });
      checkPrivate(response); assert.equal(response.status, 403);
    }
    await pool.query("ALTER TABLE libris_web.sessions RENAME TO unavailable_sessions");
    const unavailable = await fetchWeb("/en/admin", { headers: { Cookie: session } }); checkPrivate(unavailable);
    const unavailableHtml = await unavailable.text(); blocked(unavailableHtml); assert.match(unavailableHtml, /Service unavailable/);
    await pool.query("ALTER TABLE libris_web.unavailable_sessions RENAME TO sessions");
    if (process.env.TEST_WEB_BROWSER_ENABLED === "1") await probeBrowser(origin, issuer + "/csp-attack");
    const oversized = await fetchWeb("/oidc/login", { method: "POST", headers: { Origin: origin,
      "Content-Type": "application/x-www-form-urlencoded" }, body: "returnTo=" + "x".repeat(5000) });
    assert.equal(oversized.status, 413); checkPrivate(oversized);
    assert.equal((await fetchWeb("/oidc/callback?code=" + "x".repeat(4097))).status, 413);
    await pool.query("UPDATE libris_web.auth_quotas SET attempts=240 WHERE route='callback'");
    const throttled = await fetchWeb("/oidc/callback");
    assert.equal(throttled.status, 429); checkPrivate(throttled);
    assert.ok(Number(throttled.headers.get("Retry-After")) > 0);
    await pool.query("UPDATE libris_web.auth_quotas SET window_started=statement_timestamp()-interval '61 seconds' WHERE route='callback'");
    assert.equal((await fetchWeb("/oidc/callback")).status, 303);
    await pool.query("ALTER TABLE libris_web.auth_quotas RENAME TO unavailable_quotas");
    const quotaUnavailable = await fetchWeb("/oidc/callback");
    assert.equal(quotaUnavailable.status, 503); checkPrivate(quotaUnavailable);
    assert.equal(await quotaUnavailable.text(), "");
    await pool.query("ALTER TABLE libris_web.unavailable_quotas RENAME TO auth_quotas");
    assert.equal(refreshes, 0);
    assert.ok(!output.includes("http-access-secret") && !output.includes("http-refresh-secret"));
  } finally {
    web.kill("SIGTERM");
    await new Promise<void>((resolve) => { if (web.exitCode !== null) resolve(); else web.once("exit", () => resolve()); });
    await new Promise<void>((resolve) => upstream.close(() => resolve()));
    await pool.end();
  }
});
