import "server-only";
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import type { AuthConfig } from "./config";

export class TokenCipher {
  constructor(private readonly config: Pick<AuthConfig, "keys" | "activeKey">) {}
  seal(value: object, context: string): string {
    const iv = randomBytes(12);
    const key = this.config.keys.get(this.config.activeKey);
    if (!key) throw new Error("Encryption unavailable");
    const cipher = createCipheriv("aes-256-gcm", key, iv);
    cipher.setAAD(Buffer.from(context));
    const encrypted = Buffer.concat([cipher.update(JSON.stringify(value), "utf8"), cipher.final()]);
    return [this.config.activeKey, iv.toString("base64url"), cipher.getAuthTag().toString("base64url"),
      encrypted.toString("base64url")].join(".");
  }
  open(value: string, context: string): unknown {
    const [id, iv, tag, encrypted, extra] = value.split(".");
    const key = this.config.keys.get(id);
    if (!key || !iv || !tag || !encrypted || extra) throw new Error("Encrypted data unavailable");
    const decipher = createDecipheriv("aes-256-gcm", key, Buffer.from(iv, "base64url"));
    decipher.setAAD(Buffer.from(context));
    decipher.setAuthTag(Buffer.from(tag, "base64url"));
    return JSON.parse(Buffer.concat([decipher.update(Buffer.from(encrypted, "base64url")),
      decipher.final()]).toString("utf8")) as unknown;
  }
}
