#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
(cd apps/api && uv run pytest && uv run ruff check . ../../tests && uv run mypy src)
(cd apps/web && npm run build && npm run typecheck)
docker compose --env-file .env.example config --quiet
