# Verificação — Entrega A, Incremento 2 da fase 3

Data: 2026-10-10. Nenhum commit realizado.

## Resultado e escopo

Resource Server OIDC integrado ao FastAPI, descoberta/JWKS assíncronos, assinatura
JWT, claims obrigatórias, discriminador de access token, cache/rotação com limite
de frequência, identidade estável, RBAC, dependências substituíveis e /identity/me.
Ator opcional nas revisões complementa origem/processo técnico. Não foram
implementadas as entregas B, C, D ou E.

## Arquivos criados

Em `apps/api/src/libris/modules/identity/`:

- `__init__.py` e inicializadores de `api`, `application`, `domain`, `infrastructure`.
- `domain/models.py`, `domain/permissions.py`, `domain/exceptions.py`.
- `application/service.py`.
- `infrastructure/oidc.py`, `infrastructure/role_mapper.py`.
- `api/dependencies.py`, `api/router.py`.

Outros:

- `apps/api/migrations/versions/0002_revision_actor.py`.
- `tests/api/identity/test_identity.py`.
- `tests/integration/test_revision_actor_postgres.py`.
- `docker-compose.oidc.yml`, `infrastructure/keycloak/libris-realm.json`.
- `docs/decisions/0016-oidc-resource-server.md`.
- `docs/architecture/identity.md` e este relatório.

## Arquivos modificados

- `apps/api/src/libris/core/config.py`, `apps/api/src/libris/main.py`.
- Módulo bibliographic: `domain/models.py`, `application/service.py`,
  `infrastructure/persistence.py`.
- `apps/api/pyproject.toml`, `apps/api/uv.lock`: PyJWT[crypto] >=2.10,<3 e
  declaração HTTPX >=0.28,<1 em produção. Lock inclui cryptography/cffi/pycparser;
  bibliotecas de negócio existentes não foram atualizadas.
- `.env.example`, `docker-compose.yml`.
- `tests/api/test_startup.py`: OpenAPI inclui identity sem remover health.
- `README.md`, `apps/api/README.md`, `docs/architecture/overview.md`.

## Comandos e resultados executados

Python 3.13.15, dependências instaladas com `uv add` e `uv sync --locked`.
A instalação original de uv via Snap exigiu execução fora do sandbox. TestClient
ficou bloqueado no sandbox; execuções finais ocorreram fora dele.

| Verificação executada | Resultado |
| --- | --- |
| `bash scripts/check.sh` | 144 testes API passaram; Ruff e mypy passaram; interrompido em npm ausente (exit 127) |
| `uv run pytest -c pyproject.toml ../../tests/api ../../tests/integration` com banco dedicado | 147 passaram: 144 API + 3 PostgreSQL |
| `ruff check . ../../tests` | Passou |
| `mypy src` | Passou: 33 arquivos |
| `alembic heads` | 0002_revision_actor, único head |
| `alembic upgrade head --sql` | SQL offline gerado; coluna nullable aditiva |
| `alembic upgrade head` em PostgreSQL 17 descartável | Passou |
| `alembic check` no banco dedicado | Nenhuma nova operação de upgrade |
| `alembic downgrade 0001_semantic` e `upgrade head` no banco dedicado preenchido | Passaram; 32 revisões preservadas, 0 atores após remover/recriar coluna, sem backfill |
| `docker compose --env-file .env.example config --quiet` | Passou |
| Configuração Compose com overlay OIDC e valores administrativos temporários de validação | Passou |
| `npm run build && npm run typecheck` | Não executados: npm ausente |
| `git diff --check` | Passou |

O banco de teste foi criado sem volumes, porta 55449, nome
libris-identity-test-pg, sem consultar ou modificar bancos de trabalho. Foi
removido ao final. Um primeiro teste ampliado falhou por fixture que tentava
assinar kid=None; corrigida para omitir kid. A execução final passou integralmente.

Avisos persistentes: depreciação de HTTPX no TestClient Starlette e de
ConjunctiveGraph no parser RDFLib. Não foram alteradas dependências externas ao
escopo para eliminar esses avisos.

## Operação, decisões e limites

[Configuração e comandos](identity.md) documentam todas as variáveis, matriz de
permissões, dependências, algoritmo actor_id, migração e procedimento local PKCE.
[ADR 0016](../decisions/0016-oidc-resource-server.md) registra confiança OIDC,
cache por worker, deny by default e compatibilidade histórica.

Keycloak: realm libris, client de audiência libris-api com quatro client roles,
client público libris-web com PKCE S256, mappers de audiência/client roles somente
para access token; credenciais administrativas via ambiente, sem usuários
predefinidos. Hostname keycloak.localhost:8081 é compartilhado pelo navegador e
pela rede Docker; host pode exigir /etc/hosts. Configuração local é opcional.

**Não foi executado um Keycloak real nem validado o fluxo Authorization Code
contra esse provedor.** Os testes OIDC usam RSA local e HTTPX MockTransport.
O overlay/realm precisa de validação operacional no ambiente do mantenedor.
Não há login/callback Next.js; demonstração PKCE é manual ou com cliente OIDC.

Cache é por worker, discovery fica em memória durante o lifespan; mudança de
jwks_uri exige reinício. Uma rotação durante o intervalo mínimo de refresh pode
gerar 401 temporário. Produção exige HTTPS e audiência/discriminador exclusivos.
Ator NULL preserva ausência de identidade, sem classificar automaticamente
históricos como operações de serviço. Serviços internos recebem contexto confiável;
rotas de escrita futuras deverão obtê-lo da dependência autenticada.

## Próximas entregas

- B: contratos HTTP e endpoints catalográficos, aplicação das permissões às rotas.
- C: ETag/If-Match no HTTP; não houve alteração do CAS existente.
- D: validação SHACL estruturada no contrato HTTP; infraestrutura atual preservada.
- E: integridade/auditoria completa e testes próprios da entrega; testes desta
  mudança cobrem somente autenticação, autorização e associação do ator.
