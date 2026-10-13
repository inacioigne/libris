// Explicit administrative command; never imported by the application.
import { readFile } from "node:fs/promises";
import { Pool } from "pg";
const url = process.env.WEB_SESSION_DATABASE_URL;
if (!url) throw new Error("WEB_SESSION_DATABASE_URL required");
const pool = new Pool({ connectionString: url, max: 1, connectionTimeoutMillis: 5000 });
try {
  await pool.query(await readFile(new URL("../migrations/0001_oidc_sessions.up.sql", import.meta.url), "utf8"));
  console.log("Web session migration applied");
} finally { await pool.end(); }
