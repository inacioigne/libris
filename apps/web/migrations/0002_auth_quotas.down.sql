BEGIN;
-- Explicit operator action only; preserves sessions, transactions and legacy schemas.
DROP TABLE libris_web.auth_quotas;
COMMIT;
