import "server-only";
import { Pool, type PoolClient } from "pg";
import type { AuthConfig } from "./config";
import { TokenCipher } from "./crypto";
import { digest } from "./security";

export interface LoginTransaction { verifier: string; nonce: string; returnTo: string }
export interface Session {
  accessToken: string; accessExpiresAt: number; refreshToken?: string;
  refreshExpiresAt?: number; subject: string; csrf: string; expiresAt: number;
  retryAfter?: number;
}
export interface SessionHandle {
  value: Session | null;
  save(value: Session): Promise<void>;
  revoke(): Promise<void>;
}
export interface AuthStore {
  putTransaction(state: string, browser: string, value: LoginTransaction, expiresAt: number): Promise<void>;
  consumeTransaction(state: string, browser: string, now: number): Promise<LoginTransaction | null>;
  createSession(id: string, value: Session): Promise<void>;
  withSession<T>(id: string, operation: (handle: SessionHandle) => Promise<T>): Promise<T>;
}
function objectValue(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Invalid stored data");
  return value as Record<string, unknown>;
}
export function parseTransaction(value: unknown): LoginTransaction {
  const data = objectValue(value);
  if (typeof data.verifier !== "string" || typeof data.nonce !== "string" || typeof data.returnTo !== "string") {
    throw new Error("Invalid stored transaction");
  }
  return { verifier: data.verifier, nonce: data.nonce, returnTo: data.returnTo };
}
export function parseSession(value: unknown): Session {
  const data = objectValue(value);
  if (typeof data.accessToken !== "string" || typeof data.subject !== "string" ||
      typeof data.csrf !== "string" || typeof data.accessExpiresAt !== "number" ||
      typeof data.expiresAt !== "number" ||
      (data.refreshToken !== undefined && typeof data.refreshToken !== "string") ||
      (data.refreshExpiresAt !== undefined && typeof data.refreshExpiresAt !== "number") ||
      (data.retryAfter !== undefined && typeof data.retryAfter !== "number")) throw new Error("Invalid stored session");
  return data as unknown as Session;
}
export class PostgresAuthStore implements AuthStore {
  private readonly cipher: TokenCipher;
  constructor(readonly pool: Pool, config: AuthConfig) { this.cipher = new TokenCipher(config); }
  async putTransaction(state: string, browser: string, value: LoginTransaction, expiresAt: number) {
    const hash = digest(state);
    await this.pool.query("INSERT INTO libris_web.auth_transactions VALUES ($1,$2,$3,$4)",
      [hash, digest(browser), this.cipher.seal(value, `transaction:${hash}`), expiresAt]);
  }
  async consumeTransaction(state: string, browser: string, now: number): Promise<LoginTransaction | null> {
    const hash = digest(state);
    // DELETE RETURNING is atomic across workers. Wrong browsers cannot destroy legitimate attempts.
    const result = await this.pool.query<{ payload: string }>(
      "DELETE FROM libris_web.auth_transactions WHERE state_hash=$1 AND browser_hash=$2 AND expires_at>$3 RETURNING payload",
      [hash, digest(browser), now]);
    return result.rows[0] ? parseTransaction(this.cipher.open(result.rows[0].payload, `transaction:${hash}`)) : null;
  }
  async createSession(id: string, value: Session) {
    const hash = digest(id);
    await this.pool.query("INSERT INTO libris_web.sessions VALUES ($1,$2,$3)",
      [hash, this.cipher.seal(value, `session:${hash}`), value.expiresAt]);
  }
  async withSession<T>(id: string, operation: (handle: SessionHandle) => Promise<T>): Promise<T> {
    const hash = digest(id);
    const client: PoolClient = await this.pool.connect();
    try {
      await client.query("BEGIN");
      await client.query("SET LOCAL lock_timeout = '8s'");
      await client.query("SET LOCAL statement_timeout = '10s'");
      const result = await client.query<{ payload: string }>(
        "SELECT payload FROM libris_web.sessions WHERE id_hash=$1 FOR UPDATE", [hash]);
      let value: Session | null = null;
      if (result.rows[0]) {
        try { value = parseSession(this.cipher.open(result.rows[0].payload, `session:${hash}`)); }
        catch { await client.query("DELETE FROM libris_web.sessions WHERE id_hash=$1", [hash]); }
      }
      const handle: SessionHandle = {
        value,
        save: async (next) => {
          await client.query("UPDATE libris_web.sessions SET payload=$2, expires_at=$3 WHERE id_hash=$1",
            [hash, this.cipher.seal(next, `session:${hash}`), next.expiresAt]);
          handle.value = next;
        },
        revoke: async () => {
          await client.query("DELETE FROM libris_web.sessions WHERE id_hash=$1", [hash]);
          handle.value = null;
        },
      };
      const output = await operation(handle);
      await client.query("COMMIT");
      return output;
    } catch (error) { await client.query("ROLLBACK"); throw error; }
    finally { client.release(); }
  }
}
export function createPool(config: AuthConfig): Pool {
  return new Pool({ connectionString: config.databaseUrl, max: 5, connectionTimeoutMillis: 5000,
    idleTimeoutMillis: 30000, query_timeout: 12000 });
}
