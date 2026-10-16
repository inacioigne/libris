# Superfície HTTP catalográfica v1 — M05.01 / #45

Complemento do [contrato canônico v1](catalogographic-contract.md), especificação
**1.0.0**, que não significa homologação institucional dos perfis. Esta entrega
integra o ponto de composição `/api/v1/catalog`, com tag `catalog`, em `create_app`.
**Não registra operações catalográficas.** Os únicos endpoints de negócio/liveness
reais continuam sendo GET `/health` e GET `/api/v1/identity/me`. Não há reserva de
caminhos por handlers 200/201/204/501. O OpenAPI real conserva somente esses dois
caminhos, seus modelos `HealthResponse` e `IdentityResponse`, Bearer em `/me` e os
schemas de erros/diagnósticos instalados pelo mecanismo existente.

A [verificação datada](catalogographic-http-m05-01-verification-2026-10-16.md)
distingue testes HTTP reais de testes isolados de dependências e políticas.

## Recursos e representações

Todas as rotas abaixo são **contrato para entregas futuras**, ausentes do OpenAPI
operacional desta #45. `{collection}` é uma das cinco coleções fechadas da tabela;
`{id}` é UUID, nunca título, ISBN, barcode, URI arbitrária ou ID de usuário.

| Entidade | Coleção sob `/api/v1/catalog` | Create → Read; PATCH | ResourceKind confiável |
| --- | --- | --- | --- |
| Work | `/works` | WorkCreate → WorkRead; WorkUpdate | bibliographic |
| Instance | `/instances` | InstanceCreate → InstanceRead; InstanceUpdate | bibliographic |
| Item | `/items` | ItemCreate → ItemRead; ItemUpdate | bibliographic |
| Agent | `/agents` | AgentCreate → AgentRead; AgentUpdate | authority |
| Subject | `/subjects` | SubjectCreate → SubjectRead; SubjectUpdate | authority |

Os quinze modelos existentes em `bibliographic/api/schemas` permanecem a fonte de
Request/Response tipados, sem duplicação e sem modelos ORM no transporte. Não são
adicionados ao OpenAPI só para anunciar operações futuras. JSON de aplicação usa
`application/json`, snake_case, UUID serializado como string e URI persistida sem
normalização. Não é JSON-LD nem snapshot interno. Create não recebe identidade;
o servidor gera UUIDv4 e materializa a URI usando o mecanismo existente. Read
acrescenta `internal_id` e `uri`, sem ator, número de revisão ou estado técnico.
A URI persistente não é recalculada a partir da rota HTTP ou da base atual.

Create/Read usam listas vazias para propriedades opcionais, rejeitam extras e
seguem as invariantes dos [schemas](catalogographic-schemas.md). PATCH usa Update
com `exclude_unset=True`: omissão preserva; null remove propriedade opcional;
lista substitui integralmente; auxiliares são substituídos completos. Nunca usar
`exclude_none=True` para o patch. Validar o estado completo e preservar predicados
RDF fora do DTO é responsabilidade dos adaptadores #46, antes de persistir na #47.
Não aceitar `actor_id`, roles, permissions, issuer, subject de identidade ou
technical_context como autoridade em body/query/headers. O campo bibliográfico
`subject` de Work continua sendo uma referência de assunto, sem função de identidade.

## Matriz HTTP planejada

Prefixo de todas as linhas: `/api/v1/catalog`. `T` representa o tipo da coleção
acima. Sucesso só será anunciado no OpenAPI quando houver handler implementado.

| Método e caminho futuro | Entrada → saída / sucesso previsto | Operação/política | Entrega |
| --- | --- | --- | --- |
| POST `/{collection}` | TCreate → TRead; 201, Location individual | bibliographic.create ou authority.manage | #47 |
| GET `/{collection}/{id}` | sem corpo → TRead editorial; 200 | bibliographic.read_editorial ou authority.read_editorial | #47 |
| PATCH `/{collection}/{id}` | TUpdate + If-Match → TRead editorial; 200 | bibliographic.update ou authority.manage | #47 |
| GET `/{collection}/{id}/relationships` | RelationshipRead; 200 | leitura editorial do tipo real | #48 |
| PATCH `/{collection}/{id}/relationships` | RelationshipUpdate add/remove/replace → RelationshipRead; 200, If-Match | escrita do tipo real | #48 |
| POST `/{collection}/validation` | entrada DTO/perfil a detalhar na #48 → CatalogValidationResult; 200 para execução concluída, inclusive não conformidade | contexto humano e capacidade de escrita do tipo; sem persistência | #48 |
| GET `/profiles` | releases/perfis configurados; schema a definir na #48 | política exata a definir antes do handler; deny-by-default | #48 |
| POST `/{collection}/{id}/editorial/{action}` | comando do domínio, expectativas de conteúdo/estado → estado; schema/sucesso a fixar na #49 | editorial.action exata | #49 |
| GET `/{collection}/{id}/editorial` | estado/histórico; schema a fixar | metadata.editorial_history | #49 |
| GET `/{collection}/{id}/revisions` e `/revisions/{number}` | histórico/revisão; envelope a fixar | metadata_revision.read | #49 |
| GET `/{collection}/{id}/events` e `/events/{event_id}` | auditoria catalográfica; envelope a fixar | metadata_audit.read | #49 |
| POST `/{collection}/{id}/revisions/{number}/restore` | expectativas CAS → nova revisão; schema/sucesso a fixar | metadata_revision.restore | #49 |
| GET `/public/{collection}/{id}` | TRead da revisão publicada exata; 200 ou 404 sem publicação | bibliographic.read_public ou authority.read_public | #49 |
| GET `/{collection}` e `/public/{collection}` | coleção editorial ou pública paginada; envelope a fixar | leitura correspondente | #50 |
| GET individual com Accept | JSON de aplicação, application/ld+json ou text/turtle; 200, 406 se não suportado | mesma visibilidade do caminho escolhido | #50 |

`{action}` será conjunto fechado submit/approve/publish/return/withdraw/republish/archive,
nunca um destino arbitrário. Essas rotas não permitem DELETE físico. A retirada é
editorial; histórico não é mutável. Comparação de revisões também pertence à #49,
com parâmetros e schema a especificar nessa entrega. As linhas com contrato ainda
incompleto não autorizam publicar handlers até fechar schemas e políticas aplicáveis.

A separação `/public/...` é uma projeção explícita dentro da mesma convenção v1.
GET individual sem esse segmento é editorial e exige autenticação. Não fazer
fallback de editorial para público em falha de credencial, nem escolher revisão
corrente para substituir a publicada. Nas futuras operações públicas, `read_public`
e o guard verificam estado confiável e **selected_revision == public_revision**
positiva. Uma candidata nova não substitui a revisão pública; withdrawn, archived
e legado sem publicação não ficam visíveis. Estado da candidata/corrente não decide
sozinho a visibilidade. O tipo/perfil real vem do recurso persistido.

Estratégia de paginação para #50: cursor opaco e ordenação determinística com UUID
como desempate; `limit` default 20, intervalo 1–100. Cursor deve fixar ordenação,
filtros e escopo de visibilidade; não concede permissões. O envelope, os filtros e
a codificação serão fechados na #50, incluindo testes de estabilidade e custo SQL.
Históricos internos já têm paginação, sem se tornarem automaticamente esse contrato
HTTP. Não prometer snapshot estável entre páginas sob escritas concorrentes sem
implementar essa garantia. Elasticsearch não participa destas consultas.

## Matriz de autorização vigente

Fonte executável única: `identity.domain.authorization.POLICIES`; esta tabela é
documentação dessa fonte. `AuthorizationGuard` verifica todos os requisitos de
cada linha, deny-by-default; `system:admin` isolado não dá bypass. Work/Instance/Item
usam bibliographic; Agent/Subject usam authority; histórico/eventos usam metadata.
Não adicionar concessões por inferência de papel ou pelo tipo alegado no payload.

| Operação | Recursos | Permissões conjuntas / condição |
| --- | --- | --- |
| bibliographic.read_public | Work, Instance, Item | nenhuma; somente projeção publicada exata |
| bibliographic.read_editorial | Work, Instance, Item | bibliographic:read + metadata_revision:read |
| bibliographic.create | Work, Instance, Item | bibliographic:create |
| bibliographic.update | Work, Instance, Item | bibliographic:update |
| bibliographic.delete | Work, Instance, Item | bibliographic:delete; política existente, sem serviço DELETE nem endpoint planejado |
| authority.read_public | Agent, Subject | nenhuma; somente projeção publicada exata |
| authority.read_editorial | Agent, Subject | authority:read + metadata_revision:read |
| authority.manage | Agent, Subject | authority:manage; criação e revisão |
| metadata_revision.read | revisões dos cinco tipos | metadata_revision:read |
| metadata_revision.create | metadados | metadata_revision:create; política disponível, sem endpoint artificial |
| metadata_revision.restore | revisões dos cinco tipos | metadata_revision:read + metadata_revision:create |
| metadata_audit.read | eventos dos cinco tipos | metadata_audit:read |
| metadata.editorial_history | estado/histórico dos cinco tipos | metadata_revision:read + metadata_audit:read |
| editorial.submit | cinco tipos | editorial:submit |
| editorial.approve | cinco tipos | editorial:approve |
| editorial.publish | cinco tipos | editorial:publish |
| editorial.return | cinco tipos | editorial:return |
| editorial.withdraw | cinco tipos | editorial:withdraw |
| editorial.republish | cinco tipos | editorial:republish |
| editorial.archive | cinco tipos | editorial:archive |
| system.admin | system | system:admin; sem operação administrativa HTTP nesta entrega |

As condições de estado, justificativa, revisão aprovada e CAS dos serviços continuam
obrigatórias além dessas permissões. Transições e restauração exigem contexto humano;
contextos técnicos internos limitam concessões e operações conforme POLICIES, sem
credencial técnica HTTP. O authority-manager com authority:manage não ganha por isso
metadata_revision:read; leitura editorial pode exigir combinação explícita de papéis.
A [matriz histórica M04](security-access-matrix.md) contém diagnósticos datados;
o [contrato por operação](operation-authorization.md) e o código vigente prevalecem.

## Dependências e transações

`bibliographic.api.dependencies.get_session_factory(Request)` retorna exatamente
`request.app.state.database.sessions`, criada no lifespan de `main.py`. Pode ser
injetada com `Depends(get_session_factory)` nos próximos handlers/composition roots.
Não cria engine, sessão compartilhada, transação externa, commit ou migração.
`BibliographicService`, `HistoryService` e `PostgresEditorialTransactions` recebem
a fábrica existente; cada operação mantém suas sessões e seu encerramento, com
rollback em falha pelos context managers atuais. Não abrir `session.begin()` HTTP
em torno de serviços que já delimitam transações. Se algum handler futuro precisar
de sessão direta, reutilizar `Database.session()` e garantir fechamento sem commit
implícito; nenhuma dependência geradora nova foi necessária nesta #45.

Reutilizar diretamente `identity.api.dependencies.get_execution_context`,
`get_current_actor`, `get_authorization_guard` e, quando necessário para requisito
pontual, `require_permissions`; não há wrappers nem segunda matriz de autorização.
O fluxo é Bearer → IdentityService/OIDCValidator → HumanContext → serviço com
AuthorizationGuard injetado. OIDC mantém assinatura, issuer/audience, JWKS,
discriminador de access token e azp do cliente humano; roles/permissões vêm das
claims validadas e do mapa existente. Dependências substituídas em testes não são
bypass de produto. Operações contextuais futuras precisam carregar perfil/estado
mínimo confiável e autorizar novamente dentro da transação antes da mutação.

Correlação usa `RequestCorrelationMiddleware` e `core.correlation.request_id_context`.
O middleware aceita UUID canônico em X-Request-ID ou gera outro, propaga e reseta o
ContextVar, devolvendo o mesmo ID inclusive em erros. Nenhuma dependência paralela
é necessária. Auditoria bibliográfica e eventos de segurança permanecem separados.

PATCH futuro exigirá If-Match forte específico da representação de edição: ausente
428, formato inválido 400, obsoleto 412. Reutilizar `require_if_match`, sem tratar
`Revision.concurrency_token` como ETag. A #47 definirá geração e vínculo confiável
com expected_revision; CAS persistente continua árbitro final. Transições #49
incluem versão editorial e revisão selecionada independentes. Read/Update não ganham
campos técnicos para transportar expectativas. Exportações/composições terão seus
próprios validadores; não reutilizar ETag de um formato em outro.

## Erros, CORS e compatibilidade

Reutiliza-se RFC 9457 em `api/problems.py`, application/problem+json, code estável,
contract_version 1.0, request_id e instance urn:uuid. Não refletir tokens, input,
conexão SQL, stack trace, PII ou grafos privados. Falhas inesperadas continuam 500.

| Status | Uso efetivo ou futuro |
| --- | --- |
| 400 | JSON/entrada malformada; futuro If-Match inválido; preflight negado mantém resposta CORS existente |
| 401 | ausência/erro de autenticação em /me e dependência; WWW-Authenticate: Bearer |
| 403 | PermissionDenied/EditorialPermissionDenied pelos handlers existentes; catálogo testado isoladamente nesta entrega |
| 404 | rota ausente hoje; recurso/revisão ausente nos handlers futuros |
| 405 | método não suportado em rota real, preservando Allow |
| 409 | conflitos/integridade conforme mapeamento existente |
| 412 / 428 | precondição obsoleta / ausente nas futuras escritas |
| 422 | estrutura/invariantes/validação rejeitada; sem corpo catalográfico HTTP na #45 |
| 500 / 503 | falha interna / dependência indisponível conforme classificador existente |
| 406 | negociação não suportada, a integrar e testar na #50 |

Os códigos editoriais genéricos sem mapeamento específico conservam fallback 422;
não prometer automaticamente 409/412/428 pelo nome do código. Fechar o mapeamento
HTTP das transições na #49 sem modificar contratos silenciosamente. O OpenAPI global
atual documenta erros do mecanismo, não prova que cada rota os produz; a documentação
explícita de 401 em /me é lacuna preexistente, sem alteração global nesta entrega.

EndpointCORSMiddleware conserva allowlist de origens, caminhos health/me, somente
GET, headers Authorization/X-Request-ID, exposição de X-Request-ID/WWW-Authenticate
e credenciais desabilitadas. Preflight de catálogo ainda é negado. Quando operações
reais forem registradas, atualizar caminhos/métodos exatos e testar preflight nessa
mesma entrega. SecurityHeadersMiddleware e o BFF Next.js não são alterados.

FastAPI.info.version=0.1.0, `/api/v1`, bibliographic_contract=1.0 dos perfis,
contract_version=1.0 e especificação documental 1.0.0 preservam responsabilidades
independentes. Nenhuma mudança dos quinze DTOs, perfis, SHACL, snapshots, migrações,
locks ou contratos internos. Mudanças incompatíveis requerem versão/ADR/testes e
avaliação direcional do [ADR 0029](../decisions/0029-catalogographic-contract-versioning.md).
A composição mínima aplica ADRs 0011/0017/0023/0031, sem mudança arquitetural nova.

## Estado e sequenciamento

| Entrega | Estado nesta execução |
| --- | --- |
| #45 | roteador integrado sem endpoints artificiais, fábrica reutilizada, convenção HTTP e testes aplicáveis |
| #46 | adaptadores DTO ↔ RDF persistentes e preservação de extensões pendentes |
| #47 | POST/GET/PATCH, ETag e persistência HTTP dos cinco tipos pendentes |
| #48 | relações, pré-validação HTTP e catálogo de perfis pendentes |
| #49 | transições, projeção pública, histórico/auditoria/restauração HTTP pendentes |
| #50 | listagens/filtros/paginação e Accept JSON-LD/Turtle pendentes |
| #51 | homologação integrada M05 com PostgreSQL/OIDC reais isolados pendente |

Serviços internos de criação/revisão, read/read_public, relações, validação,
editorial/histórico/auditoria já existem; isso não os torna endpoints. Os testes
M05.01 não homologam novamente Keycloak, PostgreSQL, navegador ou produção. As
issues #45–#51 foram consultadas somente em leitura; nenhuma foi alterada.
