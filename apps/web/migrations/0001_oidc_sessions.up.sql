BEGIN;
-- Owned exclusively by the web BFF; no bibliographic foreign keys or tables.
CREATE SCHEMA libris_web;
CREATE TABLE libris_web.auth_transactions (
  state_hash text PRIMARY KEY CHECK (length(state_hash) = 64),
  browser_hash text NOT NULL CHECK (length(browser_hash) = 64),
  payload text NOT NULL,
  expires_at bigint NOT NULL
);
CREATE INDEX auth_transactions_expiry ON libris_web.auth_transactions (expires_at);
CREATE TABLE libris_web.sessions (
  id_hash text PRIMARY KEY CHECK (length(id_hash) = 64),
  payload text NOT NULL,
  expires_at bigint NOT NULL
);
CREATE INDEX sessions_expiry ON libris_web.sessions (expires_at);
COMMIT;
