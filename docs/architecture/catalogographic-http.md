# Superfície HTTP catalográfica v1 — M05.04 / #48

Complemento do [contrato canônico v1](catalogographic-contract.md), especificação
**1.0.0**. Implementa POST/GET/PATCH persistentes dos cinco tipos em
`/api/v1/catalog`. Não significa homologação institucional dos perfis nem do OIDC
em produção. `/health` e `/api/v1/identity/me` permanecem disponíveis.

[Evidências datadas da #47](catalogographic-m0503-verification-2026-10-16.md).
A [verificação da #45](catalogographic-http-m05-01-verification-2026-10-16.md)
permanece como registro histórico da composição sem operações naquele momento.

## Recursos e representações

POST/GET/PATCH individuais abaixo estão implementados e presentes no OpenAPI.
Relações, pré-validação e consulta de perfis também estão implementadas pela #48; as demais operações da matriz continuam futuras. `{collection}` é uma das cinco coleções fechadas da tabela;
`{id}` é UUID, nunca título, ISBN, barcode, URI arbitrária ou ID de usuário.

| Entidade | Coleção sob `/api/v1/catalog` | Create → Read; PATCH | ResourceKind confiável |
| --- | --- | --- | --- |
| Work | `/works` | WorkCreate → WorkRead; WorkUpdate | bibliographic |
| Instance | `/instances` | InstanceCreate → InstanceRead; InstanceUpdate | bibliographic |
| Item | `/items` | ItemCreate → ItemRead; ItemUpdate | bibliographic |
| Agent | `/agents` | AgentCreate → AgentRead; AgentUpdate | authority |
| Subject | `/subjects` | SubjectCreate → SubjectRead; SubjectUpdate | authority |

Os quinze modelos existentes em `bibliographic/api/schemas` permanecem a fonte de
Request/Response tipados, sem duplicação e sem modelos ORM no transporte. Integram o OpenAPI dos handlers reais. JSON de aplicação usa
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
RDF fora do DTO é executado pelos adaptadores #46 dentro do caso de uso da #47.
Não aceitar `actor_id`, roles, permissions, issuer, subject de identidade ou
technical_context como autoridade em body/query/headers. O campo bibliográfico
`subject` de Work continua sendo uma referência de assunto, sem função de identidade.

## Matriz HTTP e entregas

Prefixo de todas as linhas: `/api/v1/catalog`. `T` representa o tipo da coleção
acima. As linhas #47 e #48 possuem handlers; as demais continuam futuras.

| Método e caminho | Entrada → saída / sucesso previsto | Operação/política | Entrega |
| --- | --- | --- | --- |
| POST `/{collection}` | TCreate → TRead; 201, Location individual | bibliographic.create ou authority.manage | #47 implementada |
| GET `/{collection}/{id}` | sem corpo → TRead editorial; 200 | bibliographic.read_editorial ou authority.read_editorial | #47 implementada |
| PATCH `/{collection}/{id}` | TUpdate + If-Match → TRead editorial; 200 | bibliographic.update ou authority.manage | #47 implementada |
| GET `/{collection}/{id}/relationships` | RelationshipRead; 200 | leitura editorial do tipo real | #48 implementada |
| PATCH `/{collection}/{id}/relationships` | RelationshipUpdate add/remove/replace → RelationshipRead; 200, If-Match | escrita do tipo real | #48 implementada |
| POST `/{collection}/validation` | ValidationRequest DTO/RDF/revisão → CatalogValidationResult; 200 para execução concluída, inclusive não conformidade | contexto humano e capacidade de criação do tipo; sem persistência | #48 implementada |
| GET `/profiles` | ProfileReleaseRead configurados | metadata_revision.read; deny-by-default | #48 implementada |
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
`CatalogService` especializa `BibliographicService`, reutilizando `_create` e
`_revise`, RevisionStore, EditorialStore e AuditStore. Cada operação abre uma única
transação própria; não envolve `create`/`revise` em outra transação. Projeção Read e
validação do estado completo acontecem antes do commit. GET lê snapshot corrente e
versão editorial sob o mesmo lock de recurso, sem inicializar legado. Não consulta
histórico/auditoria nem exige metadata_audit:read. `HistoryService` e
`PostgresEditorialTransactions` continuam atendendo histórico e decisões internas;
são utilizados pelos testes de invariantes e publicação, sem novas rotas.

Escritas DTO usam o gate PostgreSQL **exclusivo**, adquirido antes do recurso e das
dependências; leituras correntes usam shared. É a mesma chave/protocolo da M03,
com serialização conservadora das escritas DTO para impedir locks cruzados durante
resolução de referências. Não há mutex Python. Ver [ADR 0036](../decisions/0036-catalog-http-concurrency.md).
O CAS SQL de conteúdo e o CAS editorial continuam sendo executados por `_revise`.
Snapshot, identidade, estado e auditoria são confirmados/revertidos juntos; a
resposta de sucesso só é liberada depois do commit.

Referências explicitamente locais são resolvidas no PostgreSQL na transação de
escrita: UUID/URI/tipo devem concordar; UUID-only usa a URI armazenada. URI-only que
corresponde a identidade local também tem tipo conferido. URI ausente localmente
não prova existência externa: mantém a pendência compatível do contrato v1, sem
consultar rede. Não se afirma validação universal de fechos/ciclos no rascunho;
a publicação interna continua aplicando a integridade mais restrita da #43.
Referências não reconciliadas e substituições de auxiliares que perderiam anotações
são recusadas conforme o adaptador #46. Perfil da criação: institucional 1.1 para
Work/Instance/Item e authority-v1 para Agent/Subject; PATCH reutiliza o ID persistido.
Perfis declarativos 2.0 não são adotados automaticamente.

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

## ETag e If-Match

POST, GET e PATCH devolvem ETag forte `"catalog-v1-<sha256>"`. O digest inclui
namespace da representação JSON de edição v1, UUID/URI, perfil persistido, revisão,
versão editorial independente (ou ausência legada) e projeção Read serializada
canonicamente. Não é `Revision.concurrency_token`, um token de autorização ou um
validador de futura exportação/composição. Alteração editorial sem revisão também
invalida o ETag. As respostas editoriais conservam `Cache-Control: no-store, private`.

PATCH exige um único `If-Match` forte. Ausente → 428; fraco, curinga, lista, header
duplicado ou sintaxe inválida → 400; forte diferente do corrente → 412. Um ETag
forte de outro recurso/formato também é obsoleto (412). Não há expected_revision
nos DTOs. `require_if_match` compara a representação carregada; o caso de uso relê
sob lock e passa a revisão e versão editorial observadas a `_revise`. CAS SQL
continua obrigatório, mesmo após a comparação. Uma corrida depois da leitura
inicial é rejeitada, sem revisão, snapshot, estado ou evento parcial. Não há retry
que atualize silenciosamente a expectativa do cliente. PATCH vazio é aceito e
produz revisão nova segundo o serviço existente.

POST retorna 201, Location relativo individual e Read com UUID/URI do servidor.
GET corrente e PATCH retornam 200 com Read. Um UUID de outra coleção retorna 404
após as verificações de acesso. Estado não editável retorna 409. Edição de publicado
cria candidata e preserva a revisão pública anterior; nenhuma rota pública foi criada.

Exemplo (Bearer obtido pelo fluxo OIDC existente; não persistir tokens no código):

```http
POST /api/v1/catalog/works
Authorization: Bearer <access-token>
Content-Type: application/json

{"title":[{"main_title":[{"value":"Obra de teste","language":"pt"}]}]}
```

```http
HTTP/1.1 201 Created
Location: /api/v1/catalog/works/<uuid-gerado>
ETag: "catalog-v1-<digest>"
Content-Type: application/json
```

O corpo é WorkRead, incluindo `internal_id`, `uri`, `title` e as listas opcionais.
Para consultar e substituir o título, usar o ETag devolvido pela consulta:

```http
GET /api/v1/catalog/works/<uuid-gerado>
Authorization: Bearer <access-token>
```

```http
PATCH /api/v1/catalog/works/<uuid-gerado>
Authorization: Bearer <access-token>
If-Match: "catalog-v1-<digest-da-consulta>"
Content-Type: application/json

{"title":[{"main_title":[{"value":"Título revisto","language":"pt"}]}],"note":null}
```

PATCH 200 devolve novo ETag e WorkRead atualizado. Um segundo PATCH com o ETag
anterior recebe Problem Details 412 `revision.stale`. As cinco entidades seguem
os mesmos status/headers, com os respectivos DTOs da tabela.

## Erros, CORS e compatibilidade

Reutiliza-se RFC 9457 em `api/problems.py`, application/problem+json, code estável,
contract_version 1.0, request_id e instance urn:uuid. Não refletir tokens, input,
conexão SQL, stack trace, PII ou grafos privados. Falhas inesperadas continuam 500.

| Status | Uso efetivo ou futuro |
| --- | --- |
| 400 | JSON/entrada malformada; If-Match inválido; preflight negado mantém resposta CORS existente |
| 401 | ausência/erro de autenticação em /me e catálogo; WWW-Authenticate: Bearer |
| 403 | permissões insuficientes para a operação editorial |
| 404 | recurso inexistente ou de outra coleção; rotas futuras ausentes |
| 405 | método não suportado em rota real, preservando Allow |
| 409 | conflitos/integridade conforme mapeamento existente |
| 412 / 428 | precondição obsoleta / ausente no PATCH |
| 422 | estrutura/invariantes/validação do estado completo rejeitada |
| 500 / 503 | falha interna / dependência indisponível conforme classificador existente |
| 406 | negociação não suportada, a integrar e testar na #50 |

A #47 mapeia explicitamente editorial.version_stale para 412 e
editorial.transition_forbidden/editorial.state_invalid para 409. Os demais códigos
não mapeados preservam fallback 422. ValidationError do estado completo usa os
mesmos diagnósticos estruturais de RequestValidationError. ConnectionError/TimeoutError
de dependências são 503 sem detalhes sensíveis; outros erros inesperados são 500.

EndpointCORSMiddleware mantém origens explícitas e sem credenciais, permite POST
somente nas cinco coleções e GET/PATCH nos UUIDs individuais. Health/me continuam
GET. Headers permitidos incluem Authorization, Content-Type, X-Request-ID e If-Match;
expõe ETag, Location, X-Request-ID e WWW-Authenticate. Rotas futuras/DELETE continuam
negados no preflight. CORS não concede autenticação nem autorização.

FastAPI.info.version=0.1.0, `/api/v1`, bibliographic_contract=1.0 dos perfis,
contract_version=1.0 e especificação documental 1.0.0 preservam responsabilidades
independentes. Nenhuma mudança dos quinze DTOs, perfis, SHACL, snapshots ou migrações. Mudanças incompatíveis requerem versão/ADR/testes e
avaliação direcional do [ADR 0029](../decisions/0029-catalogographic-contract-versioning.md).
A integração aplica ADRs 0011/0017/0023/0028/0031 e 0036.

## Estado e sequenciamento

| Entrega | Estado nesta execução |
| --- | --- |
| #45 | roteador integrado sem endpoints artificiais, fábrica reutilizada, convenção HTTP e testes aplicáveis |
| #46 | [adaptadores internos DTO ↔ RDF](catalogographic-dto-rdf-adapters.md) e PATCH sobre snapshot completo implementados; sem endpoints |
| #47 implementada | POST/GET/PATCH, ETag e persistência PostgreSQL dos cinco tipos |
| #48 implementada | relações, pré-validação HTTP e catálogo somente-leitura; limites no complemento abaixo |
| #49 | transições, projeção pública, histórico/auditoria/restauração HTTP pendentes |
| #50 | listagens/filtros/paginação e Accept JSON-LD/Turtle pendentes |
| #51 | homologação integrada M05 com PostgreSQL/OIDC reais isolados pendente |

Serviços internos de criação/revisão, read/read_public, relações, validação,
editorial/histórico/auditoria já existem; isso não os torna endpoints. Os testes
M05.01 não homologam novamente Keycloak, PostgreSQL, navegador ou produção. As
issues #45/#46/#47 e as dependências M03/M04 foram consultadas somente em
leitura; nenhuma foi alterada.

## Instalação e testes PostgreSQL

Executar migrações explicitamente: `cd apps/api && uv run alembic upgrade head`.
O schema experimental existente é suficiente; a #47 não cria migração. Startup
não executa DDL nem `create_all`. Não executar downgrade em bases de trabalho.

A suíte padrão `uv run pytest` não depende de serviços. Para persistência, criar um
PostgreSQL **descartável e exclusivo**, aplicar head nele usando DATABASE_URL e
fornecer TEST_DATABASE_URL para a suíte. Nunca apontar ao banco de desenvolvimento.

```bash
cd apps/api
# URLs de bancos descartáveis configuradas no ambiente, sem versionar credenciais.
uv run alembic upgrade head
uv run pytest -c pyproject.toml ../../tests/integration -m integration
```

TEST_MIGRATION_DATABASE_URL, TEST_EDITORIAL_MIGRATION_DATABASE_URL e
TEST_WEB_MIGRATION_DATABASE_URL precisam ser **outros** bancos inicialmente vazios
para testes de upgrade/downgrade; o último exige TEST_WEB_ISOLATED=1. Ausência gera
skips, que não comprovam integração. A evidência da #47 descreve os bancos exclusivos
utilizados, resultados e limites. OIDC nos novos testes é substituído por ator
sintético via dependência; não comprova nova homologação Keycloak/produção.

## M05.04 / #48 — capacidades implementadas

Este complemento sucede as indicações de pendência da #48 nas seções históricas
acima. [ADR 0037](../decisions/0037-catalog-relationships-prevalidation.md) e
[verificação própria](catalogographic-m0504-verification-2026-10-16.md).

| Método | Caminho sob `/api/v1/catalog` | Entrada → saída | Permissão efetiva |
| --- | --- | --- | --- |
| GET | `/{collection}/{id}/relationships` | sem body → RelationshipRead, 200 | bibliographic:read + metadata_revision:read; authority:read + metadata_revision:read nas autoridades |
| PATCH | `/{collection}/{id}/relationships` | RelationshipUpdate + If-Match → RelationshipRead, 200 | bibliographic:update ou authority:manage |
| POST | `/{collection}/validation` | ValidationRequest → CatalogValidationResult 1.0, 200 | bibliographic:create ou authority:manage; revisão existente exige também leitura editorial |
| GET | `/profiles` | lista de ProfileReleaseRead, 200 | metadata_revision:read |
| GET | `/profiles/release?release_id=IRI` | ProfileReleaseRead, 200 | metadata_revision:read |

Coleções são somente works/instances/items/agents/subjects. O OpenAPI usa parâmetro
collection enumerado nos novos handlers. Não há PUT/DELETE de registros, nem
rotas administrativas de perfis. Substituição é a operação replace do PATCH;
RelationshipReplace continua sendo o contrato interno de substituição completa.

### Relações e precondições

GET retorna relações próprias. `?include_inverses=true` inclui hasInstance/hasItem
obtidas dos snapshots filhos correntes, sem gravá-las no pai. O discriminador vem
do registro de relações: predicado derived não pode ser editado. Para editar, obter
ETag de GET **sem inversas**, que identifica a coleção proprietária. Inversas não
constituem representação histórica global nem comprovam publicação dos filhos.

ETag `"catalog-relationships-v1-<digest>"` inclui projeção relacional ordenada,
conteúdo corrente e versão editorial. If-Match exige um único ETag forte: ausente
428; sintaxe inválida/duplicada 400; divergente 412. ETag do GET de recurso completo
ou do GET com inversas diferentes não substitui o da coleção proprietária.
O serviço relê ambas as versões sob lock; os CAS existentes continuam obrigatórios.

Exemplo de adição (substituir os UUIDs sintéticos por identidades existentes):

```http
PATCH /api/v1/catalog/works/00000000-0000-4000-8000-000000000001/relationships
Authorization: Bearer <access-token>
If-Match: "catalog-relationships-v1-<digest-da-consulta>"
Content-Type: application/json

{"operations":[{"op":"add","links":[{"kind":"direct","source":{"kind":"local","entity_type":"Work","internal_id":"00000000-0000-4000-8000-000000000001"},"predicate":"http://id.loc.gov/ontologies/bibframe/relatedTo","target":{"kind":"external","entity_type":"Work","uri":"https://example.invalid/work"}}]}]}
```

Remoção usa `op=remove` e o vínculo consultado; substituição usa
`{"op":"replace","predicate":"http://id.loc.gov/ontologies/bibframe/relatedTo","links":[]}`.
Uma única lista de operações é atômica e validada no estado final. Duplicata e
cardinalidade inválida → 422 schema.invalid; remoção inexistente, origem/identidade
incompatível, alvo local inexistente, autorreferência ou ciclo local → 422
reference.invalid, ou diagnóstico estrutural quando detectado pelo DTO. A matriz
oficial diferencia Work/Instance mesmo para relatedTo. hasInstance/hasItem graváveis
são recusadas. UUID de origem ausente/coleção errada → 404 resource.unknown.

Cada PATCH cria uma revisão e um evento revised na mesma transação de conteúdo,
estado e referências; falhas, inclusive de commit, revertem todos os efeitos.
Não modifica revisões históricas nem publica candidata. Graph completo é copiado;
propriedades, extensões, idiomas/datatype e identidade fora da operação permanecem.
Contribution exige papéis; Publication usa activity_key consultada para identificar
atividade existente, conservando lugar/data. Chaves novas criam atividade privada;
chaves de blank nodes não são identidade permanente. Remoção de Contribution com
anotações ou compartilhamento não representados é recusada com 422 profile.policy.

Referências locais são resolvidas e conferidas na transação. Uma referência
alegada externa cuja URI seja local é tratada como local e seu tipo é conferido.
Externas sem identidade local não são consultadas remotamente nem viram entidades.
Unreconciled → 422 reference.invalid: não existe política persistente de rascunho
para elas. Campos namespace/external_id não possuem representação RDF e não são
recuperados do snapshot. Para dcterms:relation de Agent, tipo externo Agent/Subject
é ambíguo no RDF: recebe 422 reference.unverified, sem inferência. Isso é uma
limitação explícita; não afeta alvos locais nem relações de destino único.

### Pré-validação para o editor M07

ValidationRequest é união discriminada por kind, com extras proibidos:

```json
{"kind":"dto","profile_release":"urn:libris:profile:monograph:v1:1","resource":{"title":[{"main_title":[{"value":"Proposta","language":"pt"}]}]}}
```

```json
{"kind":"rdf","profile_release":"urn:libris:profile:monograph:v1:1","format":"turtle","root":"https://example.invalid/work","context":"snapshot","document":"<https://example.invalid/work> a <http://id.loc.gov/ontologies/bibframe/Work> ."}
```

```json
{"kind":"revision","resource_id":"00000000-0000-4000-8000-000000000001","revision":1}
```

DTO usa um dos cinco Create e o tipo deve corresponder à coleção. Identidade nova
é somente efêmera em memória. Revision valida snapshot autorizado, com release
armazenada, sem aceitar troca implícita; revision omitida seleciona a corrente.
Não representa PATCH de revisão nem publicação. RDF aceita somente Turtle/JSON-LD,
raiz explícita e contexto snapshot/composed; composto é fornecido integralmente,
sem derivação automática ou leitura de outros registros. Snapshot exige ownership.
Perfil/release são resolvidos localmente, por ID exato, sem escolha de “mais recente”.
Releases 2.0 candidate/published são selecionáveis explicitamente; draft/deprecated
são consultáveis, mas não selecionáveis para nova proposta. Incompatível → 422
profile.incompatible; inexistente → 404 profile.unknown. Histórico usa seu próprio
perfil, preservando os contratos anteriores.

Execução concluída retorna 200, inclusive conforms=false com issues estáveis.
O RDF do segundo exemplo viola título obrigatório e retorna shacl.min_count.
`resource={"title":[]}` é estruturalmente inválido e retorna Problem Details 422,
sem passar pelo motor. Falha conhecida do motor retorna state=failed, sem conforms,
com validator.failure/infrastructure.unavailable; entrada/perfil inválido usa
Problem Details. Falha inesperada permanece 500; escrita semanticamente rejeitada
permanece 422 validation.rejected com validation, usando as mesmas regras SHACL.

Não há INSERT/UPDATE/DELETE bibliográfico, revisão, auditoria bibliográfica,
publicação ou transição. DTO resolve referências numa transação PostgreSQL READ
ONLY; RDF é processado em memória; revisão usa somente a leitura autorizada.
Eventos de segurança do guard continuam independentes da auditoria bibliográfica.
Diagnostics preservam contract_version=1.0, severidade, campo/path, shape,
constraint, fonte e mensagens seguras conforme #22. request_id correlaciona header
e resultado. Interfaces devem apresentar também erros sem field_ids e state=failed.

O body completo de comandos novos é limitado a RDF_MAX_DOCUMENT_BYTES (default
1 MiB) durante a leitura, sem confiar em Content-Length; profundidade JSON 64.
O parser RDF conserva seus próprios limites. Contexto remoto, formato desconhecido
ou entrada não suportada são recusados; não buscar ontologias/shapes/vocabulários.
Não há limite de CPU ou homologação de carga institucional neste incremento.

### Catálogo de perfis

ProfileReleaseRead contém configured=true, profile e persistent_writes_supported.
Profile é ResolvedProfile 2.0 existente ou LegacyProfileRead, sem nomes de arquivos.
Ambos incluem ID/release/status, propriedades e referências SHACL; 2.0 inclui
família, lineage, seções, condições, políticas e variantes de valores. Legado usa
release_id=id histórico e sua estrutura de campos original. A lista tem ordem por
release_id e a consulta exata não troca release nem altera estado do registro.

Configured significa presente no pacote, enquanto candidate/published/deprecated/
draft são estados do perfil. O pacote atual tem 14 releases configuradas, com estados candidate e draft. Não há
estado institucional approved no modelo; published não é convertido em approved.
Somente os três IDs históricos são suportados pela persistência atual; o booleano
não promete que qualquer RDF ou DTO será aceito. Perfis 2.0 estão disponíveis para
pré-validação e descoberta, sem adoção automática pela escrita.

CORS permite as cinco novas operações somente nos caminhos reais e métodos
correspondentes. Mantém origens explícitas, Bearer, no-store/private, request ID e
Problem Details existentes. DELETE e rotas futuras continuam negados no preflight.
