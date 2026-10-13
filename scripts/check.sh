#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
(cd apps/api && uv run pytest && uv run ruff check . ../../tests && uv run mypy src)
(cd apps/web && npm test && npm run build && npm run typecheck)
# Credenciais efêmeras somente para validação estática; não inicia serviços.
KEYCLOAK_ADMIN_USERNAME="$(apps/api/.venv/bin/python -c 'import secrets; print(secrets.token_hex(16))')" \
KEYCLOAK_ADMIN_PASSWORD="$(apps/api/.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))')" \
  docker compose --env-file .env.example config --quiet
