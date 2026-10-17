# Verificação M05.05 / issue #49 — 2026-10-16

Data local: America/Manaus. Relatório novo; não substitui evidências M03/M04/M05
anteriores. Implementação e testes locais, sem homologação institucional/produção.
[Contrato HTTP completo](catalogographic-editorial-http.md),
[ADR 0038](../decisions/0038-catalog-editorial-http.md).

## Diagnóstico e dependências confirmadas

Início em main, working tree limpo; HEAD `6731891 M05.04`. Consultas GitHub foram
somente leitura, sem sincronização, edição de issue ou PR. Números/conteúdos
confirmados na execução:

| Issue | Entrega confirmada no GitHub | Estado consultado | Evidência no código local |
| --- | --- | --- | --- |
| [#27](https://github.com/inacioigne/libris/issues/27) | M03.04.01 estados e transições | closed | domain/editorial.py, application/editorial.py; matriz fechada de sete comandos |
| [#28](https://github.com/inacioigne/libris/issues/28) | M03.04.02 proveniência, auditoria/versionamento | closed | HistoryService, AuditStore, restore_content, compare_graphs e migração 0003 |
| [#43](https://github.com/inacioigne/libris/issues/43) | M03.04.03 integração editorial transacional | closed | PostgresEditorialTransactions, EditorialStore, gate/CAS e migração 0004 |
| [#38](https://github.com/inacioigne/libris/issues/38) | M04.05 autorização backend por operação | closed | get_execution_context, AuthorizationGuard, POLICIES e ROLE_PERMISSIONS |
| [#41](https://github.com/inacioigne/libris/issues/41) | M04.08 auditoria de segurança | closed | módulo security_audit; continua separado da auditoria catalográfica |
| [#42](https://github.com/inacioigne/libris/issues/42) | M04.09 testes e homologação M04 | closed | testes identity, harness Keycloak e evidências M04 existentes; não rehomologados aqui |
| [#45](https://github.com/inacioigne/libris/issues/45) | M05.01 superfície HTTP v1 | closed | composição em main, dependências de sessão/contexto e Problem Details |
| [#46](https://github.com/inacioigne/libris/issues/46) | M05.02 DTO ↔ RDF | closed | serialization/adapters.py, graph_to_read, apply_update |
| [#47](https://github.com/inacioigne/libris/issues/47) | M05.03 CRUD/CAS persistente | closed | CatalogService, 15 rotas CRUD e ETag/If-Match |
| [#48](https://github.com/inacioigne/libris/issues/48) | M05.04 relações/validação HTTP | open | commit local M05.04 já contém capabilities, RelationshipService, pré-validação/perfis e testes |
| [#49](https://github.com/inacioigne/libris/issues/49) | M05.05 ciclo editorial/histórico HTTP | open | objeto desta implementação; issue remota preservada |

Fechamento de issue não foi usado como substituto da inspeção de código. Migrações
0001–0004 continuam experimentais; head vigente 0005_web_auth. Nenhuma migração,
perfil/SHACL ou dependência foi alterada. README, contratos de arquitetura, segurança,
SHACL/diagnósticos e ADRs pertinentes foram consultados antes da implementação.

## Matriz de implementação

| Requisito | Serviço/contrato reutilizado | Alteração necessária |
| --- | --- | --- |
| sete comandos explícitos | EditorialService.transition + TRANSITIONS | rotas literais; expected_operation opcional verificado sob transação |
| estado e ponteiros separados | EditorialRecord + CatalogView | EditorialStateRead e observação coerente sem inicializar legado |
| leitura pública | BibliographicService.read_public + política pública | rota pública isolada; política de bibliografia/autoridade conforme perfil persistido |
| revisões/snapshots/comparação | HistoryService + compare_graphs + serializador limitado | autorização/coleção e transporte HTTP, sem algoritmo de diff novo |
| histórico/auditoria | HistoryService.read_editorial/list_events/read_event | consultas/cursor existentes; permissões independentes |
| restauração | BibliographicService.restore_content | body limitado, ETag existente, CAS de ambas as versões e proveniência do servidor |
| CAS/rollback/validação | PostgresEditorialTransactions e stores M03 | nenhuma persistência paralela; diagnóstico de publicação no Problem Details existente |
| snapshots legados incompletos/compostos | RevisionStore + parser limitado e tipo da raiz | conferência da raiz sem exigir projeção Read corrente para consultas históricas |

## Rastreabilidade dos critérios

Abreviações: **H** = tests/api/test_editorial_http.py; **P** =
tests/integration/test_editorial_http_postgres.py; **E** =
tests/integration/test_editorial_postgres.py; **C** =
tests/integration/test_catalog_http_postgres.py; **A** =
tests/integration/test_audit_postgres.py. Os nomes abaixo identificam testes
comportamentais executáveis, não apenas presença de rotas.

| Critério | Situação | Evidência automatizada |
| --- | --- | --- |
| Transições editoriais e perfis dos cinco tipos | Concluído | P::test_http_publication_candidate_history_restore_and_archive (5 tipos); E::test_publication_all_supported_types_with_local_reference_integrity; suíte de domínio test_editorial.py |
| Histórico autorizado, snapshots e paginação | Concluído | H::test_editorial_anonymous_and_insufficient_permissions_before_storage; P::test_http_live_keyset_pages_and_wrong_resource_events; P::test_http_history_reads_incomplete_legacy_without_rewriting_or_inventing_events |
| Leitura pública isolada (A–E) | Concluído | P::test_http_publication_candidate_history_restore_and_archive; P::test_http_public_r1_stays_until_r2_published_and_failed_integrity_rolls_back; P::test_http_shacl_failure_preserves_publication_and_safe_diagnostics |
| CAS conteúdo/estado e concorrência real | Concluído | P::test_http_two_requests_with_same_etag_have_one_winner (submit/restore); P::test_http_publish_races_with_edit_and_keeps_exact_approval; E::test_concurrent_sessions_reject_stale_decisions; C::test_two_http_sessions_race_through_persistent_cas |
| Publicação da revisão aprovada exata | Concluído | P::test_http_trusted_transition_actor_and_exact_selected_revision; P::test_http_publish_races_with_edit_and_keeps_exact_approval; E::test_local_dependency_cannot_change_between_validation_and_commit |
| SHACL/integridade e rollback | Concluído | P::test_http_shacl_failure_preserves_publication_and_safe_diagnostics; P::test_http_public_r1_stays_until_r2_published_and_failed_integrity_rolls_back; E::test_invalid_legacy_shacl_publication_preserves_diagnostics_and_state; E::test_unclassified_required_reference_blocks_publication_atomically |
| Restauração imutável sem publicação | Concluído | P::test_http_publication_candidate_history_restore_and_archive; P::test_http_late_audit_failure_rolls_back_state_snapshot_and_event (restore); A::test_content_history_restore_and_authorization |
| Auditoria no mesmo commit | Concluído | P::test_http_late_audit_failure_rolls_back_state_snapshot_and_event; E::test_transition_failures_roll_back_in_fresh_session; C::test_http_transaction_failures_roll_back; testes de triggers em A |
| Ator OIDC confiável/RBAC sem elevação | Concluído | P::test_http_effective_role_matrix; P::test_http_trusted_transition_actor_and_exact_selected_revision; H::test_transition_rejects_client_identity_and_expectations; regressão identity/test_identity.py e identity/test_authorization.py |
| Comparação RDF por isomorfismo | Concluído | P::test_http_publication_candidate_history_restore_and_archive; test_audit_history.py e comparação semântica de A |
| Erros, limites e OpenAPI | Concluído | H::test_editorial_openapi_contract; H::test_event_cursor_input_is_bounded_and_timezone_aware; P::test_http_editorial_and_restore_require_existing_if_match_contract; testes de OpenAPI das entregas anteriores atualizados para as rotas reais |
| Documentação e evidência PostgreSQL real | Concluído | contrato HTTP, ADR 0038 e comandos/resultados abaixo |

## Ambiente isolado e comandos

PostgreSQL 17.11, imagem local postgres:17-bookworm, container exclusivo
`libris-issue49-20261016`, label libris.verification=issue49. Dados em tmpfs
`/var/lib/postgresql/data`, sem volumes de trabalho e com porta dinâmica publicada
apenas em loopback (32768 nesta execução). Autenticação trust restrita ao ensaio
local descartável; nenhum segredo de trabalho lido/exposto. Banco criado junto do
container: `libris_issue49_test`. O ensaio final de compatibilidade recriou o container descartável com o mesmo
nome/porta, novamente sem volumes e com banco novo. Antes de cada upgrade, executado explicitamente
`SELECT current_database(), version()` e conferido esse nome.

URL usada somente no ambiente dos comandos:
`postgresql+asyncpg://postgres@127.0.0.1:32768/libris_issue49_test`.

Comandos de migração, em apps/api:

```bash
DATABASE_URL=<url-descartavel> uv run alembic upgrade head
DATABASE_URL=<url-descartavel> uv run alembic current
uv run alembic heads
DATABASE_URL=<url-descartavel> uv run alembic check
```

Upgrade passou; current/heads retornaram 0005_web_auth; check retornou
`No new upgrade operations detected.` Não houve downgrade, DDL no startup,
create_all nem operação em banco/volume existente. Testes de migração destrutiva
não foram necessários para uma entrega sem mudança de schema e não foram rodados.

Ferramentas: Python 3.13.15, uv 0.12.21; Node 24.16.0 existente via NVM para check.sh.
uv Snap e Docker exigiram execução fora do sandbox: confinamento Snap e acesso ao
socket falharam na tentativa inicial. Escalonamento autorizado permitiu execução;
nenhuma instalação ou mudança de locks. Não foram bloqueios finais.

Resultados PostgreSQL concluídos (sem somar testes repetidos):

| Comando em apps/api | Resultado |
| --- | --- |
| `TEST_DATABASE_URL=<url-descartavel> uv run pytest -c pyproject.toml ../../tests/integration/test_editorial_http_postgres.py ../../tests/integration/test_editorial_postgres.py ../../tests/integration/test_catalog_http_postgres.py ../../tests/integration/test_audit_postgres.py ../../tests/integration/test_authorization_postgres.py ../../tests/integration/test_catalog_capabilities_postgres.py` | 112 passed, 0 failed, 0 skipped; 117,82 s; 1.788 avisos RDFLib |
| `TEST_DATABASE_URL=<url-descartavel> uv run pytest -c pyproject.toml -q ../../tests/integration/test_editorial_http_postgres.py` — última execução, com todos os casos novos de legado e ator | 26 passed, 0 failed, 0 skipped; 39,57 s; 722 avisos RDFLib |
| `uv run pytest -q ../../tests/api/test_catalogographic_contract_specification.py ../../tests/api/test_editorial_http.py` | 164 passed, 0 failed, 0 skipped; 34,11 s; 1 aviso Starlette/httpx |
| `uv run ruff check . ../../tests` | passou |
| `uv run mypy src` | passou, 102 arquivos |

A regressão de 112 testes precedeu os dois últimos casos adicionais; a última
execução dos 26 testes HTTP PostgreSQL inclui esses casos e a seleção da política
pública por tipo. Há sobreposição entre comandos; 112 + 26 não representa total de
testes distintos. Nenhum teste de integração dessa seleção foi skipped.

Rodadas intermediárias detectaram listas antigas de paths OpenAPI em três testes,
ordem de autorização/tipo que devolvia 403 para coleção errada, um erro de variável
no teste novo e uma injeção que acionava ownership antes de SHACL. Foram corrigidos
mantendo assertivas de comportamento. Uma rodada PostgreSQL com suítes simultâneas
no mesmo banco descartável também invalidou contagens globais em dois testes;
a regressão final foi executada sozinha e passou. Não houve mudança para ocultar
falhas ou substituir PostgreSQL por mocks. A primeira execução de check.sh parou
na API com 1.913 passed e 2 failed (listas OpenAPI antigas); a reexecução integral
final passou, conforme os resultados abaixo.

### Verificação completa final

Na raiz, executado `PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh`.
Exit code **0**. O PATH seleciona apenas o Node 24 existente.

| Etapa executada pelo script | Resultado final |
| --- | --- |
| `cd apps/api && uv run pytest` | **1.915 passed, 0 failed, 0 skipped**, 212,96 s; 513 avisos existentes Starlette/httpx e RDFLib |
| `uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py` | **All checks passed** |
| `uv run mypy src` | **Success**, 102 arquivos |
| `cd apps/web && npm test` | **167 passed, 0 failed, 0 skipped** |
| `npm run build` | **passou**, Next.js 16.4.0, compilação e geração completas |
| `npm run typecheck` | **passou**, tsc --noEmit |
| `docker compose --env-file .env.example config --quiet`, com valores efêmeros do script | **passou**, validação estática sem iniciar serviços |
| `git diff --check` | **passou** |

Não há bloqueio final dos comandos solicitados. O frontend não foi alterado.
A última mudança na conferência da raiz histórica foi verificada pelos 26 testes
HTTP PostgreSQL e pela tipagem/lint finais. A regressão PostgreSQL ampla de 112
casos também passou na execução separada indicada acima. Não somar as contagens
sobrepostas nem considerar testes não executados como aprovados.

Logs desta sessão, fora do controle de versão: /tmp/libris-issue49-check-final.log,
/tmp/libris-issue49-postgres-final.log e /tmp/libris-issue49-http-legacy-final.log.

Os containers efêmeros do ensaio foram parados/removidos após conferir nome, label
e tmpfs. Nenhum volume foi criado/removido e nenhum banco de trabalho foi tocado.
A segunda instância substituiu somente o primeiro ambiente descartável já removido.

## Limites e riscos residuais

- OIDC nos testes HTTP PostgreSQL usa override do get_current_actor com
  AuthenticatedActor sintético confiável; assinatura/issuer/audience/JWKS/RBAC
  continuam cobertos pela suíte padrão M04. Não há nova homologação Keycloak real,
  navegador ou produção nesta entrega. Evidência anterior da #42 continua datada.
- Falhas após INSERT são injetadas para testar rollback físico em PostgreSQL;
  stores/commit/CAS não são substituídos por memória. A falha SHACL do teste HTTP
  usa contexto inválido injetado; a rejeição de snapshot legado inválido persistido
  também é testada diretamente em E. Nenhuma simulação é apresentada isoladamente
  como prova de integridade transacional.
- Paginação é viva, determinística por chave; não garante snapshot global entre
  páginas. Nova inserção com chave anterior ao cursor exige navegação nova.
- Gate conservador, custo de comparação RDF e carregamento do snapshot corrente
  para conferir coleção/ETag mantêm os limites documentados. Consultas históricas
  não exigem um Read corrente válido nem inicializam metadados legados.
- Mapa externo confiável do serviço interno não é entrada HTTP. Publicação com
  referência não local sem classificação é bloqueada. Não presume existência remota.
- Esquema experimental, sem nova homologação institucional dos perfis. Descoberta/
  listagens/Accept (#50), integração M05 completa (#51), editor M07 e circulação
  permanecem fora do escopo.

## Arquivos e revisão local

- `api/editorial.py` e `api/schemas/editorial.py` do módulo bibliographic: 17
  operações, DTOs de comando/estado/páginas e validação de cursor.
- `application/catalog_editorial.py`: adaptação autorizada de coleção e ETag aos
  serviços existentes; consultas legadas sem projeção DTO obrigatória, inclusive protótipo composto.
- `application/editorial.py`: expectativa opcional de comando literal dentro da
  transação, sem alterar matriz de domínio ou chamadores anteriores.
- `application/service.py`: seleção da política pública bibliográfica/autoridade
  conforme o perfil da revisão pública armazenada.
- `bibliographic/api/router.py`: inclusão do roteador editorial.
- `libris/api/problems.py`: preserva diagnóstico tipado da publicação rejeitada.
- `libris/api/security.py`: CORS somente dos métodos/caminhos novos reais.
- `tests/api/test_editorial_http.py` e `tests/integration/test_editorial_http_postgres.py`:
  cobertura HTTP/autorização e PostgreSQL real; três testes OpenAPI anteriores
  atualizados em test_catalogographic_http.py, test_catalogographic_contract_specification.py
  e test_startup.py.
- README, contrato catalográfico/HTTP, lifecycle/persistence e proveniência: referências
  ao escopo disponível. Novos contrato HTTP editorial, ADR 0038 e este relatório.

Working tree local em main, sem staging. Nenhuma branch, commit, push, PR, merge,
rebase, cherry-pick, reset, stash, clean ou atualização remota. Estado e diff finais
conferidos abaixo. HEAD permanece 6731891; não houve sincronização do remoto.

O build atualizou next-env.d.ts automaticamente de tipos dev para tipos de
produção. Essa alteração gerada foi desfeita no próprio arquivo, preservando seu
conteúdo inicial e mantendo o diff sem mudanças de frontend. Após essa restauração,
`cd apps/web && npm run typecheck` foi executado novamente e passou (exit code 0).

## Git final

```text
$ git branch --show-current
main
```

```text
$ git status --short
 M README.md
 M apps/api/src/libris/api/problems.py
 M apps/api/src/libris/api/security.py
 M apps/api/src/libris/modules/bibliographic/api/router.py
 M apps/api/src/libris/modules/bibliographic/application/editorial.py
 M apps/api/src/libris/modules/bibliographic/application/service.py
 M docs/architecture/catalogographic-contract.md
 M docs/architecture/catalogographic-http.md
 M docs/architecture/editorial-lifecycle.md
 M docs/architecture/editorial-persistence.md
 M docs/architecture/provenance-audit-versioning.md
 M tests/api/test_catalogographic_contract_specification.py
 M tests/api/test_catalogographic_http.py
 M tests/api/test_startup.py
?? apps/api/src/libris/modules/bibliographic/api/editorial.py
?? apps/api/src/libris/modules/bibliographic/api/schemas/editorial.py
?? apps/api/src/libris/modules/bibliographic/application/catalog_editorial.py
?? docs/architecture/catalogographic-editorial-http.md
?? docs/architecture/catalogographic-m0505-verification-2026-10-16.md
?? docs/decisions/0038-catalog-editorial-http.md
?? tests/api/test_editorial_http.py
?? tests/integration/test_editorial_http_postgres.py
```

```text
$ git diff --stat
 README.md                                          |  6 ++-
 apps/api/src/libris/api/problems.py                |  7 ++-
 apps/api/src/libris/api/security.py                | 14 ++++++
 .../src/libris/modules/bibliographic/api/router.py |  3 ++
 .../modules/bibliographic/application/editorial.py | 11 +++++
 .../modules/bibliographic/application/service.py   |  7 +--
 docs/architecture/catalogographic-contract.md      |  9 ++++
 docs/architecture/catalogographic-http.md          | 55 ++++++++++++----------
 docs/architecture/editorial-lifecycle.md           |  7 +++
 docs/architecture/editorial-persistence.md         |  8 ++++
 docs/architecture/provenance-audit-versioning.md   |  8 ++++
 .../test_catalogographic_contract_specification.py |  9 ++++
 tests/api/test_catalogographic_http.py             | 14 +++++-
 tests/api/test_startup.py                          |  9 ++++
 14 files changed, 134 insertions(+), 33 deletions(-)
```

O diff --stat lista somente os arquivos rastreados: 14 files changed, 134 insertions(+), 33 deletions(-).
Os oito arquivos novos estão como ?? no status e não foram adicionados ao índice.
Total: 22 arquivos novos/modificados, todos preservados localmente e sem staging.
Nenhuma operação Git proibida foi executada; a issue remota permanece sem alteração.
