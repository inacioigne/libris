import "server-only";
import { headers } from "next/headers";
import { createCatalogographicClient } from "../../generated/catalogographic-client";
import type { components } from "../../generated/catalogographic-openapi";
import { authService } from "../auth/runtime";
import { sessionCookie, uniqueCookie, validId } from "../auth/security";
import type { AuthService, Identity } from "../auth/service";
import { currentCorrelation, withCorrelation } from "../security-audit";

export type WorkRead = components["schemas"]["WorkRead"];
export type WorkCreate = components["schemas"]["WorkCreate"];
export type WorkUpdate = components["schemas"]["WorkUpdate"];

export type CatalogPermission =
  | "bibliographic:read"
  | "bibliographic:create"
  | "bibliographic:update";

export interface CatalogRequestOptions {
  service?: AuthService;
  sessionId?: string;
  requestHeaders?: Headers;
  ifMatch?: string;
}

export interface CatalogSessionContext {
  sessionId: string;
  accessToken: string;
  csrf: string;
  identity: Identity;
  requestId: string;
}

export class CatalogAccessError extends Error {
  constructor(
    public readonly status: number,
    public readonly code:
      | "session_missing"
      | "session_expired"
      | "permission_denied"
      | "not_found"
      | "validation_error"
      | "conflict"
      | "precondition_failed"
      | "api_unavailable",
    public readonly detail?: unknown,
  ) {
    super(
      code === "permission_denied"
        ? "Catalog access denied"
        : code === "session_missing" || code === "session_expired"
          ? "Catalog session unavailable"
          : code === "api_unavailable"
            ? "Catalog API unavailable"
            : "Catalog request failed",
    );
  }
}

const catalogPermissions: Record<"read" | "create" | "update", readonly string[]> = {
  read: ["bibliographic:read"],
  create: ["bibliographic:create"],
  update: ["bibliographic:update"],
};

function hasPermission(identity: Identity, required: readonly string[]): boolean {
  return required.every((permission) => identity.permissions.includes(permission));
}

async function resolveSessionContext(options: CatalogRequestOptions = {}): Promise<CatalogSessionContext> {
  const service = options.service ?? authService();
  let sessionId = options.sessionId;
  if (!sessionId) {
    const direct = options.requestHeaders ?? (() => {
      try {
        return headers();
      } catch {
        return new Headers();
      }
    })();
    const incoming = await Promise.resolve(direct);
    sessionId = uniqueCookie(incoming, sessionCookie(service.config));
  }

  if (!validId(sessionId)) {
    throw new CatalogAccessError(401, "session_missing");
  }

  const resolution = await withCorrelation(currentCorrelation(), () => service.resolveSession(sessionId));
  if (resolution.status === "authenticated") {
    return {
      sessionId,
      accessToken: resolution.accessToken,
      csrf: resolution.csrf,
      identity: resolution.identity,
      requestId: currentCorrelation(),
    };
  }
  if (resolution.status === "expired") {
    throw new CatalogAccessError(401, "session_expired", resolution.csrf ? { csrf: resolution.csrf } : undefined);
  }
  if (resolution.status === "forbidden") {
    throw new CatalogAccessError(403, "permission_denied", resolution.csrf ? { csrf: resolution.csrf } : undefined);
  }
  if (resolution.status === "anonymous") {
    throw new CatalogAccessError(401, "session_missing");
  }
  throw new CatalogAccessError(503, "api_unavailable");
}

function mapCatalogFailure(status: number, detail?: unknown): CatalogAccessError {
  if (status === 401) return new CatalogAccessError(401, "session_expired", detail ?? "Authentication required");
  if (status === 403) return new CatalogAccessError(403, "permission_denied", detail ?? "Permission denied");
  if (status === 404) return new CatalogAccessError(404, "not_found", detail ?? "Resource not found");
  if (status === 409) return new CatalogAccessError(409, "conflict", detail ?? "Revision conflict");
  if (status === 412) return new CatalogAccessError(412, "precondition_failed", detail ?? "Precondition failed");
  if (status === 422) return new CatalogAccessError(422, "validation_error", detail ?? "Invalid catalog payload");
  if (status === 503) return new CatalogAccessError(503, "api_unavailable", detail ?? "Catalog service unavailable");
  if (status === 504) return new CatalogAccessError(504, "api_unavailable", detail ?? "Catalog request timed out");
  return new CatalogAccessError(status || 500, "api_unavailable", detail ?? "Catalog request failed");
}

async function executeWorkRequest<T>(
  request: (client: ReturnType<typeof createCatalogographicClient>, context: CatalogSessionContext) => Promise<{ data?: T; error?: unknown; response?: Response }>,
  options: CatalogRequestOptions = {},
  requiredPermission: CatalogPermission,
): Promise<T> {
  const context = await resolveSessionContext(options);
  const required = requiredPermission === "bibliographic:read"
    ? catalogPermissions.read
    : requiredPermission === "bibliographic:create"
      ? catalogPermissions.create
      : catalogPermissions.update;
  if (!hasPermission(context.identity, required)) {
    throw new CatalogAccessError(403, "permission_denied", context.identity);
  }

  const client = createCatalogographicClient(options.service ? options.service.config.apiUrl : authService().config.apiUrl);
  const response = await request(client, context);
  if (response.error) {
    const problem = response.response ? await response.response.clone().json().catch(() => undefined) : undefined;
    throw mapCatalogFailure(response.response?.status ?? 500, problem ?? response.error);
  }
  if (!response.data) {
    throw new CatalogAccessError(500, "api_unavailable");
  }
  return response.data as T;
}

export async function getWork(id: string, options: CatalogRequestOptions = {}): Promise<WorkRead> {
  return executeWorkRequest(async (client, context) => {
    const result = await client.GET("/api/v1/catalog/works/{id}", {
      params: { path: { id } },
      headers: {
        Authorization: `Bearer ${context.accessToken}`,
        "X-Request-ID": context.requestId,
        "Cache-Control": "no-store, private",
        Accept: "application/json",
      },
    });
    return { data: result.data as WorkRead, error: result.error, response: result.response };
  }, options, "bibliographic:read");
}

export async function createWork(payload: WorkCreate, options: CatalogRequestOptions = {}): Promise<WorkRead> {
  return executeWorkRequest(async (client, context) => {
    const result = await client.POST("/api/v1/catalog/works", {
      body: payload,
      headers: {
        Authorization: `Bearer ${context.accessToken}`,
        "X-Request-ID": context.requestId,
        "Cache-Control": "no-store, private",
        Accept: "application/json",
      },
    });
    return { data: result.data as WorkRead, error: result.error, response: result.response };
  }, options, "bibliographic:create");
}

export async function updateWork(id: string, payload: WorkUpdate, options: CatalogRequestOptions = {}): Promise<WorkRead> {
  const ifMatch = options.ifMatch ?? "";
  if (ifMatch.trim() === "") {
    throw new CatalogAccessError(428, "precondition_failed", "ETag required");
  }
  return executeWorkRequest(async (client, context) => {
    const result = await client.PATCH("/api/v1/catalog/works/{id}", {
      params: { path: { id }, header: { "if-match": ifMatch } },
      body: payload,
      headers: {
        Authorization: `Bearer ${context.accessToken}`,
        "X-Request-ID": context.requestId,
        "Cache-Control": "no-store, private",
        Accept: "application/json",
      },
    });
    return { data: result.data as WorkRead, error: result.error, response: result.response };
  }, options, "bibliographic:update");
}

export async function requireCatalogPermission(
  required: CatalogPermission,
  options: CatalogRequestOptions = {},
): Promise<CatalogSessionContext> {
  const context = await resolveSessionContext(options);
  const expected = required === "bibliographic:read"
    ? catalogPermissions.read
    : required === "bibliographic:create"
      ? catalogPermissions.create
      : catalogPermissions.update;
  if (!hasPermission(context.identity, expected)) {
    throw new CatalogAccessError(403, "permission_denied", context.identity);
  }
  return context;
}
