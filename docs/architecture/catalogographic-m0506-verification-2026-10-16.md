# Verificação M05.06 / issue #50 — 2026-10-16

Execução local em America/Manaus; os logs UTC podem indicar 2026-10-17.
Este é um relatório novo. As evidências históricas não foram sobrescritas.

## Diagnóstico e implementação

Branch inicial `main`; `git status --short` e `git diff --stat` inicialmente vazios.
Foram consultadas a #50 aberta (milestone 5), #18, #31, #43, #47, #49 e as issues
M04 pelo conector GitHub, somente leitura. Estado comprovado pelo código: CRUD
persistente, CAS, workflow, políticas OIDC/read_public, negociador Accept e exportador
integral já existiam. Faltavam consultas de coleção e integração de Accept nos GET.

Implementação: dez GET de listagem concretos, envelope Pydantic por tipo, filtros
fechados, keyset UUID, consulta SQLAlchemy única e negociação sobre o snapshot exato.
A revisão candidata não substitui a publicada; histórico, estado e ator não integram
as respostas públicas. A serialização usa o Graph completo, preservando extensões.
Não foram modificados os DTOs históricos, releases, perfis/SHACL, locks, máquina
editorial, políticas, dependências, lockfiles ou migrações.

[Contrato com exemplos](catalogographic-listing.md) e
[ADR 0039](../decisions/0039-catalog-listing-representations.md).

## Ambiente PostgreSQL e SQL

PostgreSQL **17.11**, imagem local `postgres:17-bookworm`, container exclusivo
`libris-issue50-test`, `--rm`, tmpfs `/var/lib/postgresql/data`, sem volumes de
trabalho, porta dinâmica publicada somente em loopback (`127.0.0.1:32769`). Banco
novo `libris_issue50_test`; a matriz M05.06 foi repetida também no segundo banco
novo `libris_issue50_cursor_test` do mesmo container, sem outros escritores. Autenticação trust limitada ao container de teste local;
não é configuração de implantação. Não foram usados bancos de desenvolvimento.

Migrações existentes aplicadas explicitamente com `DATABASE_URL` desse banco e
`uv run alembic upgrade head`; startup não executa migrações. Sem create_all,
downgrade, remoção de volumes ou alteração de infraestrutura global. uv instalado
via Snap e rede local exigiram execução fora do sandbox; a revisão automática
permitiu os comandos. Nenhuma rejeição de aprovação bloqueou esta entrega.

[EXPLAIN ANALYZE/BUFFERS e índices completos](catalogographic-m0506-query-plan-2026-10-16.txt)
foram capturados numa amostra inicial de 24 identidades/42 snapshots. A consulta
editorial levou 0,822 ms e a pública 0,581 ms nessa execução; não são benchmark de
carga. O plano editorial fez hash join/scans/sort; o público fez joins/scans/sort e
index scan por PK da identidade. Isso não demonstra escala institucional nem custo
constante de linhas examinadas. A contagem constante refere-se a statements.

Antes da alteração não existia consulta de coleção para comparar planos; os GET
individuais já liam a revisão/estado sob o protocolo transacional e mantêm essa
estratégia. O novo statement substitui a necessidade de invocar um GET por recurso.

Forma da consulta (nomes abreviados somente neste exemplo):

```sql
SELECT r.id, r.uri, v.number, v.document
FROM experimental_semantic_resources AS r
LEFT JOIN experimental_semantic_editorial_states AS e ON e.resource_id = r.id
JOIN experimental_semantic_revisions AS v
  ON v.resource_id = r.id AND v.number = e.published_revision
WHERE e.editorial_state = :published
  AND v.document @> jsonb_build_array(jsonb_build_object(
    '@id', r.uri, '@type', jsonb_build_array(:entity_class)))
  AND r.id > :after
ORDER BY r.id ASC LIMIT :limit_plus_one;
```

A consulta editorial escolhe r.current_revision; estado só restringe se fornecido.
Agent combina três classes com OR. Filtros UUID/URI/perfil acrescentam igualdades
parametrizadas. PK recursos(id), UNIQUE recursos(uri), PK revisões(resource_id,number)
e PK estado(resource_id) já existem. Nenhuma nova migração foi demonstrada necessária.
Um GIN genérico de todo o histórico não resolve automaticamente o join/@id correlacionado;
materialização/índices adicionais exigem medição representativa e decisão incremental.

## Matriz de testes e aceite

Arquivo **U**: `tests/api/test_catalog_listing.py`.
Arquivo **P**: `tests/integration/test_catalog_listing_postgres.py`.
Arquivo **H**: `tests/api/test_catalogographic_http.py`.

| Critério original da #50 | Estado | Evidência executável |
| --- | --- | --- |
| Listar por tipo, paginação determinística, filtros e limites | ATENDIDO | P `test_list_and_export_exact_published_revision` ×5; `test_keyset_pages_static_and_concurrent_changes_with_constant_sql_cost`; U `test_closed_listing_query` ×30 |
| Escopo público versus editorial autorizado | ATENDIDO | U `test_listing_authorizes_before_storage` ×5; P publicação/candidata ×5 e `test_listing_does_not_infer_state_for_legacy` |
| Accept JSON/JSON-LD/Turtle, MIME e 406 | ATENDIDO | P publicação/candidata ×5, com q, curingas, ausência, vazio, mídia inválida; U `test_listing_openapi_and_cors` |
| URI/idioma/datatype/referências/extensões preservados | ATENDIDO | P publicação/candidata ×5 compara Graph completo, Unicode, idiomas pt-BR/en, xsd:date, IRI externa e extensões dcterms |
| Evitar N+1, paginação estável e consulta/índices documentados | ATENDIDO | P keyset mede exatamente um statement por página; EXPLAIN acima; ADR 0039 documenta scans e limitações |
| Fronteira M09 sem Elasticsearch/facetas/full-text | ATENDIDO | infraestrutura/catalog_query.py consulta somente PostgreSQL; testes reais executados sem serviço de busca; contrato/ADR |
| Travessia sem duplicatas/omissões em conjunto estático e filtros autorizados | ATENDIDO | P keyset: títulos repetidos, primeira/intermediária/última/vazia, limites 1/2/100; filtros combinados nos cinco tipos; U cursor vinculado a filtros/escopo/tipo/limite |
| Draft/histórico/candidata fora do público e revisão publicada exata | ATENDIDO | P ×5 verifica draft/in_review/approved, candidata draft/aprovada divergente, retirada/arquivamento e histórico de publicação; legado separado |
| JSON-LD/Turtle parseiam e são isomorfos | ATENDIDO | P ×5 usa parse_representation/RDFLib e isomorphic com o snapshot publicado e entre sintaxes; não compara strings RDF |
| Consultas sem busca externa e com permissões M04 | ATENDIDO | U negação antes do SQL, token ausente/inválido e expirado assinado com JWKS offline; P execução real PostgreSQL |

Complementos: P `test_agent_subtypes_and_parameterized_filters` ×3 verifica
Agent/Person/Organization e valor com sintaxe de injeção tratado como igualdade.
U `test_cursor_is_canonical_and_bound_to_scope_filters_and_limit` cobre cursor
inválido, padding não canônico e incompatibilidade. H e os testes de startup/contrato
conferem inventário OpenAPI das 49 operações reais, sem endpoints documentais.

A garantia concorrente é limitada: UUID de ordenação não se move com edição;
novos UUIDs anteriores ao cursor ficam fora e posteriores podem entrar. Cada
página usa uma visão SQL coerente, mas não há snapshot global entre páginas.
Mudanças de filtro/visibilidade podem alterar participação. Cursor não é assinado,
nem concede autorização; permissões e seleção pública são reaplicadas sempre.

## Comandos e resultados finais

| Comando efetivamente executado | Resultado |
| --- | --- |
| `DATABASE_URL=<banco-descartavel> uv run alembic upgrade head` (dois bancos novos) | Migrações até 0005_web_auth aplicadas explicitamente |
| `uv run pytest` (dentro de check.sh) | 1953 passed, 0 failed, 0 skipped; 513 avisos; execução de 248,74 s |
| `uv run ruff check . ../../tests` | Passou |
| `uv run mypy src` | Passou, 106 arquivos |
| `TEST_DATABASE_URL=<banco-descartavel> uv run pytest -c pyproject.toml -q ../../tests/integration/test_catalog_listing_postgres.py ../../tests/integration/test_catalog_http_postgres.py ../../tests/integration/test_editorial_http_postgres.py ../../tests/integration/test_catalog_capabilities_postgres.py ../../tests/integration/test_editorial_postgres.py ../../tests/integration/test_audit_postgres.py ../../tests/integration/test_authorization_postgres.py` | 124 passed, 0 failed, 0 skipped; 2328 avisos; 137,59 s |
| Matriz M05.06 inteira no segundo banco novo | 10 passed, 0 failed, 0 skipped; 425 avisos; 24,89 s |
| `test_keyset_pages_static_and_concurrent_changes_with_constant_sql_cost` repetido sozinho no segundo banco | 1 passed, 0 failed, 0 skipped; 108 avisos; 9,41 s; inserções antes/depois do cursor, atualização e repetibilidade |
| `DATABASE_URL=<segundo-banco-descartavel> uv run alembic check` | No new upgrade operations detected |
| `uv run alembic heads` | 0005_web_auth (head) |
| `git diff --check` | Passou |

A primeira execução de `bash scripts/check.sh` passou API/testes/Ruff/mypy e terminou
com exit 127 porque npm não estava no PATH. O Node 24.16.0 já existente em
`/home/inacio/.nvm/versions/node/v24.16.0/bin` foi selecionado na reexecução:
`PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh`.
A reexecução completa terminou com **exit code 0**:

| Etapa do check.sh com Node 24 | Resultado final |
| --- | --- |
| `uv run pytest` | 1953 passed, 0 failed, 0 skipped; 513 avisos; 218,76 s |
| `uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py` | Passou |
| `uv run mypy src` | Passou, 106 arquivos |
| `cd apps/web && npm test` | 167 passed, 0 failed, 0 skipped |
| `npm run build` | Passou; Next.js 16.4.0, compilação, TypeScript e geração concluídas |
| `npm run typecheck` | Passou, tsc --noEmit |
| `docker compose --env-file .env.example config --quiet` | Passou; valores efêmeros gerados pelo script, sem iniciar serviços |

O arquivo rastreado next-env.d.ts foi regenerado automaticamente pelo build;
restaurado ao conteúdo inicial, sem incluir esse efeito na entrega. O typecheck
foi repetido depois dessa restauração. Nenhuma alteração funcional de frontend.
O container descartável foi encerrado explicitamente ao final; os dois bancos
estavam em tmpfs e nenhum volume de trabalho foi removido.

Avisos são de depreciação RDFLib ConjunctiveGraph e Starlette/httpx; não foram
introduzidas dependências para ocultá-los. Nenhum teste de integração listado acima
foi pulado por ausência de infraestrutura. Não foi executada uma nova homologação
Keycloak real; essa limitação não é apresentada como teste aprovado.

Logs locais desta sessão: `/tmp/libris-issue50-postgres-final.log`,
`/tmp/libris-issue50-isolated-final.log`, `/tmp/libris-issue50-concurrent-final.log`,
`/tmp/libris-issue50-check.log` e `/tmp/libris-issue50-check-final.log`. Resultados e
plano SQL persistem neste documento e no artefato datado, sem depender desses logs.

## Falhas encontradas e correções

A primeira suíte completa, durante a implementação, teve **1908 passed / 7 failed**:
todas as sete falhas eram inventários OpenAPI/CORS/status que ainda tratavam listagens
como rotas futuras (405/preflight negado). Foram atualizados para as operações reais,
sem relaxar autenticação, CAS ou proteção de histórico.

Na criação dos novos testes foram corrigidos: composição do IdentityService de teste
com os parâmetros M04 reais; inclusão de Origin em Vary pelo CORS; seleção da revisão
publicada nos comandos de retirada; uso de extensão dcterms:source para IRI externa
sem fingir classificação de dcterms:relation de Agent. A publicação continuou rejeitando
referências não verificadas: a política de produto não foi modificada para testar.
Um ensaio adicional de travessia estática teve **1 failed** porque outro processo
de regressão escrevia no mesmo banco durante a coleta. A divergência era a inserção
de uma nova entidade entre travessias, coerente com a garantia documentada. Esse
ensaio não comprovava conjunto estático; a matriz foi repetida em um segundo banco
vazio sem outros escritores (**10 passed / 0 failed / 0 skipped**). Não se alterou
o teste para ignorar linhas concorrentes.

Uma verificação focada posterior teve 144 passed / 1 failed por expectativa antiga
de Allow-Methods GET em coleção que agora também suporta POST; a asserção foi corrigida.

## Riscos e limites

Sem homologação Keycloak/produção nesta execução: testes OIDC reutilizam o Resource
Server real com JWKS offline e as integrações PostgreSQL usam o override confiável de
ator já existente. Não se altera login, sessão, roles ou autorização para facilitar testes.
Homologação institucional dos perfis e benchmark em grande volume ficam separados.
Não se promete estabilidade de ETag RDF entre serializações isomorfas com blank nodes.
Não há expansão de referências, busca avançada, circulação, inventário físico ou RDF Store.
M09 deverá decidir indexação, outbox, consistência, facetas, full-text e relevância.

## Arquivos e Git

Novos: api/listing.py; api/schemas/listing.py; application/catalog_listing.py;
infrastructure/catalog_query.py, todos em bibliographic; U e P; contrato
catalogographic-listing.md; ADR 0039; plano SQL datado e este relatório.
Modificados: router/editorial/representations; CatalogView e adaptador de leitura pública;
CORS; três testes de inventário (H, startup e contract_specification); README e contratos
HTTP/editorial/serialização. A lista completa final está no relatório ao usuário.

Branch local main. Nenhuma branch, commit, push, PR, pull, merge, rebase, cherry-pick,
stash ou alteração de issue/remotos. As alterações permanecem no workspace local.

### Inventário completo desta entrega

| Arquivo | Situação e responsabilidade |
| --- | --- |
| apps/api/src/libris/api/security.py | Modificado: preflight das coleções reais |
| apps/api/src/libris/modules/bibliographic/api/router.py | Modificado: composição das listagens e Accept nos cinco GET |
| apps/api/src/libris/modules/bibliographic/api/editorial.py | Modificado: Accept no GET público |
| apps/api/src/libris/modules/bibliographic/api/representations.py | Modificado: negociação, MIME, Vary e ETags próprios |
| apps/api/src/libris/modules/bibliographic/api/listing.py | Novo: dez handlers tipados |
| apps/api/src/libris/modules/bibliographic/api/schemas/listing.py | Novo: parâmetros fechados e páginas Pydantic |
| apps/api/src/libris/modules/bibliographic/application/catalog.py | Modificado: snapshot autorizado na CatalogView |
| apps/api/src/libris/modules/bibliographic/application/catalog_editorial.py | Modificado: leitura pública com snapshot, preservando adaptador anterior |
| apps/api/src/libris/modules/bibliographic/application/catalog_listing.py | Novo: autorização, cursor e projeção limitada |
| apps/api/src/libris/modules/bibliographic/infrastructure/catalog_query.py | Novo: statement SQLAlchemy único |
| tests/api/test_catalog_listing.py | Novo: 38 casos sem banco |
| tests/integration/test_catalog_listing_postgres.py | Novo: 10 casos PostgreSQL reais |
| tests/api/test_catalogographic_http.py | Modificado: operações reais, CORS, OpenAPI e 401 |
| tests/api/test_catalogographic_contract_specification.py | Modificado: inventário OpenAPI |
| tests/api/test_startup.py | Modificado: inventário OpenAPI |
| README.md | Modificado: capacidade M05.06 e link |
| docs/architecture/catalogographic-http.md | Modificado: estado implementado e referência do contrato |
| docs/architecture/catalogographic-editorial-http.md | Modificado: integração com leitura pública |
| docs/architecture/semantic-serialization.md | Modificado: integração HTTP atual |
| docs/architecture/catalogographic-listing.md | Novo: contrato completo, exemplos, erros e limites |
| docs/decisions/0039-catalog-listing-representations.md | Novo: decisão de consulta/cursor/representações |
| docs/architecture/catalogographic-m0506-query-plan-2026-10-16.txt | Novo: SQL, EXPLAIN e índices observados |
| docs/architecture/catalogographic-m0506-verification-2026-10-16.md | Novo: este relatório e matriz de aceite |
