import "server-only";
import { AsyncLocalStorage } from "node:async_hooks";
import { createHash, randomUUID } from "node:crypto";

export type SecurityEventType = "authentication.started" | "authentication.failed" |
  "session.created" | "session.expired" | "session.revoked" | "session.refreshed" |
  "session.refresh_failed" | "session.logout" | "access.administrative_denied" | "access.quota_exceeded";
export type SecurityAction = "login" | "callback" | "reauthenticate" | "identity" | "refresh" | "logout" | "admin.access";
export type Outcome = "success" | "denied" | "error" | "unavailable";
export type Reason = "none" | "invalid_request" | "callback_rejected" | "cancelled" |
  "session_expired" | "refresh_rejected" | "provider_unavailable" | "api_rejected" |
  "storage_unavailable" | "insufficient_permissions" | "login_required" | "quota_exceeded";
export interface SecurityEvent {
  schema_version: "1.0"; event_id: string; event_type: SecurityEventType; occurred_at: string;
  correlation_id: string; actor_id: string | null; actor_type: "human" | "unknown";
  action: SecurityAction; outcome: Outcome; reason: Reason;
  resource_type: "session" | "administrative" | null; resource_id: null; component: "bff";
}
export interface SecuritySink { emit(event: Readonly<SecurityEvent>): void }
const correlations = new AsyncLocalStorage<string>();
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
export function safeCorrelation(value?: string | null): string {
  return value && value.length === 36 && uuid.test(value) ? value : randomUUID();
}
export function currentCorrelation(): string { return correlations.getStore() ?? randomUUID(); }
export function withCorrelation<T>(value: string | null | undefined, work: () => T): T {
  return correlations.run(safeCorrelation(value), work);
}
export function actorIdentifier(issuer: string, subject: string): string {
  return "oidc:sha256:" + createHash("sha256").update(JSON.stringify([issuer, subject]), "utf8").digest("hex");
}
const eventTypes: readonly SecurityEventType[] = ["authentication.started", "authentication.failed", "session.created",
  "session.expired", "session.revoked", "session.refreshed", "session.refresh_failed", "session.logout",
  "access.administrative_denied", "access.quota_exceeded"];
const actions: readonly SecurityAction[] = ["login", "callback", "reauthenticate", "identity", "refresh", "logout", "admin.access"];
const reasons: readonly Reason[] = ["none", "invalid_request", "callback_rejected", "cancelled", "session_expired",
  "refresh_rejected", "provider_unavailable", "api_rejected", "storage_unavailable", "insufficient_permissions", "login_required", "quota_exceeded"];
const fields = "action,actor_id,actor_type,component,correlation_id,event_id,event_type,occurred_at,outcome,reason,resource_id,resource_type,schema_version";
export function serializeSecurityEvent(event: Readonly<SecurityEvent>): string {
  if (Object.keys(event).sort().join(",") !== fields || event.schema_version !== "1.0" || event.component !== "bff" ||
      !uuid.test(event.event_id) || !uuid.test(event.correlation_id) ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(event.occurred_at) ||
      !Number.isFinite(Date.parse(event.occurred_at)) || new Date(event.occurred_at).toISOString() !== event.occurred_at || !eventTypes.includes(event.event_type) ||
      !actions.includes(event.action) || !reasons.includes(event.reason) ||
      !["success", "denied", "error", "unavailable"].includes(event.outcome) ||
      !["session", "administrative", null].includes(event.resource_type) || event.resource_id !== null ||
      (event.actor_id === null ? event.actor_type !== "unknown" :
        event.actor_type !== "human" || !/^oidc:sha256:[0-9a-f]{64}$/.test(event.actor_id)))
    throw new Error("Invalid security envelope");
  const confirmation = ["authentication.started", "session.created", "session.expired", "session.revoked", "session.refreshed"].includes(event.event_type);
  if ((confirmation && event.outcome !== "success") ||
      (["authentication.failed", "session.refresh_failed", "access.administrative_denied", "access.quota_exceeded"].includes(event.event_type) && event.outcome === "success") ||
      (event.event_type === "authentication.failed" && event.actor_id !== null))
    throw new Error("Security event/outcome mismatch");
  // Sorted explicit keys, no exception/request/session object serialization.
  return JSON.stringify(event, fields.split(","));
}
export class LoggingSecuritySink implements SecuritySink {
  emit(event: Readonly<SecurityEvent>): void { console.info(serializeSecurityEvent(event)); }
}
export class SecurityAudit {
  constructor(private readonly sink: SecuritySink = new LoggingSecuritySink()) {}
  event(eventType: SecurityEventType, action: SecurityAction, outcome: Outcome,
    reason: Reason = "none", actorId: string | null = null): SecurityEvent {
    return Object.freeze({ schema_version: "1.0", event_id: randomUUID(), event_type: eventType,
      occurred_at: new Date().toISOString(), correlation_id: currentCorrelation(), actor_id: actorId,
      actor_type: actorId === null ? "unknown" : "human", action, outcome, reason,
      resource_type: eventType.startsWith("session.") ? "session" : eventType === "access.administrative_denied" ? "administrative" : null,
      resource_id: null, component: "bff" });
  }
  emit(event: SecurityEvent): void {
    try {
      serializeSecurityEvent(event);
      this.sink.emit(event);
    } catch {
      // Adapter boundary: best effort, static loss signal, no arbitrary exception text.
      console.warn("security_audit_sink_unavailable");
    }
  }
  record(...args: Parameters<SecurityAudit["event"]>): void { this.emit(this.event(...args)); }
}
