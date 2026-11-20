import "server-only";

const DEFAULT_LOCAL_API_ORIGIN = "http://localhost:8000";

export function getApiOrigin(): URL {
  const configuredOrigin = process.env.API_INTERNAL_URL?.trim();

  if (!configuredOrigin && process.env.NODE_ENV === "production") {
    throw new Error("A variavel de ambiente API_INTERNAL_URL e obrigatoria.");
  }

  const origin = new URL(configuredOrigin || DEFAULT_LOCAL_API_ORIGIN);
  if (origin.protocol !== "http:" && origin.protocol !== "https:") {
    throw new Error("API_INTERNAL_URL deve usar HTTP ou HTTPS.");
  }

  return origin;
}
