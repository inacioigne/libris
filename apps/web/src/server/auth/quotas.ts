import "server-only";
import type { Pool } from "pg";

export type AuthRoute = "login" | "callback" | "logout";
export interface QuotaPolicy { windowSeconds: number; limits: Readonly<Record<AuthRoute, number>> }
export interface QuotaResult { allowed: boolean; retryAfter: number }

export async function postgresQuota(pool: Pool, route: AuthRoute, policy: QuotaPolicy): Promise<QuotaResult> {
  // One bounded row per route, shared by replicas. No IP/header or attacker-created keys.
  // ON CONFLICT takes the row lock; statement_timestamp uses the database clock.
  const result = await pool.query<{ allowed: boolean; retry_after: number }>(`
    INSERT INTO libris_web.auth_quotas AS q (route, window_started, attempts)
    VALUES ($1, statement_timestamp(), 1)
    ON CONFLICT (route) DO UPDATE SET
      window_started = CASE WHEN q.window_started + $2 * interval '1 second' <= statement_timestamp()
        THEN statement_timestamp() ELSE q.window_started END,
      attempts = CASE WHEN q.window_started + $2 * interval '1 second' <= statement_timestamp()
        THEN 1 ELSE LEAST(q.attempts + 1, $3 + 1) END
    RETURNING attempts <= $3 AS allowed,
      LEAST($2, GREATEST(1, CEIL(EXTRACT(EPOCH FROM (window_started + $2 * interval '1 second' - clock_timestamp())))))::int AS retry_after
  `, [route, policy.windowSeconds, policy.limits[route]]);
  const row = result.rows[0];
  if (!row) throw new Error("Quota unavailable");
  return { allowed: row.allowed, retryAfter: row.retry_after };
}
