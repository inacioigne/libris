# Matriz normativa de acesso — M04.01 / #34

Data e checkout: [baseline de 2026-10-13](security-baseline.md).
Esta matriz consolida o uso das permissões existentes. Requisitos de rotas futuras
não são enforcement já implementado. O código do enum/mapa é a fonte de concessões;
não se introduz um segundo mapa executável. IT/IO/EP/ND seguem a baseline.

## Permissões e papéis efetivos

Fonte: [Permission](../../apps/api/src/libris/modules/identity/domain/permissions.py)
e [ROLE_PERMISSIONS](../../apps/api/src/libris/modules/identity/infrastructure/role_mapper.py).
São **17 valores e seis papéis**. Nas tabelas de operações, R = libris-reader,
C = libris-cataloger, A = libris-authority-manager, V = libris-reviewer,
P = libris-publisher, S = libris-admin. Letras apenas abreviam nomes.

| Permissão interna | R | C | A | V | P | S |
| --- | --- | --- | --- | --- | --- | --- |
| `bibliographic:read` | sim | sim | sim | sim | sim | sim |
| `bibliographic:create` | — | sim | — | — | — | sim |
| `bibliographic:update` | — | sim | — | — | — | sim |
| `bibliographic:delete` | — | — | — | — | — | sim |
| `authority:read` | sim | sim | sim | sim | sim | sim |
| `authority:manage` | — | — | sim | — | — | sim |
| `metadata_revision:read` | — | sim | — | sim | sim | sim |
| `metadata_revision:create` | — | sim | — | — | — | sim |
| `metadata_audit:read` | — | — | — | sim | sim | sim |
| `editorial:submit` | — | sim | — | — | — | sim |
| `editorial:approve` | — | — | — | sim | — | sim |
| `editorial:return` | — | — | — | sim | — | sim |
| `editorial:publish` | — | — | — | — | sim | sim |
| `editorial:withdraw` | — | — | — | — | sim | sim |
| `editorial:republish` | — | — | — | — | sim | sim |
| `editorial:archive` | — | — | — | — | sim | sim |
| `system:admin` | — | — | — | — | — | sim |

Papéis desconhecidos/ausentes/malformados não concedem permissões; múltiplos papéis
acumulam concessões. A fonte padrão é resource_access do client configurado;
realm_access só por configuração explícita. Claims devem ter assinatura validada.
Papéis desconhecidos podem constar de /me, com permissões vazias: autenticação
válida não é autorização de uma operação privilegiada.

`system:admin` isolado não satisfaz outras permissões. O mapa atual concede
`frozenset(Permission)` a libris-admin: enum completo explicitamente, sem atalho
no authorize; adicionar um valor ao enum ampliará esse papel e exige revisão.
Frontend só adapta a experiência; decisão final é do backend.
Permissões catalográficas não autorizam dados pessoais de leitores. Não há escopo
institucional/por recurso implementado nem regra de quatro olhos.

## Operações por domínio

Colunas separam **pública**, **identidade**, **privilégio** e **interna**. “Interna
atual / HTTP futuro” significa que há função, mas não endpoint. Permissões indicadas
como requisito futuro não são exigidas automaticamente pelas primitivas internas.
`B` é [bibliographic](../../apps/api/src/libris/modules/bibliographic/).

| Domínio / operação | Pública | Identidade | Permissão / papéis | Interna e situação | Estados / pré-condições | Enforcement atual ou previsto / evidência / responsável |
| --- | --- | --- | --- | --- | --- | --- |
| Bibliographic: ler registro publicado | futura: sim | não no HTTP público futuro | nenhuma para projeção pública | read_public IT interno; HTTP EP | somente public_revision em published; legado/retirado/arquivado não visíveis | `B/application/service.py::read_public`; futura rota M05 deve selecionar projeção, nunca read corrente; teste físico `test_persistent_workflow_candidate_return_restore_and_archive` |
| Bibliographic: leitura editorial corrente | não | sim na exposição futura | bibliographic:read; R/C/A/V/P/S | read IT interno sem RBAC; HTTP EP | publicado e rascunho não compartilham visibilidade pública; não expor histórico por esta permissão | guard #38 + boundary M05; `B/application/service.py::read`; política contextual futura não pode ser inferida apenas do papel reader |
| Bibliographic: criar Work/Instance/Item | não | sim no HTTP futuro | bibliographic:create; C/S | create IT interno sem esse guard; HTTP EP | perfil aplicável; identidade nova; r1/draft, snapshot e auditoria juntos | `B/application/service.py::create`; #38/M05 aplica permissão antes da chamada |
| Bibliographic: atualizar conteúdo/relações | não | sim no HTTP futuro | bibliographic:update; C/S | revise e contratos de relações IT internos; HTTP EP | expected_revision; CAS; edição somente draft/candidata draft, RETURN antes de editar in_review/approved | `service.py::revise`, `api/schemas/relationships.py`, `application/relationships.py`; #38/M05 aplica guard e contrato HTTP de concorrência |
| Bibliographic: exclusão prevista | não | sim | bibliographic:delete; S | EP/ND, sem serviço de exclusão | não apagar snapshots nem reutilizar UUID/URI; política de encerramento ainda exige decisão | [identificadores](persistent-identifiers.md), ADR 0019; M05 ou entrega posterior conforme escopo aprovado; permissão não autoriza SQL DELETE direto |
| Bibliographic: serializar JSON-LD/Turtle | apenas projeção publicada futura | sim para conteúdo editorial | nenhuma na exportação pública; bibliographic:read no editorial; metadata_revision:read no histórico | serializadores IT puros, HTTP EP | autorização e seleção do snapshot precedem serialização; formato não altera visibilidade | `B/infrastructure/serialization/representation.py`; [serialização](semantic-serialization.md); M05 |
| Bibliographic: consultar relações | somente as publicáveis futuras | sim para editorial | bibliographic:read; R/C/A/V/P/S | contratos/validação IT; consulta HTTP EP | não compor rascunhos alheios nem snapshots correntes em exportação histórica por pressuposição | [relações](relationships.md); `application/relationships.py`; #38/M05 |
| Authority: leitura Agent/Subject | publicada futura | não para pública; sim para editorial | authority:read no editorial; R/C/A/V/P/S | snapshots/Read IT; API EP | mesma seleção de visibilidade; autoridade não é usuário/leitor | [schemas](catalogographic-schemas.md), `service.py::read_public`; boundary futuro de autoridades, M05–M15 conforme escopo |
| Authority: manutenção e identificadores | não | sim no HTTP futuro | authority:manage; A/S | contratos e persistência interna IT; autorização geral EP | CAS/URI imutável/perfil de autoridade; nenhuma concessão editorial automática | serviços existentes + guard #38 no boundary futuro; [identificadores](persistent-identifiers.md); M05–M15 conforme escopo |
| Authority: reconciliação/fusão | não | sim prevista | authority:manage como requisito mínimo; A/S; granularidade futura requer decisão | EP/ND, sem reconciliador operacional | sucessor/evidência; não gerar owl:sameAs nem alterar identidade histórica automaticamente | [domínios](domains.md), [ciclo editorial/identidade](editorial-lifecycle.md); M05–M15, sem atribuir milestone específico |
| Metadata revision: consultar/listar/comparar | não | sim | metadata_revision:read; C/V/P/S | HistoryService IT interno; HTTP EP | revisões do mesmo recurso; leitura não modifica corrente; comparação isomórfica | `B/application/history.py::{read_revision,list_revisions,compare_revisions}`; `test_history_denial_precedes_storage`; exposição futura M05 |
| Metadata revision: criar revisão por edição | não | sim no HTTP futuro | metadata_revision:create; C/S; escrita bibliográfica também requer bibliographic:update no boundary futuro | revise IT interno sem guard geral; HTTP EP | nova revisão sequencial, CAS, estado editável; histórica imutável | `service.py::revise`; #38/M05 deve compor permissões, sem afirmar que revise já as verifica |
| Metadata revision: restaurar conteúdo | não | sim | metadata_revision:read **e** metadata_revision:create; C/S | restore_content IT interno; HTTP EP | source_revision válida; CAS/estado editável; rN+1 com proveniência atual; não publica | `service.py::restore_content`; testes `test_history_permission_policy` e físico `test_content_history_restore_and_authorization`; HTTP M05/futuro |
| Metadata audit: listar/ler eventos | não | sim | metadata_audit:read; V/P/S | HistoryService IT interno; HTTP EP | recurso/evento associados, paginação; NULL histórico permanece desconhecido | `history.py::{list_events,read_event}`; `test_history_denial_precedes_storage`; #41 define eventos de segurança distintos, HTTP futuro |
| Editorial: consultar estado e histórico | não | sim | metadata_revision:read **e** metadata_audit:read; V/P/S | read_editorial IT interno; HTTP EP | estado/current/eventos coerentes; None em legado sem estado observado | `history.py::read_editorial`; [persistência](editorial-persistence.md), teste físico de workflow; M05 |
| System: GET /health | sim atual | não | nenhuma | IT HTTP, não operação de domínio | liveness; sem acesso a banco/provedor | [health.py](../../apps/api/src/libris/api/health.py), `test_disabled_never_bypasses_authentication`, `test_lifespan_and_health_without_external_services` |
| System: GET /api/v1/identity/me | não | sim | nenhuma adicional; qualquer identidade válida | IT HTTP | OIDC habilitado/token válido; retorna actor_id/roles/permissions, sem token/e-mail | [router](../../apps/api/src/libris/modules/identity/api/router.py)::me; `get_current_actor`; testes identidade; integração real #35 |
| System: OpenAPI/Swagger/ReDoc | sim atual | não | nenhuma | IT configuração FastAPI | /openapi.json, /docs, /docs/oauth2-redirect, /redoc; não são CRUD nem callback de login Libris | `create_app`; exposição em produção deve ser revisada em #40, sem supor proteção atual |
| System: administrar configurações futuras | não | sim | system:admin; S | EP, sem endpoint | concessão explícita, ambiente confiável e auditoria; não bypass de operações de catálogo | `Permission.SYSTEM_ADMIN` não cria funcionalidade; #38/#39/#41 e entrega futura aprovada |
| System: administrar provedor/infraestrutura | não | identidade do provedor/ambiente | políticas próprias, não automaticamente system:admin | overlay IO dev; operação externa | credenciais no ambiente, menor privilégio, revogação e segregação; Libris não gerencia senhas | [realm](../../infrastructure/keycloak/libris-realm.json), #35/#39; produção fora do Compose local |

Leitura editorial com bibliographic:read é requisito mínimo de capacidade, não
aprovação institucional de acesso de todos os leitores a todo rascunho. #38 deve
fixar contexto/recurso antes de expor rotas; a matriz não fabrica um guard desse escopo.
Manutenção de autoridades não requer permissões bibliographic:create/update por
inferência; seu boundary futuro usa authority:manage. Histórico e decisões editoriais
continuam exigindo suas próprias permissões, inclusive para authority-manager.

## Submatriz editorial vigente

Todas são internas implementadas (domínio IT, integração operacional IO) e HTTP
futuro M05. Exigem humano autenticado confiável, expected_version,
expected_current_revision, selected_revision e instante UTC. Enforcement:
[`EditorialService.transition`](../../apps/api/src/libris/modules/bibliographic/application/editorial.py)
reutiliza authorize/OPERATION_PERMISSIONS;
[`PostgresEditorialTransactions`](../../apps/api/src/libris/modules/bibliographic/application/editorial_postgres.py)
compõe CAS e AuditStore no mesmo commit. Não há bypass por admin/update.

| Operação | Origem → destino | Permissão / papéis | Pré-condição adicional / efeito | Evento observado |
| --- | --- | --- | --- | --- |
| submit | draft → in_review | editorial:submit; C/S | revisão corrente selecionada; scope record ou candidate | record.submitted |
| approve | in_review → approved | editorial:approve; V/S | aprovação ligada à corrente esperada; record ou candidate | record.approved |
| return | in_review → draft; approved → draft | editorial:return; V/S | justificativa; remove aprovação; record ou candidate | record.returned |
| publish | approved → published | editorial:publish; P/S | revisão aprovada exata; perfil/SHACL/referências válidos; candidata só substitui quando registro published | record.published |
| withdraw | published → withdrawn | editorial:withdraw; P/S | justificativa; scope record; preserva publicada histórica/candidata, suspende visibilidade | record.withdrawn |
| republish | withdrawn → published | editorial:republish; P/S | scope record; revalida publicada anterior, não publica candidata corrente | record.restored, restoration_kind=editorial |
| archive | withdrawn → archived | editorial:archive; P/S | justificativa; scope record; terminal; encerra candidata e preserva snapshots | record.archived |

Qualquer aresta ausente é recusada. Publicação exige contexto completo confiável;
falha de validação, dependência, autorização ou CAS reverte mudanças/auditoria.
Transições não criam snapshots; edição candidata conserva a revisão pública até
publicação explícita. Não excluir recursos para retirar/arquivar.
Evidências: [test_editorial.py](../../tests/api/test_editorial.py)::test_entire_matrix,
test_permissions_reject_without_mutation, test_publication_dependencies_fail_closed,
test_content_and_editorial_revisions_are_independent;
[test_editorial_postgres.py](../../tests/integration/test_editorial_postgres.py) cobre
rollback/CAS/validação/candidata em banco real. Execução atual no relatório separado.

## 401, 403 e falhas internas

Sem Bearer, JWT inválido, OIDC desabilitado ou falha de obtenção de chave confiável:
get_current_actor retorna **401**, WWW-Authenticate: Bearer, detalhe genérico.
Identidade válida sem todas as permissões: require_permissions retorna **403**.
Papel desconhecido com token válido autentica /me, mas falha em operação privilegiada.
/health permanece público. Rotas protegidas de teste não são endpoints de produto.

authorize levanta PermissionDenied internamente; EditorialService o adapta para
CatalogError/editorial.permission_denied. Isso não comprova 403 de uma API editorial
inexistente: o handler CatalogError atual tem fallback 422 para códigos aditivos,
conforme [rastreabilidade D02](catalogographic-contract-traceability.md).
O boundary HTTP futuro deve definir/validar o mapeamento sem romper Problem Details v1.
Falha inesperada de infraestrutura pode produzir erro técnico, nunca sucesso anônimo;
não há teste específico de ausência de app.state.identity_service ou de ator None
em toda operação tipada como obrigatória.

## Execução interna e identidade do ator

Chamadas entre módulos usam contratos explícitos, sem acesso direto a tabelas de
outro domínio. AuthenticatedActor é objeto confiável produzido por IdentityService,
não DTO deserializado nem prova criptográfica por si só. audit_actor confere coerência
de hash/tipo, mas código capaz de fabricar issuer/sub/permissions continua privilegiado.
O guard de aplicação geral e escopo de serviço são dependências #38/#39.

create/revise admitem ausência de ator por compatibilidade interna, ou ExecutionActor
service/automated controlado pelo servidor; não inferir esse tipo de source/process.
Nenhum desses caminhos equivale a acesso HTTP anônimo. Decisões editoriais exigem
humano; contas de serviço não ganham esse papel por fabricar um hash.
Não aceitar actor_id, roles, permissions ou execution_actor de payload/header.
Rotas futuras obtêm ator da dependência OIDC e o propagam explicitamente.

Revision.actor_id histórico opcional permanece NULL; ausência não prova automação.
Conteúdo, estado e eventos compartilham a transação quando exigido; falha de auditoria
reverte a operação. Preservar revisões/candidatas/publicadas e não fabricar autoria
retroativa. Auditoria bibliográfica M03 não é log de login, concessão ou recusa:
#41 definirá segurança/retenção sem duplicar revisões. Tokens/claims/PII não entram
nos envelopes; textos livres exigem minimização explícita.
