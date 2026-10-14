import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

// Administrative setup for disposable integration databases only. No runtime import.
export async function migrateDatabase(connection: string): Promise<void> {
  if (process.env.TEST_WEB_ISOLATED !== "1") throw new Error("Isolated database required");
  try {
    await promisify(execFile)(
      fileURLToPath(new URL("../../api/.venv/bin/python", import.meta.url)),
      ["-m", "alembic", "upgrade", "head"],
      {
        cwd: new URL("../../api", import.meta.url),
        env: { ...process.env, APP_ENV: "test", OIDC_ENABLED: "false", CORS_ORIGINS: "[]",
          DATABASE_URL: connection.replace(/^postgres(?:ql)?:/, "postgresql+asyncpg:") },
      },
    );
  } catch {
    // Subprocess errors contain environment/SQL context; never echo credentials.
    throw new Error("Alembic test setup failed; install API dependencies and inspect isolated DB");
  }
}
