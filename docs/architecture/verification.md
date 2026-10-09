# Verificação da estrutura inicial

Data: 2026-10-09. Resultados observados nesta sessão; não são uma certificação de
produção ou um teste dos módulos bibliotecários, ainda inexistentes.

## Ferramentas e dependências

O diretório inicial continha apenas diretórios reservados `.git`, `.agents`,
`.codex` e `.aws`, sem código. `git status` indicou que não era um repositório Git
válido; esses diretórios foram preservados e não foi criado commit.

O host não tinha uv, Node.js ou pip no Python padrão. As ferramentas de verificação
foram instaladas em `/tmp`, com Python 3.13.16 gerenciado pelo uv, sem alterar
instalações globais. Node.js 24.21.0 foi obtido da distribuição oficial e seu SHA-256
foi conferido. O backend foi inicialmente gerado com `fastapi-new` e adaptado ao
layout `src/libris`, sem rotas fictícias.

Locks resolvidos: FastAPI 0.143.0, SQLAlchemy 2.0.54, asyncpg 0.32.0, Alembic 1.20.0,
Pydantic 2.14.0; Next.js 16.4.0, React 19.3.0, Tailwind 4.3.3, TypeScript 5.9.3; Radix UI Separator adicionado e validado
com novo build e análise TypeScript.
Docker Engine 29.8.2 e Compose 5.6.0 estavam disponíveis.

## Resultados concluídos

| Verificação | Resultado |
| --- | --- |
| `pytest` | 5 testes passaram em 2,52 s |
| `ruff check . ../../tests` | Passou |
| `mypy src` | Passou: 8 arquivos Python |
| `alembic heads` | Passou, nenhuma revisão |
| `alembic upgrade head --sql` | Passou; somente BEGIN/COMMIT, sem tabelas |
| `uv run --locked fastapi --help` | Passou |
| `npm install` | Lock gerado; auditoria inicial informou 0 vulnerabilidades |
| `next build --webpack` | Passou; páginas `/`, `/pt`, `/en` geradas |
| `npm run typecheck` | Passou |
| Frontend standalone via HTTP | `/pt` e `/en`: 200, idioma, título e CSS conferidos |
| Navegação de idioma via HTTP | `/` redirecionou para `/pt`; `/fr` retornou 404 |
| API Uvicorn via HTTP | `/health`: 200 e JSON esperado |
| `docker compose --env-file .env.example config --quiet` | Passou |
| `bash -n scripts/check.sh` | Passou |

Os testes da API usaram `TestClient` com lifespan ativo e não precisaram abrir
conexões PostgreSQL/Elasticsearch. A resposta de saúde representa somente liveness.

## Limites observados

O sandbox bloqueou subprocessos e a abertura de portas internas. Os testes e
checagens finais Python/TypeScript foram executados fora dele com autorização
nativa. O build Turbopack falhou ao abrir a porta interna para processar CSS,
inclusive na tentativa com escalonamento. O build webpack suportado pelo Next.js
passou e foi adotado em `npm run build`.

Starlette emitiu `StarletteDeprecationWarning` sobre o uso de httpx em TestClient,
sugerindo httpx2. Isso não causou falhas; acompanhar a evolução dos clientes e
validar a migração em atualização futura das dependências.

Não foi feita inspeção visual em navegador nem auditoria formal WCAG. Foram
verificados build, tipos e respostas HTML/CSS. Não há testes de RDF/SHACL, banco,
indexação, autenticação ou concorrência de empréstimos porque essas funcionalidades
não foram implementadas nesta fase.

## Docker integrado

`docker compose --env-file .env.example -p libris-verification up --build -d`
terminou com sucesso. Ambas as imagens de aplicação foram construídas a partir
dos locks e os quatro serviços atingiram `healthy`.

- PostgreSQL 17: conexão real de dentro da API usando SQLAlchemy async/asyncpg;
  `SELECT 1` retornou 1 e `pg_tables` confirmou ausência de tabelas no schema public.
- Elasticsearch 9.5.5: `_cluster/health` respondeu HTTP 200 e status `green`.
- API containerizada: `/health` respondeu HTTP 200 com o contrato esperado.
- Frontend containerizado: `/pt` e `/en` responderam HTTP 200, idioma e título
  corretos; os arquivos CSS responderam 200. `/` redirecionou para `/pt` e `/fr`
  retornou 404.

A stack usou somente dados descartáveis e variáveis de `.env.example`. Ao final,
containers, rede e volumes exclusivos do projeto `libris-verification` foram
removidos. As imagens construídas permanecem no cache Docker. Nenhum serviço de
outro projeto foi alterado. Não foi criado `.env` com credenciais reais.

