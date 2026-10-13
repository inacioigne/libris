// Scheduled administrative maintenance; no background worker or startup mutation.
import { Pool } from "pg";
if (!process.env.WEB_SESSION_DATABASE_URL) throw new Error("WEB_SESSION_DATABASE_URL required");
const pool = new Pool({ connectionString: process.env.WEB_SESSION_DATABASE_URL, max: 1, connectionTimeoutMillis: 5000 });
try {
  for (const table of ["auth_transactions", "sessions"]) {
    const key = table === "sessions" ? "id_hash" : "state_hash";
    const result = await pool.query(
      `DELETE FROM libris_web.${table} WHERE ${key} IN (SELECT ${key} FROM libris_web.${table} WHERE expires_at <= $1 LIMIT 1000)`,
      [Date.now()]);
    console.log(`Expired ${table} removed: ${result.rowCount}`);
  }
} finally { await pool.end(); }
