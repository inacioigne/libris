// Explicit administrative command; never imported by the application.
import { readFile } from "node:fs/promises";
import { Pool } from "pg";

async function main(): Promise<void> {
  const url = process.env.WEB_SESSION_DATABASE_URL;

  if (!url) {
    throw new Error("WEB_SESSION_DATABASE_URL required");
  }

  const pool = new Pool({
    connectionString: url,
    max: 1,
    connectionTimeoutMillis: 5000,
  });

  try {
    // Choose one incremental migration explicitly. Never run either at startup.
    const migration = process.argv[2] ?? "0001_oidc_sessions";
    if (!["0001_oidc_sessions", "0002_auth_quotas"].includes(migration)) throw new Error("Unknown migration");
    const sql = await readFile(
      new URL(`../migrations/${migration}.up.sql`, import.meta.url),
      "utf8"
    );

    await pool.query(sql);

    console.log("Web session migration applied");
  } finally {
    await pool.end();
  }
}

main().catch((error: unknown) => {
  console.error("Web session migration failed:", error instanceof Error ? error.name : "UnknownError");
  process.exitCode = 1;
});