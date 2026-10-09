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

Consulte o README da raiz para ambiente e Docker. A Etapa 2 implementa o módulo
bibliográfico experimental e a migração `0001_semantic`; execute `uv run alembic
upgrade head` explicitamente para criar suas tabelas. O startup não migra o banco.
`alembic current` exige PostgreSQL disponível. Testes padrão não exigem serviços.

Diagnóstico local:

```bash
uv run python -m libris.modules.bibliographic ../../tests/fixtures/bibliographic/book.ttl
```

[Fundação semântica](../../docs/architecture/semantic-foundation.md) descreve o
perfil, serialização, revisões, integração PostgreSQL e limitações.
