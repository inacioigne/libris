# Libris API

Execute os comandos a partir deste diretório:

```bash
uv sync --locked
uv run fastapi dev --host 0.0.0.0
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
uv run alembic current
```

Consulte o README da raiz para ambiente e Docker. Não há modelos de negócio nem
migrações de tabelas nesta fase. `alembic current` exige PostgreSQL disponível.
