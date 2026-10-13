# Reprodução e evidências de conformidade catalográfica v1 — #30

Este documento reúne os comandos efetivamente suportados e os resultados da
consolidação. Consulte a [matriz](catalogographic-v1-conformance-matrix.md) e o
[inventário](catalogographic-v1-test-inventory.md) para associar requisitos,
fixtures e funções. As evidências históricas dos incrementos anteriores continuam
em seus relatórios; os números abaixo pertencem somente à execução da #30.

## Ambiente e dependências

Python `>=3.13,<3.15`, referência 3.13; ambiente desta execução: Python 3.13.15.
Use `uv sync --locked` em `apps/api` para instalar dependências e grupo dev do
`pyproject.toml`/`uv.lock`: pytest, Ruff, mypy, Pydantic 2, RDFLib, pySHACL,
SQLAlchemy async, asyncpg e Alembic. Não há dependências novas nem novo runner.
A suíte padrão não exige PostgreSQL, Elasticsearch, OIDC ou fontes RDF remotas.

O script geral exige também Node/npm (referência Node 24), dependências instaladas
com `npm ci` em `apps/web`, e Docker Compose para validar a configuração. Build do
frontend não é evidência de editor catalográfico nem valida `docs/examples/validation/consume.ts`.

## Testes locais e conformidade

A partir da raiz:

```bash
cd apps/api
uv sync --locked
uv run pytest

# Consolidação específica: 23 casos novos e 70 casos do corpus/contrato institucional.
uv run pytest ../../tests/api/test_catalogographic_conformance.py \
  ../../tests/api/test_catalogographic_contract.py

# Todos os contratos semânticos (exclui somente startup e autenticação isolada).
uv run pytest ../../tests/api \
  --ignore=../../tests/api/test_startup.py --ignore=../../tests/api/identity

uv run ruff check . ../../tests
uv run mypy src
cd ../..
bash scripts/check.sh
```

`testpaths` seleciona `tests/api`; integração é executada explicitamente abaixo.
Os testes novos verificam Create + identidade armazenada → Read → Graph, estado
completo após Update → Read → Graph, perfil legado aplicável e perfil declarativo
específico de cada entidade. O merge de Update é uma composição de teste; não cria
um serviço público nem resolve referências em banco. Os cinco patches removem a
propriedade indicada, e isomorfismo comprova preservação do restante do grafo.

Round-trip significa equivalência de grafos com `rdflib.compare.isomorphic`, nunca
igualdade textual de JSON-LD/Turtle ou rótulos de blank nodes. Não existe Graph → DTO
completo; extensões usam Graph → representação integral. Parsing de dados sempre
passa pelos adaptadores limitados, sem contextos/imports remotos. Os testes não
reescrevem nenhuma fixture histórica ou shape para obter conformidade.

Em ambiente previamente sincronizado, `.venv/bin/pytest`, `.venv/bin/ruff` e
`.venv/bin/mypy` em `apps/api` são alternativas às respectivas chamadas `uv run`.
Nesta sessão, o uv via Snap falhou dentro do sandbox. Uma tentativa da suíte completa
pela `.venv` ficou bloqueada em testes HTTP e foi interrompida; não conta como aprovação.
Os 23 testes novos passaram também pela `.venv`; as execuções completas finais usaram
as ferramentas existentes com execução autorizada fora do bloqueio do sandbox.

## Integração PostgreSQL

Use PostgreSQL real via URL `postgresql+asyncpg://`, nunca SQLite. A execução desta
sessão utilizou PostgreSQL 17-bookworm descartável, sem volume, em container exclusivo
`libris-issue30-postgres` e porta local dinâmica `127.0.0.1:32769`.
Nenhum banco de trabalho ou container Libris preexistente foi alterado.

Há três variáveis de ambiente independentes (URLs locais não devem ser versionadas):

| Variável | Pré-condição / uso |
| --- | --- |
| TEST_DATABASE_URL | Banco exclusivo de testes, migrado até `0004_semantic_editorial`; snapshots, identidade, CAS, rollback, auditoria e editorial |
| TEST_MIGRATION_DATABASE_URL | Outro banco inicialmente vazio e descartável; teste de upgrade/downgrade de auditoria |
| TEST_EDITORIAL_MIGRATION_DATABASE_URL | Terceiro banco inicialmente vazio e descartável, distinto dos dois anteriores; upgrade/downgrade editorial |
| DATABASE_URL | Para Alembic: apontar explicitamente ao mesmo banco exclusivo de TEST_DATABASE_URL durante instalação; não usar a URL de trabalho |

Os testes de migração executam DDL/downgrade e os demais exercitam rejeições de DML.
Somente apontar essas variáveis para os bancos exclusivos indicados. A execução é
opt-in; variáveis ausentes geram `skip`, não aprovação de persistência. PostgreSQL
inacessível ou URL de outro dialect produz falha de ambiente, não um substituto local.

Exemplo de preparação isolada que reproduz a estratégia desta sessão, usando a
imagem já disponível. Autenticação trust pertence somente a esta instância efêmera
com porta publicada em loopback:

```bash
# Raiz do repositório; não reutilizar o nome de um container existente.
docker run -d --name libris-issue30-postgres --label libris.task=issue30 \
  --publish 127.0.0.1::5432 --env POSTGRES_HOST_AUTH_METHOD=trust \
  --env POSTGRES_USER=libris_test --env POSTGRES_DB=libris_test postgres:17-bookworm
docker port libris-issue30-postgres 5432/tcp
docker exec libris-issue30-postgres pg_isready -U libris_test
# Prosseguir depois que pg_isready indicar disponibilidade.
docker exec libris-issue30-postgres createdb -U libris_test libris_migration_test
docker exec libris-issue30-postgres createdb -U libris_test libris_editorial_migration_test

# Substituir PORTA pelo valor mostrado por docker port; nenhuma senha é versionada.
export TEST_DATABASE_URL='postgresql+asyncpg://libris_test@127.0.0.1:PORTA/libris_test'
export TEST_MIGRATION_DATABASE_URL='postgresql+asyncpg://libris_test@127.0.0.1:PORTA/libris_migration_test'
export TEST_EDITORIAL_MIGRATION_DATABASE_URL='postgresql+asyncpg://libris_test@127.0.0.1:PORTA/libris_editorial_migration_test'
cd apps/api
DATABASE_URL="$TEST_DATABASE_URL" uv run alembic upgrade head
uv run pytest -c pyproject.toml ../../tests/integration -q
cd ../..

# Ao terminar, remover apenas a instância descartável criada acima.
docker rm -f libris-issue30-postgres
unset TEST_DATABASE_URL TEST_MIGRATION_DATABASE_URL TEST_EDITORIAL_MIGRATION_DATABASE_URL
```

Para repetir a suíte de migrações, prepare novamente os bancos inicialmente vazios
conforme seus pré-requisitos. Não execute downgrade para “limpar” um banco existente.
A reprodução não exige `create_all`, Elasticsearch nem `docker compose down -v`.

## Interpretação de falhas e limites

- Falha de DTO: verificar fixture e contrato Create/Read/Update; extras, null obrigatório, datatype/idioma e referências têm camadas próprias.
- Falha SHACL: usar focus/path/sourceShape/componente e release/contexto fixados; comparar à expectativa do manifesto, sem alterar shapes históricas para aceitar a entrada.
- Falha de isomorfismo: perda/alteração de termos RDF; ordem textual e rótulo de BNode não justificam falha. Alguns lexicais aceitos no DTO são explicitamente não exportáveis por RDFLib.
- Falha operacional: indisponibilidade de shapes/engine/banco não é violação catalográfica nem conformidade. Falha de import/lint/build pertence à verificação geral.
- `skip` em integração: falta a variável de banco correspondente; registrar a garantia não verificada. Nenhum skip ocorreu na execução PostgreSQL desta sessão.
- Warnings de RDFLib/ConjunctiveGraph e Starlette/httpx são depreciações preexistentes, mantidas visíveis. Não são aprovações de compatibilidade com futuras versões.

## Resultados desta execução — 2026-10-12

Resultados finais são registrados após conclusão dos processos. Logs temporários em
`/tmp/libris-issue30-*.log` são auxiliares da sessão, não artefatos versionados.

| Comando executado | Resultado |
| --- | --- |
| `uv run pytest -q ../../tests/api/test_catalogographic_conformance.py` | 23 aprovados, 0 reprovados, 0 ignorados; 76 avisos; Python 3.13.15 |
| `.venv/bin/pytest -q ../../tests/api/test_catalogographic_conformance.py` | 23 aprovados, 0 reprovados, 0 ignorados; 76 avisos; alternativa local confirmada |
| `uv run pytest -q ../../tests/api/test_catalogographic_conformance.py ../../tests/api/test_catalogographic_contract.py` | 93 aprovados, 0 reprovados, 0 ignorados; 358 avisos; `/tmp/libris-issue30-conformance.log` |
| `DATABASE_URL` exclusivo: `uv run alembic upgrade head` | Exit code 0; banco descartável instalado até `0004_semantic_editorial` |
| Três URLs exclusivas: `uv run pytest -c pyproject.toml ../../tests/integration -q` | 55 aprovados, 0 reprovados, 0 ignorados; 256 avisos; `/tmp/libris-issue30-integration.log` |
| `uv run ruff check . ../../tests` | Passou após corrigir imports do arquivo novo |
| `uv run mypy src` | Passou: 76 arquivos de código |

A seleção semântica documentada foi conferida com `--collect-only`: 1.139 casos
(sem startup/autenticação); a suíte geral executa também esses mesmos casos.

Primeira execução de `scripts/check.sh`: 1.195 testes aprovados, 0 reprovados,
0 ignorados, 465 avisos; depois parou no Ruff por ordenação de imports no arquivo novo.
Corrigida conforme configuração de `apps/api`, sem alterar código de produção.
Essa rodada não comprova frontend/Compose.

Execução final de `PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh`:
**exit code 0**. `uv run pytest`: **1.195 aprovados, 0 reprovados, 0 ignorados**, 465
avisos; Ruff passou; mypy passou em 76 arquivos; `npm run build`, `npm run typecheck`
e `docker compose --env-file .env.example config --quiet` passaram. Node 24.16.0 já
estava instalado; não houve instalação ou atualização de dependências.
Log: `/tmp/libris-issue30-check-final.log`. Os 23 testes novos e os 93 da consolidação
são subconjuntos dos 1.195, não quantidades adicionais.

`git diff --check` passou. Inventário conferido contra os 177 caminhos existentes;
referências explícitas `arquivo.py::test_*` conferidas contra as funções reais.
O container exclusivo de integração foi removido depois da execução, com seus três
bancos descartáveis. Nenhum serviço externo permanece necessário para a suíte local.

## Avaliação e pendências

Inventário e matriz distinguem cobertura local, física PostgreSQL e contratos ainda
futuros. Não há alteração de arquitetura, dependências, locks, releases, migrações ou
funcionalidades bibliotecárias. Fixtures existentes bastaram; somente o manifesto
institucional recebeu expectativas explícitas dos constraints já estabelecidos.

Homologação institucional, resolução HTTP/tombstones, editor/cliente, PATCH público
transacional e conectores de vocabulário são limites documentados na matriz, fora
desta subissue. Não há pendência de integração PostgreSQL desta execução.
Nenhuma branch, staging, commit, push, PR ou recurso remoto foi criado/modificado.

**Avaliação da #30: pronta para revisão.** Critérios no escopo implementado possuem
evidências reproduzíveis e todas as verificações finais passaram. As lacunas G01–G06
da matriz delimitam funcionalidades futuras ou limites deliberados, sem fingir cobertura.
