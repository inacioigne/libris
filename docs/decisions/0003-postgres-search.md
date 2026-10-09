# ADR 0003 — PostgreSQL autoritativo e Elasticsearch como projeção

Status: aceito para a estrutura inicial

Data: 2026-10-09

## Contexto

Transações administrativas e descoberta têm necessidades distintas.

## Decisão

PostgreSQL 17, SQLAlchemy 2 async/asyncpg e Alembic; Elasticsearch 9 para índices reconstruíveis.

## Consequências

Busca poderá ser eventualmente consistente. Outbox será introduzido junto da primeira indexação; não há escrita dupla ingênua nem índices implementados agora.
