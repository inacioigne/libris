BEGIN;
-- Shared global circuit quotas; constant cardinality (three routes), no client identifiers.
CREATE TABLE libris_web.auth_quotas (
  route text PRIMARY KEY CHECK (route IN ('login', 'callback', 'logout')),
  window_started timestamptz NOT NULL,
  attempts integer NOT NULL CHECK (attempts > 0)
);
COMMIT;
