# Verificação — M04.05 / issue #38

Data: **2026-10-13**, America/Manaus. Branch inicial: **main**.
HEAD inicial: **3f03eeb4ec12b4c01d6496e0ed43b258b8458d2e** (M04.04).
Working tree inicial vazio. Sem staging, commit, branch nova, sincronização remota,
push, PR ou alteração da issue. Este relatório registra uma nova execução;
nenhum relatório histórico foi modificado.

## Diagnóstico comprovado

AGENTS.md, README, contratos arquiteturais/catalográficos, identidade, baseline,
matriz, ameaças, critérios M04, editorial/proveniência e ADRs 0016/0026–0028/0030
examinados. Não existem AGENTS.md adicionais em apps/tests. Inspecionados git show
M04.01–M04.04 e git diff dos módulos API entre essas entregas: não introduziram
guard de aplicação geral; M04.02 ampliou validação OIDC, M04.03 implementou BFF,
sessões/refresh/PKCE, M04.04 implementou shell administrativo server-side.
Login não foi tratado como ausente: código Next.js e evidências datadas já existem,
com limites de navegador/produção. Não foram homologados novamente nesta entrega.

Consulta somente de leitura ao GitHub: [#38](https://github.com/inacioigne/libris/issues/38)
aberta, milestone 4/M04, corpo lido pelo conector; issues vigentes relacionadas
consultadas. O conteúdo da issue ainda descreve login/integração pendentes anteriores;
o checkout/evidências prevalecem. A primeira tentativa por web não recuperou a página;
o conector leu a issue posteriormente. Um argumento inválido inicial do conector foi
corrigido; nenhuma operação remota de escrita ocorreu.

Lacunas iniciais: create/revise/read sem RBAC interno; ExecutionActor apenas de
registro de autoria; admin com crescimento automático pelo enum; controles de
histórico/editorial próprios e falta de contexto técnico com allowlist.
OIDC/JWT/JWKS, Hash de ator, sete operações, validação, CAS e auditoria M03 reutilizados.

## Implementação efetiva

[Contrato vigente](operation-authorization.md), [ADR 0031](../decisions/0031-operation-authorization.md).

- POLICIES/Operation/OperationPolicy/ResourceContext: política tipada fechada por ação,
  tipo de recurso, permissões conjuntas, modalidade humana/técnica/pública e projeção.
- HumanContext: ator autenticado propagado pelo adaptador OIDC/HTTP; valida coerência,
  sem prometer que a construção de objeto Python autentica alguém.
- TechnicalContext: identidade service/automated, origem interna, concessões e allowlist
  explícitas; decisões editoriais humanas e SYSTEM_ADMIN recusados.
- AuthorizationGuard: instância injetável, sem FastAPI, singleton ou consulta a tabelas;
  missing context/unknown operation/recurso incompatível/conjunção incompleta negados.
- BibliographicService: create/revise/read/restore_content protegidos, sem actor=None
  privilegiado. Kind persistido verificado antes de initialize/CAS. Público seleciona
  revisão publicada exata; candidata/legado/retirada/arquivamento não são expostos.
- HistoryService/EditorialService: guard comum, autorização prévia à sessão quando
  possível; decisão editorial exata revalidada no estado bloqueado. OPERATION_PERMISSIONS
  é visão derivada da política. Não se recriaram a máquina de estados ou transações.
- ROLE_PERMISSIONS: seis papéis/17 concessões mantidos; mapa imutável; admin enumerado.
- HTTP: get_current_actor/require_permissions preservados, get_execution_context
  acrescentado; PermissionDenied gera 403 pelo Problem Details 1.0. Exceção específica
  EditorialPermissionDenied mantém CatalogError/código editorial internamente e gera
  403; CatalogError genérico legado continua com seu fallback 422.
- Fixtures legítimas passam contexto técnico/humano explícito; legado nulo é representado
  por inserção em stores no banco descartável, sem endpoint/modo legado de aplicação.

Nenhuma dependência/lock, perfil/shape/DTO, frontend ou migração foi alterado.
Nenhum evento histórico foi reescrito ou sintetizado. Não há CRUD M05, credentials
M2M, novas tabelas de permissões, policy engine, framework ou serviço paralelo.

## Comandos e resultados

Executados antes de editar: git branch --show-current; git status --short;
git rev-parse HEAD; git log -12 --oneline. Branch main e status vazio.
Python 3.13.15; Node 24.16.0 existente via NVM; dependências travadas existentes.

| Comando | Resultado final |
| --- | --- |
| cd apps/api; uv sync --locked | passou: 83 pacotes resolvidos, 82 conferidos |
| uv run pytest ../../tests/api/identity | 333 passaram; zero falhas/skips |
| uv run pytest ../../tests/api/test_editorial.py | 97 passaram; teste adicional de compatibilidade posteriormente acrescentado, 98 na regressão específica |
| uv run pytest ../../tests/api/test_audit_history.py | 102 passaram; zero falhas/skips |
| uv run pytest ../../tests/api/test_catalogographic_contract_specification.py ../../tests/api/test_editorial.py | 138 passaram após corrigir adaptação HTTP; zero falhas/skips |
| uv run pytest | execução inicial: 1260 passaram; final pelo gate: 1524 passaram, zero falhas/skips, 476 avisos, 131,75 s |
| uv run ruff check . ../../tests | passou |
| uv run mypy src | passou: 78 arquivos |
| uv run alembic upgrade head, somente no PostgreSQL temporário | passou; head 0004_semantic_editorial |
| uv run pytest -c pyproject.toml ../../tests/integration, somente nos bancos temporários | final: 63 passaram, zero falhas, 1 skip Keycloak real, 259 avisos, 35,80 s |
| PATH com Node 24; bash scripts/check.sh | exit 0: 1524 API; Ruff; mypy 78 arquivos; 91 web; build Next.js; typecheck; Compose |
| git diff --check | passou nas inspeções; ver estado final abaixo |

Execuções intermediárias, sem apagar evidências negativas:

1. uv sync no sandbox falhou por snap-confine/AppArmor; executado com escalonamento
   autorizado, assim como verificações/Docker. Nenhuma rejeição da revisão automática.
2. Primeiros testes direcionados: 268 passaram, 1 falha por expectativa ValueError;
   corrigida para a nova recusa tipada PermissionDenied.
3. Novos testes: 527 passaram, 3 falharam em fixtures que montavam estados approved/
   published/withdrawn inválidos; corrigidas sem relaxar domínio. Suíte nova final: 253.
4. PostgreSQL inicial: 61 passaram, 1 falhou na expectativa de actor_type=None para
   uma nova revisão técnica autorizada, 1 skip. Fixture corrigida para SERVICE;
   identidade técnica explícita não foi convertida em autoria histórica inventada.
5. Gate ampliado inicial: 1522 passaram, 1 falhou no fallback catalográfico v1.
   Corrigido com EditorialPermissionDenied, mantendo a asserção histórica existente;
   nenhum teste de contrato foi removido/modificado para esconder a incompatibilidade.
6. Repetição PostgreSQL: 62 passaram, 1 falha por URI fixa repetida no novo teste,
   1 skip. Corrigido para ResourceIdentity.create com UUID/URI exclusivos; sem limpeza
   de dados/relaxamento da constraint de URI.
7. npm run typecheck foi invocado uma vez por engano na raiz (ENOENT sem package.json);
   reexecutado em apps/web após restaurar next-env.d.ts gerado pelo build.
8. Ruff inicialmente invocado da raiz aplicou configuração externa ao pacote; alterações
   de formatação automáticas da própria tarefa em testes não relacionados foram revertidas
   ao conteúdo HEAD via leitura de git show. Verificações finais usam configuração API.
   Uma invocação intermediária de mypy fora da configuração API não contou como gate.

Avisos de depreciação preexistentes: Starlette/httpx e RDFLib ConjunctiveGraph.
Nenhum aviso foi silenciado, skip contado como integração, segredo/token incluído no Git.

## PostgreSQL descartável e isolamento

Container exclusivo **libris-m0405-isolated-4b126fb0**, PostgreSQL 17-bookworm,
publicado somente em 127.0.0.1:55458, --rm, dados em tmpfs, sem volumes persistentes.
Credencial aleatória em arquivo privado /tmp modo 0600, sem saída do valor/URL.
Banco principal novo libris_rbac_test; bancos novos e distintos para cada execução
TEST_MIGRATION_DATABASE_URL e TEST_EDITORIAL_MIGRATION_DATABASE_URL.

Migrações 0001–0004 executadas explicitamente somente nesses bancos. Upgrade/downgrade
foram os testes existentes, em bancos exclusivos inicialmente vazios; banco principal
nunca foi rebaixado. Não usado SQLite. Não houve down -v, prune ou remoção de volumes.
Serviços libris-web/api/postgres/keycloak/elasticsearch de trabalho permaneceram ativos;
nenhuma conexão/migração/alteração de realm/usuário foi feita contra eles.

Regressão física: CAS de conteúdo/estado, rollback de auditoria, candidata independente,
aprovação/publicação, retirada/republicação/arquivamento, restore_content, autoria
histórica nula, tipos Work/Instance/Item/Agent/Subject, relações e snapshots imutáveis.
Novo test_authorization_postgres comprova em sessão nova que recusas não criaram
revisões/eventos nem alteraram estado; importador limitado cria conteúdo, mas não
revisa/lê editorialmente/submete por privilégio implícito.
Skip único: test_real_keycloak_code_pkce_and_resource_server, ativação TEST_KEYCLOAK_ENABLED ausente.
Sete casos puros do harness foram executados; skip não comprova provedor real.

## Critérios de aceite do pedido

Cada estado “atendido” se limita à implementação/testes desta issue; não significa
homologação institucional, navegador ou produção.

| Critério | Estado | Evidência concreta |
| --- | --- | --- |
| Permission e ROLE_PERMISSIONS consistentes/testados | atendido | test_six_roles_seventeen_permissions + inventário independente |
| Seis papéis preservados | atendido | EXPECTED e ROLE_PERMISSIONS; seis chaves iguais |
| Matriz RBAC parametrizada, concessões/recusas | atendido | 6 × 17 casos + uniões/unknown/ausente |
| Unknown operation deny-by-default | atendido | test_unregistered_or_untyped_operation_is_denied |
| Guard reutilizável independente HTTP | atendido | identity/application/authorization; injeção comprovada |
| Ação e contexto de recurso explícitos | atendido | POLICIES, ResourceContext, visibilidade pública, domínio editorial M03 |
| Chamadas internas protegidas | atendido | create/revise/read/history/editorial/restore recebem contexto |
| Público limitado à publicação efetiva | atendido | test_read_public_uses_selected_revision_never_current + workflow PG |
| Editorial/histórico com controles próprios | atendido | conjunções, papéis próprios, HistoryService |
| Técnico mínimo e explícito | atendido | TechnicalContext + concessões/allowlist independentes |
| Decisões humanas não concedidas ao serviço | atendido | test_technical_cannot_claim_human_operation + editorial preflight |
| actor_id histórico nulo preservado | atendido | test_revision_actor_postgres, testes migração legada, projeção pública |
| Sem token recusado | atendido | testes HTTP 401 com WWW-Authenticate |
| Papéis desconhecidos sem privilégios | atendido | matriz, uniões, HTTP unknown-role |
| Payload/headers sem elevação | atendido | test_operation_guard_ignores_forged_http_authority |
| Sem SYSTEM_ADMIN universal | atendido | todas as operações funcionais negadas com concessão administrativa isolada |
| Sem acesso a tabelas alheias | atendido | guard não depende de ORM; importação explícita identity/bibliographic |
| Contratos M03 preservados | atendido | regressão padrão/PG; fallback v1 intacto; perfis/DTO/migrações sem diff |
| Negação sem mutação | atendido | spies antes da sessão + test_authorization_postgres com persistência real |
| Documentação/relatório atualizados | atendido | contrato vigente, identidade/matriz/saída, ADR0031 e este relatório |
| Branch main local | atendido | branch inicial/final main |
| Nenhum commit novo | atendido | HEAD inicial/final igual |
| Nenhuma branch criada | atendido | nenhuma operação de criação/troca utilizada |
| Nenhum push/PR | atendido | nenhum comando Git/connector de escrita remota |

Não há critério parcialmente atendido dentro do escopo técnico #38. Limites abaixo
são capacidades explicitamente separadas no pedido, sem promessa de integração real.

## Pendências separadas e limites reais

- M05: endpoints CRUD, editor/adaptadores DTO↔Graph, autorização propagada pelo novo
  contexto; políticas delete/system não criam funcionalidades inexistentes.
- #39: governança, revogação e autenticação técnica M2M. Contexto técnico aqui é interno
  seguro sob composition root confiável, não credencial client_credentials operacional.
- Escopo institucional/propriedade: não existe contrato confiável; leitura editorial
  permanece restrita por capacidade de histórico, sem ownership fabricado/multi-tenant.
- #40–#42: segurança HTTP ampliada, eventos de segurança e homologação E2E/produção.
  Keycloak real/browser não foram reexecutados; frontend não alterado.
- Código/provedor/DBA comprometidos continuam fora das garantias. Classes Python,
  hashes e types não constituem fronteira criptográfica contra código no mesmo processo.

## Arquivos e responsabilidades

Novos:

- apps/api/src/libris/modules/identity/domain/authorization.py: operações/políticas/recursos.
- apps/api/src/libris/modules/identity/application/authorization.py: contextos/guard.
- tests/api/identity/test_authorization.py: matriz e aplicação/visibilidade/contextos.
- tests/integration/test_authorization_postgres.py: recusa sem efeito durável.
- docs/architecture/operation-authorization.md: contrato e exemplos reais.
- docs/decisions/0031-operation-authorization.md: decisão duradoura e confiança.
- docs/architecture/identity-m04-05-verification.md: esta evidência.

Modificados:

- identity/infrastructure/role_mapper.py: admin enumerado e mapa imutável;
  identity/application/service.py: permissão desconhecida/tipo de ator recusados;
  identity/domain/exceptions.py: descrição da exceção para contextos;
  identity/api/dependencies.py: contexto humano OIDC e guard injetável.
- bibliographic/application/service.py, history.py, editorial.py: enforcement e
  exceção editorial tipada; api/problems.py: tradução de PermissionDenied, sem alterar DTO.
- tests/api/identity/test_identity.py e test_editorial.py: spoof HTTP/preflight/fallback;
  test_audit_history.py: recusa tipada;
  test_catalog_diagnostics.py, test_semantic_extensions.py e test_shacl_validation.py:
  contextos legítimos nas regressões existentes.
- tests/integration/test_audit_postgres.py, test_diagnostic_transactions_postgres.py,
  test_editorial_postgres.py, test_entity_revisions_postgres.py,
  test_revision_actor_postgres.py e test_semantic_postgres.py: consumidores explícitos;
  autoria técnica atual e fixture histórica realmente nula.
- README.md e docs/architecture/catalogographic-contract.md, identity.md,
  security-access-matrix.md e security-m04-exit-criteria.md: enforcement vigente e limites.

## Inspeção final

Gate completo exit 0. O build gerou alteração em apps/web/next-env.d.ts;
restaurado somente esse arquivo gerado ao conteúdo HEAD, pois frontend não faz parte
da implementação. Typecheck foi executado novamente sobre o conteúdo restaurado.
O container tmpfs exclusivo foi encerrado e os arquivos privados /tmp de credenciais/
runner foram removidos. Inventário final confirmou os cinco containers libris de
trabalho ativos. Nenhuma remoção de volume ou mutação em banco de trabalho.

Git branch final **main**. HEAD final igual ao inicial. `git diff --check` passou;
`git diff --cached --name-only` vazio. Nenhuma branch criada, commit/staging/push/PR,
merge/rebase/cherry-pick/reset/stash/pull ou alteração de issue/remoto.
Todas as mudanças permanecem exclusivamente no working tree local da main.

Saídas finais (diff --stat inclui somente arquivos rastreados, não os sete novos):

```text
$ git branch --show-current
main
```

```text
$ git rev-parse HEAD
3f03eeb4ec12b4c01d6496e0ed43b258b8458d2e
```

```text
$ git status --short
 M README.md
 M apps/api/src/libris/api/problems.py
 M apps/api/src/libris/modules/bibliographic/application/editorial.py
 M apps/api/src/libris/modules/bibliographic/application/history.py
 M apps/api/src/libris/modules/bibliographic/application/service.py
 M apps/api/src/libris/modules/identity/api/dependencies.py
 M apps/api/src/libris/modules/identity/application/service.py
 M apps/api/src/libris/modules/identity/domain/exceptions.py
 M apps/api/src/libris/modules/identity/infrastructure/role_mapper.py
 M docs/architecture/catalogographic-contract.md
 M docs/architecture/identity.md
 M docs/architecture/security-access-matrix.md
 M docs/architecture/security-m04-exit-criteria.md
 M tests/api/identity/test_identity.py
 M tests/api/test_audit_history.py
 M tests/api/test_catalog_diagnostics.py
 M tests/api/test_editorial.py
 M tests/api/test_semantic_extensions.py
 M tests/api/test_shacl_validation.py
 M tests/integration/test_audit_postgres.py
 M tests/integration/test_diagnostic_transactions_postgres.py
 M tests/integration/test_editorial_postgres.py
 M tests/integration/test_entity_revisions_postgres.py
 M tests/integration/test_revision_actor_postgres.py
 M tests/integration/test_semantic_postgres.py
?? apps/api/src/libris/modules/identity/application/authorization.py
?? apps/api/src/libris/modules/identity/domain/authorization.py
?? docs/architecture/identity-m04-05-verification.md
?? docs/architecture/operation-authorization.md
?? docs/decisions/0031-operation-authorization.md
?? tests/api/identity/test_authorization.py
?? tests/integration/test_authorization_postgres.py
```

```text
$ git diff --stat
 README.md                                          |   4 +
 apps/api/src/libris/api/problems.py                |   4 +
 .../modules/bibliographic/application/editorial.py |  82 ++++++++---
 .../modules/bibliographic/application/history.py   |  80 ++++++++---
 .../modules/bibliographic/application/service.py   | 155 +++++++++++++++++++--
 .../libris/modules/identity/api/dependencies.py    |  11 ++
 .../libris/modules/identity/application/service.py |   6 +-
 .../libris/modules/identity/domain/exceptions.py   |   2 +-
 .../modules/identity/infrastructure/role_mapper.py | 111 +++++++++------
 docs/architecture/catalogographic-contract.md      |  14 +-
 docs/architecture/identity.md                      |  36 ++++-
 docs/architecture/security-access-matrix.md        |  37 +++--
 docs/architecture/security-m04-exit-criteria.md    |  21 +++
 tests/api/identity/test_identity.py                |  67 ++++++++-
 tests/api/test_audit_history.py                    |   2 +-
 tests/api/test_catalog_diagnostics.py              |  30 ++++
 tests/api/test_editorial.py                        |  48 +++++++
 tests/api/test_semantic_extensions.py              |  37 ++++-
 tests/api/test_shacl_validation.py                 |  47 ++++++-
 tests/integration/test_audit_postgres.py           |  75 +++++++---
 .../test_diagnostic_transactions_postgres.py       |  59 ++++++--
 tests/integration/test_editorial_postgres.py       | 152 ++++++++++++++++----
 .../integration/test_entity_revisions_postgres.py  |  95 ++++++++++---
 tests/integration/test_revision_actor_postgres.py  |  57 ++++++--
 tests/integration/test_semantic_postgres.py        |  57 ++++++--
 25 files changed, 1074 insertions(+), 215 deletions(-)
```
