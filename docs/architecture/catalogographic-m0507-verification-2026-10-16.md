# Verificação M05.07 / #51 — 2026-10-16

Data local America/Manaus; logs UTC podem indicar 2026-10-17.
Entrega exclusivamente no workspace local da branch `main`.
HEAD base: `b1d3464f290a3ff1e44d10270494c5a2f8bb12d6`.
Nenhum resultado histórico de M03/M04/M05 foi sobrescrito.

## Fontes e levantamento

Issue [#51](https://github.com/inacioigne/libris/issues/51) consultada integralmente,
aberta e sem comentários. Dependências #45–#50 (M05.01–06), #42 (M04.09) e #29–#31
consultadas com seus comentários disponíveis pelo conector GitHub, somente leitura.
O estado fechado das dependências não foi usado como prova de execução.

Referências: AGENTS.md, README, overview/domains, contrato catalográfico v1,
HTTP, testing/conformance-matrix/test-inventory v1, lifecycle/persistence editorial,
autorização por operação, segurança HTTP, serialização e extensões semânticas;
ADRs de identidade/revisões/ownership/relações/serialização/editorial/autorização e
0036–0039. Inspecionados composição FastAPI, handlers, DTOs, serviços catalográficos,
identity/JWT/roles, stores, migrações e testes API/integration/fixtures.

`git branch --show-current`, `git status --short`, `git diff --stat` e
`git diff --cached --stat` confirmaram inicialmente `main`, workspace e índice limpos.
Não havia alterações locais preexistentes. Nenhum pull/staging/stash/commit/push/PR,
troca/criação de branch, merge/rebase/reset/clean ou alteração remota foi executado.

O levantamento confirmou rotas reais para os cinco tipos, relações, pré-validação,
perfis, sete transições, revisões, auditoria, restauração e listagens. Os testes
existentes já verificavam CRUD, rollback físico e publicação. Lacunas desta entrega:
OIDC assinado nas rotas de catálogo, confidencialidade de todas as consultas
auxiliares, autoridades compartilhadas via HTTP, CAS concorrente parametrizado
nos cinco tipos, corpus institucional pelo transporte e reprodução isolada sem skips.
Também faltava declarar o formato Problem Details no erro 406 do OpenAPI.

## Matriz de rastreabilidade

Abreviações de caminhos, relativos à raiz:

- H: `tests/integration/test_catalog_http_postgres.py`.
- C: `tests/integration/test_catalog_capabilities_postgres.py`.
- E: `tests/integration/test_editorial_http_postgres.py`.
- L: `tests/integration/test_catalog_listing_postgres.py`.
- A: `tests/integration/test_catalog_acceptance_postgres.py` (novo).
- U: `tests/api/identity/test_identity.py`.
- V: `tests/api/test_catalog_capabilities.py`.
- O: `tests/api/test_catalogographic_http.py`.

| Requisito #51 | Contrato / implementação existente | Testes existentes | Lacuna / ação nesta entrega | Evidência executável final |
| --- | --- | --- | --- | --- |
| A: cinco tipos, Create/Read/PATCH, UUID/URI, ETag/Location | HTTP v1; router.py; CatalogService; DTO↔RDF | H::test_persistent_http_lifecycle; H::test_http_rejections_leave_persistence_unchanged | Integrar cadeia de identidade assinada e rejeição de alvos ausentes dos cinco tipos | A::test_signed_role_matrix_and_editorial_actor; A::test_validation_missing_references_and_no_physical_delete; H, todos parametrizados |
| B: Work↔Instance, Instance↔Item, Work→Agent/Subject; integridade | ADRs 0015/0018/0037; RelationshipService, resolvedor PostgreSQL | C::test_inverses_cycles_and_target_types; C::test_relationship_writes_all_five_entities; H::test_local_references_resolved_in_the_write_transaction | Autoridade/assunto locais compartilhados entre dois Works; remoção isolada, snapshot histórico e lote de falha sem escrita parcial | A::test_http_shared_authorities_preserve_owners_and_atomic_link_batch; sessão independente via state após falha |
| B: cardinalidade, tipos e fixtures institucionais | Perfis/SHACL históricos; prevalidate/validate_catalog; parser limitado | test_relationships.py; test_catalogographic_contract.py; corpus/manifest | Exercitar os 28 arquivos pelo endpoint real, com composição/inversas explícitas na cópia de teste | V::test_institutional_corpus_through_http_validation; manifesto preservado; 13 conformes e 15 inválidos |
| C: JWT ausente/malformado/expirado/assinatura/issuer/audience/chaves | Resource Server OIDC; OIDCValidator; get_current_actor | U: testes de JWT, JWKS, throttle, falha/rotação e identidade | Negativos aplicados às cinco rotas de criação; negar antes do storage | U::test_catalog_rejects_invalid_oidc_before_storage: 40 casos; mocks só de discovery/JWKS |
| C: RBAC, leitura/edição/publicação/admin; cliente não define ator | POLICIES/ROLE_PERMISSIONS; HumanContext e guard existentes | O: negações antes do banco; E::test_http_effective_role_matrix | Token assinado sem permissões/reader/publisher não é promovido; testar seis papéis reais e ator de cada transição | U::test_catalog_signed_roles_cannot_be_promoted_by_client: 15 casos; A::test_signed_role_matrix_and_editorial_actor: cinco tipos |
| D: revisão correta/ausente/obsoleta, ETag e CAS | ADRs 0011/0036; precondições HTTP + CAS transacional | H::test_http_rejections_leave_persistence_unchanged; E::test_http_two_requests_with_same_etag_have_one_winner | Ampliar corrida de dois PATCH para cinco tipos, com barreira Event e sessões próprias | H::test_two_http_sessions_race_through_persistent_cas: cinco tipos; um 200, um 412, só R2/evento vencedor |
| D: transação revertida, conteúdo/relações/revisão/estado/auditoria | BibliographicService/RelationshipService/PostgresEditorialTransaction; stores, FK e commit | H::test_http_transaction_failures_roll_back; H::test_post_advance_rejection_is_atomic; C::test_relationship_failure_rolls_back; E::test_http_late_audit_failure_rolls_back_state_snapshot_and_event | Reexecutar garantias físicas existentes e acrescentar lote relacional misto válido/inexistente | Suíte PostgreSQL completa; leituras state e consultas de revisões/contagens em novas sessões depois das falhas; sem SQLite/sleeps de corrida |
| E: transições, revisão aprovada, candidata, proveniência e imutabilidade | ADRs 0026/0028/0038; comandos HTTP literais; public_view | E::test_http_publication_candidate_history_restore_and_archive; E::test_http_public_r1_stays_until_r2_published_and_failed_integrity_rolls_back | Identidades assinadas distintas para submit/approve/publish; não divulgação inspecionada em payload e headers | A::test_signed_role_matrix_and_editorial_actor; A::test_confidentiality_all_auxiliary_paths_and_formats: draft/approved/candidate, anônimo/reader/sem concessões |
| E: endpoints auxiliares/listagens/formatos sem vazamento | HTTP editorial/listing; public_revision exata; sem expansão de alvos | L::test_list_and_export_exact_published_revision; E: withdrawn/archived e histórico | Cobrir também relações/inversas, revisão individual, snapshot, compare e evento individual nas negações | A::test_confidentiality_all_auxiliary_paths_and_formats: 11 caminhos por tipo, headers sem ETag/Location em erros, JSON/JSON-LD/Turtle públicos |
| F: PostgreSQL real isolado e execução sem skips | Alembic HEAD e migrações experimentais existentes | Integração opt-in com quatro URLs; execução manual sujeita a skips | Novo scripts/test-postgres.sh: porta dinâmica, tmpfs, quatro bancos, instalação explícita, JUnit recusa skips e cleanup por ID | Execução completa registrada abaixo; dois testes Keycloak deliberadamente fora da seleção |
| Contrato v1, RDF e extensões | DTOs fechados; Graph canônico; parse_representation/serialize_graph | L::test_list_and_export_exact_published_revision (cinco tipos); H::test_patch_extensions_validation_and_public_snapshot; regressão M03 | Reexecutar sem alterar releases, snapshots, UUID/URIs ou fixtures | Isomorfismo RDF nas suítes API/PostgreSQL; extensões de idioma/datatype/IRI sobrevivem persistência/PATCH/exportação; seed de extensões pela camada interna explicitamente separado do comportamento HTTP |
| OpenAPI e Problem Details | main.py/router e hook install_problem_handlers | O::test_openapi_only_describes_real_operations_and_schemas; testes de contrato v1 | Corrigir MIME/schema de todos os erros já declarados, inclusive 406, preservando status/headers/rotas | O::test_openapi_declared_errors_match_problem_details_transport; runtime 406 e Vary em L |
| Documentação e evidências | Contratos HTTP/editorial/listagem existentes | Documentos/ADRs e relatórios históricos preservados | Guia consolidado, exemplos cinco tipos, permissões, erros, concorrência, níveis OIDC e reprodução | catalogographic-api-testing.md; README/HTTP com links; este relatório separado |

## Disponibilidade e limites deliberados

| Operação / garantia | Estado e tratamento |
| --- | --- |
| POST/GET/PATCH, relações, validação, histórico, transições, restore, listagens e RDF individual | Disponível e exercitado pelas rotas implementadas; OpenAPI sem placeholders |
| Remoção física / DELETE | Não implementado por decisão explícita de #47; cinco testes confirmam 405, inclusive admin com bibliographic:delete |
| Retirada e arquivamento | Disponíveis como transições; não apagam UUID/URI/snapshots; E e L verificam invisibilidade posterior |
| Inversas graváveis, edição arbitrária de perfis/SHACL | Não aplicável ao contrato de escrita; inversas são derivadas e releases são somente consulta |
| Upload RDF por CRUD, DTO genérico de extensão, reconciliação remota, tombstones/resolvedor | Não implementados; pré-validação RDF não é ingestão; propriedades importadas já persistidas usam Graph integral |
| Login/refresh/senhas na API | Não aplicável ao Resource Server; fluxo externo/BFF permanece M04 |
| Keycloak real, navegador/produção | Harness existente permanece opt-in; nenhuma execução real Keycloak nesta entrega |
| Editor, MARC21, Elasticsearch, inventário/circulação, deploy | Fora do escopo #51; sem rotas artificiais |

## Execução e resultados

Ambiente e comandos finais são registrados após término dos processos. Logs em
`/tmp/libris-issue51-*` são auxiliares locais, sem valores de tokens versionados.
As contagens focadas são subconjuntos das suítes completas, nunca somas adicionais.

Baseline: `PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh`
concluiu com exit 0: **1.953 testes API**, **167 testes web**, Ruff, mypy em 106
arquivos, build, typecheck e Compose aprovados. Log `/tmp/libris-issue51-baseline.log`.

Rodadas focadas:

- OIDC novo: **55 passed**, 115 deselected, 0 skipped; `/tmp/libris-issue51-oidc.log`.
- OpenAPI: **2 passed**, 54 deselected, 0 skipped; `/tmp/libris-issue51-openapi.log`.
- Primeira aceitação PostgreSQL: **10 passed / 1 failed**, sem skips. O teste novo
  enviava role da contribuição como string; o DTO exige `{uri:...}`. Corrigido o
  teste, preservando contrato/serviço. Essa rodada não comprova aprovação completa.
- Primeira rodada do corpus HTTP: **27 passed / 1 failed**. O Subject isolado foi
  enviado com perfil monográfico inaplicável; corrigida a seleção do perfil de
  autoridades. Não houve alteração de shape/fixture ou flexibilização do handler.
- Corpus HTTP final: **28 passed**, 25 deselected, 0 skipped;
  `/tmp/libris-issue51-corpus-final.log`.

`bash scripts/test-postgres.sh` concluiu com **exit 0**, **167 passed**, **0 failed**,
**0 skipped**, **2 deselected** (os dois testes Keycloak real), em 200,69 segundos.
Log `/tmp/libris-issue51-postgres.log`; JUnit
`/tmp/libris-postgres-junit.hAxIpZ.xml`: tests=167, errors=0, failures=0, skipped=0.
O executor conferiu essas contagens e removeu automaticamente seu container.
As quatro bases foram criadas nessa execução; o banco principal recebeu HEAD e
os três bancos de migração começaram vazios. PostgreSQL 17-bookworm da imagem
local, dados em tmpfs, sem serviço Elasticsearch ou OIDC externo. A seleção inclui
CRUD, relações, editorial, concorrência, rollback, listagens, extensões, as 16
aceitações HTTP assinadas novas e regressões de migração/persistência M03/M04.

Python **3.13.15** e Node **24.16.0**. `uv run ruff check . ../../tests` e
`uv run mypy src` executados separadamente após as mudanças: lint aprovado e
**106 source files** sem problemas. `bash -n scripts/test-postgres.sh` aprovado.
Os cinco payloads mínimos do guia foram extraídos e validados por seus modelos
Create v1, substituindo somente os UUIDs ilustrativos. Links locais dos documentos
novos também foram conferidos por script somente-leitura.

Gate final:
`PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh`
concluiu com **exit 0**. Log `/tmp/libris-issue51-check-final.log`:

| Verificação final | Resultado |
| --- | --- |
| uv run pytest (suíte padrão offline) | **2.037 passed**, 0 failed, 0 skipped; 513 avisos, 206,98 segundos |
| uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py | Aprovado |
| uv run mypy src | Aprovado: 106 arquivos |
| npm test | **167 passed**, 0 failed |
| npm run build | Aprovado com Node 24.16.0 |
| npm run typecheck | Aprovado |
| docker compose --env-file .env.example config --quiet | Aprovado; credenciais efêmeras usadas apenas para validação estática |

Os 84 casos offline novos (55 OIDC/RBAC + 28 corpus + 1 OpenAPI) estão incluídos
nos 2.037; os 16 casos assinados e quatro parametrizações adicionais de corrida
estão incluídos nos 167 da integração. Nenhum teste reportado como skip foi
contado como integração executada. O arquivo next-env.d.ts regenerado pelo build
foi devolvido ao conteúdo original; não há alteração de frontend na entrega.

Revisão Git final: `main`; `git diff --check` sem erros; índice vazio em
`git diff --cached --stat`. Todos os onze arquivos da entrega permanecem sem
staging e sem commits. Nenhum commit/push/PR ou alteração da issue foi realizado.

## Alterações e riscos

Código de produção limitado ao OpenAPI de erros: conteúdo de erros declarados agora
aponta para ProblemDetails também em 406, sem alterar autorização, transações,
status, DTOs ou novas rotas. Sem dependências, locks, migrations, perfis ou SHACL novos.
Novos testes/guia/runner e ampliação de testes existentes; nenhuma arquitetura nova
exige ADR nesta entrega. O gate pode regenerar next-env.d.ts; derivações de build
sem relação com a tarefa são restauradas ao conteúdo original antes da entrega.

Persistem homologação institucional dos perfis, Keycloak/produção nesta entrega,
benchmark em volume representativo e paginação sem snapshot global entre páginas.
Os avisos de depreciação preexistentes de Starlette/httpx e RDFLib continuam visíveis;
não se adicionaram bibliotecas para suprimi-los. Propriedades RDF externas são
preservadas, sem declarar homologação de toda ontologia complementar.

O primeiro ensaio Docker usou o volume anônimo padrão da imagem; o runner foi
ajustado para tmpfs nas rodadas seguintes. A origem exclusiva desse volume foi
comprovada por eventos create/mount/unmount do container etiquetado da #51. Sua
remoção foi inicialmente recusada pela revisão automática por interpretar AGENTS.md
como proibição de remoção de volumes. Após autorização explícita do usuário para
esse volume exato, nova inspeção confirmou ausência de containers vinculados e
`docker volume rm 0cfbe78f259d2e8304089c60e06003f9051c0ffc92be12cbf31695dce5b3c8f5`
concluiu com exit 0. A ausência do volume foi conferida na listagem posterior.
Nenhum volume preexistente ou banco de trabalho foi removido/modificado.

## Inventário local da entrega

| Arquivo | Alteração |
| --- | --- |
| apps/api/src/libris/api/problems.py | Declara ProblemDetails no conteúdo de todos os erros já presentes no OpenAPI |
| tests/api/identity/test_identity.py | 55 casos OIDC/RBAC nas rotas reais de criação dos cinco tipos |
| tests/api/test_catalog_capabilities.py | 28 fixtures institucionais pelo endpoint HTTP, sem DML |
| tests/api/test_catalogographic_http.py | Regressão do MIME/schema de erros declarados no OpenAPI |
| tests/integration/test_catalog_http_postgres.py | Corrida HTTP/CAS ampliada para cinco tipos |
| tests/integration/test_catalog_acceptance_postgres.py | Novo: 16 casos com JWT assinado, banco real, papéis, ator, confidencialidade, validação, referências e autoridades compartilhadas |
| scripts/test-postgres.sh | Novo: preparação/execução/cleanup de PostgreSQL exclusivo; recusa skips |
| docs/architecture/catalogographic-api-testing.md | Novo: guia de consumo, exemplos, níveis de evidência, erros e reprodução |
| docs/architecture/catalogographic-m0507-verification-2026-10-16.md | Novo: matriz, comandos, resultados e limitações desta execução |
| README.md | Referência ao guia, matriz e runner |
| docs/architecture/catalogographic-http.md | Referência à consolidação M05.07 e correção OpenAPI |
