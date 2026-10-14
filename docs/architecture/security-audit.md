# Auditoria de segurança — M04.08 / issue #41

Implementação local de [#41](https://github.com/inacioigne/libris/issues/41),
separada da auditoria bibliográfica [#28](provenance-audit-versioning.md) e
[#43](editorial-persistence.md). Decisão: [ADR 0035](../decisions/0035-security-audit-emission.md).
Resultados executados: [verificação desta entrega](security-audit-m04-08-verification.md).
Não declara homologação Keycloak, navegador, institucional ou de produção.

## Arquitetura e confiança

API: `modules/security_audit/domain/events.py` define SecurityEvent; aplicação define
SecuritySink/emit_safely; infraestrutura emite uma linha JSON por logging nativo.
IdentityService e AuthorizationGuard aceitam observador opcional. Cada serviço/guard
possui seu adaptador; não há singleton de auditoria nem acesso a tabelas de outro módulo.
A instância real de IdentityService permanece no lifespan da aplicação.

BFF: `server/security-audit.ts` é server-only, com interface SecuritySink,
validação/serialização fechadas e SecurityAudit injetável. AuthService usa a instância
injetada; handlers a reutilizam. Guarda administrativa admite injeção própria.
Estado por chamada e AsyncLocalStorage isolam requisições concorrentes.

AuthService associa ator de sessão somente após exchange validado por OIDC ou leitura
de sessão previamente criada por esse boundary. É o mesmo SHA-256 do JSON compacto
UTF-8 `[issuer, subject]`, prefixado por `oidc:sha256:`; não muda actor_identifier da
API. Hash é pseudônimo correlacionável, **não anonimização**. Cookie bruto, CSRF,
state ou claims não identificam o ator nos eventos. Callback rejeitado e logout com
CSRF inválido não recebem identidade inferida do cookie. Serviço técnico interno
usa somente TechnicalContext validado, como `service:import`; M2M externo permanece
fora desta entrega. Ator histórico M03 null nunca é reclassificado.

## Envelope 1.0

API/BFF compartilham nomes e semântica dos campos, mas têm perfis explícitos de tipos
adequados aos pontos observados. Não existe gerador/framework de contratos compartilhado.
Validadores e testes verificam cada perfil, inclusive hash comum, UTC e serialização.

| Campo | Contrato e minimização |
| --- | --- |
| schema_version | `1.0` fixo; alterações incompatíveis exigem nova versão |
| event_id | UUID novo; identifica observação, não pessoa/sessão |
| event_type | Enum API / união fechada BFF listados abaixo |
| occurred_at | UTC com timezone; Python normaliza timezone e rejeita datetime ingênuo; BFF ISO UTC com milissegundos e validação real da data |
| correlation_id | UUID canônico; contexto HTTP ou UUID novo para chamada interna sem contexto |
| actor_id | null ou hash `oidc:sha256:` + 64 hex; API também admite namespace técnico interno validado |
| actor_type | human, technical (API) ou unknown; null corresponde a unknown |
| action | API: Operation vigente ou identity.authenticate/permission_check/unknown_operation; BFF: login/callback/reauthenticate/identity/refresh/logout/admin.access |
| outcome | success, denied, error, unavailable; evento e resultado devem ser compatíveis |
| reason | Categoria fechada, sem mensagem arbitrária, status externo ou claims |
| resource_type | API: bibliographic/authority/metadata/system ou null; BFF: session/administrative ou null |
| resource_id | UUID de recurso conhecido na API; BFF mantém null, nunca ID/hash de sessão |
| component | api, authorization ou bff |
| required_permissions | Apenas perfil API: tupla de Permission, para dependência HTTP que exige capacidades; vazia nos demais eventos |

Identificadores de recurso são argumentos dos serviços proprietários. ResourceContext
recebe resource_id opcional ao final, preservando usos posicionais anteriores.
Nenhuma URI bibliográfica, título ou dado de leitor é incluído. Operação desconhecida
vira identity.unknown_operation, sem ecoar o valor recebido. Roles não entram no log.

Python `extra=forbid` e validação de campos; BFF verifica exatamente as chaves,
valores e compatibilidade antes da emissão. JSON tem chaves ordenadas deterministicamente,
sem extras/serialização automática. Determinismo refere-se ao mesmo evento: IDs/instantes
novos continuam únicos. Payloads de DTO públicos e Problem Details v1 não mudam.

## Taxonomia e pontos de observação

| Evento | Ponto confiável e significado |
| --- | --- |
| authentication.succeeded (API) | IdentityService após JWT, issuer/audience/exp/typ, cliente azp e mapeamento; access token autenticou identidade, sem afirmar operação autorizada |
| authentication.failed (API) | IdentityService: invalid_token, client_not_allowed ou provider_unavailable; dependência HTTP: missing_bearer/malformed_bearer; sempre ator null |
| authorization.granted / authorization.denied (API) | Guard por Operation/ResourceContext e dependência require_permissions; é decisão de acesso, não resultado de escrita |
| authentication.started (BFF) | Transação de login armazenada após authorize; não prova que houve login no provedor |
| authentication.failed (BFF) | Callback inválido/cancelado, falha de login/identity/quota storage; sempre null, sem decodificar entrada inválida |
| session.created (BFF) | createSession retornou com persistência confirmada após exchange; também representa callback aceito, sem evento redundante de redirect |
| session.revoked (BFF) | withSession confirmou revogação de sessão existente em reautenticação, refresh recusado/incerto ou API 401 |
| session.expired (BFF) | Sessão existente expirada ou sem refresh utilizável foi efetivamente removida e withSession confirmou |
| session.refreshed (BFF) | Refresh aceito e alteração confirmada pelo store, após COMMIT |
| session.refresh_failed (BFF) | Recusa/erro do refresh seguido de revogação confirmada, ou indisponibilidade definida 5xx/429 com backoff confirmado |
| session.logout (BFF) | success após revogação local confirmada; denied por requisição/CSRF inválidos; unavailable por falha de armazenamento |
| access.administrative_denied (BFF) | guardAdminContent bloqueia renderização por identidade, sessão, capacidade ou disponibilidade; ator somente se /me autenticou |
| access.quota_exceeded (BFF) | takeQuota retorna allowed=false; mantém 429/Retry-After |

API agrupa assinatura, expiração, issuer/audience, ID token e token malformado em
invalid_token; não expõe diferenças exploráveis no HTTP. JWKS indisponível, inclusive
backoff após falha do provedor, produz unavailable no evento, mas conserva **401 +
WWW-Authenticate: Bearer**. Token de cliente indevido continua 401. Permissão
insuficiente continua 403. /health permanece público e não gera autenticação fictícia.

Razões do guard: invalid_operation_resource, unpublished_projection, missing_context,
invalid_context, technical_scope e insufficient_permissions. Operação/recurso inválidos,
contexto ausente, modalidade técnica restrita e falta de permissões são distintos.
SYSTEM_ADMIN não é bypass; POLICIES, ROLE_PERMISSIONS e 17 permissões são preservados.
Pré-verificação de alternativa e verificação após carregar perfil/estado podem emitir
mais de uma decisão: não são mutações duplicadas. Um granted anterior não prova commit.

No BFF, denied significa tentativa recusada/validação incompatível; unavailable indica
indisponibilidade definida de provedor/armazenamento; error inclui operação de rede
com resultado incerto. A revogação existente após refresh incerto é preservada.
Login/logout dos handlers validam entrada antes do serviço; cada nível observa somente
sua própria rejeição, evitando evento duplicado da mesma tentativa.

## Confirmação, concorrência e perda

Eventos preparados dentro de identityLocked usam array local. Somente depois de
withSession retornar (PostgresAuthStore faz COMMIT antes do retorno) o serviço emite
confirmações. Falha/rollback descarta esse array e registra indisponibilidade sem ator
inventado. createSession usa INSERT autocommit e só depois emite session.created.
Reautenticação confirma revogação antiga antes de inserir sessão nova: são operações
existentes separadas; se criação falha, revogação já confirmada continua verdadeira.
Refresh_failed e revoked são duas observações diferentes (tentativa e mudança local).

Logout local não depende da disponibilidade do end_session_endpoint. Falha do RP logout
não desfaz revogação local nem significa logout global confirmado. Sessão inexistente
não fabrica expired/revoked por simples cookie presente. Expiração só é observada
quando sessão existente é lida/revogada; prune administrativo preexistente não emite
histórico individual e não há scheduler de expiração nesta entrega.

Logs são best effort. Exceção do sink emite sinal estático
`security_audit_sink_unavailable`, sem texto/traceback externo; não concede acesso,
substitui negação, causa rollback ou muda resultados HTTP. Falhas nativas de logging
podem ser tratadas internamente pelo próprio handler; ausência de exceção não prova
entrega. Monitorar também collector/streams/volume. Não há contagem durável de perda.

Não há tabela de segurança, fila, outbox, migração ou transação distribuída. Eventos
podem se perder entre commit e emissão, morte de processo, disco cheio, buffers ou
collector indisponível. Ordem de linhas concorrentes não é ordem global de commits.
Timestamps usam relógio do componente (configurar sincronização); não há prova
criptográfica, imutabilidade, entrega exatamente uma vez nem retenção automática.
AuditStore M03 continua fail-closed na própria transação, independentemente do logger.

## Correlação HTTP

API aceita **um** X-Request-ID de exatamente 36 caracteres ASCII, UUID na grafia
canônica minúscula com hífens. Duplicatas, excesso, controles, outras grafias e valores
malformados geram UUID novo. O ID é metadado informativo, nunca evidência de confiança,
chave de quota ou autorização. Clientes podem reutilizar um UUID válido; não assumir
unicidade da requisição pelo header. event_id é independente. Middleware ASGI externo
cobre CORS/erros 500, devolve o mesmo ID e reseta ContextVar em finally. Não lê corpo,
muda streaming nem usa estado global mutável por requisição.

Proxy Next gera UUID novo para cada requisição relevante e sobrescreve X-Request-ID
externo antes do SSR. Contexto server-side de handlers/requestIdentity/guarda mantém
esse valor em AsyncLocalStorage; callbacks internos sem HTTP geram valor novo. Handlers
expõem o ID na resposta, inclusive falhas. Chamada server-side /identity/me encaminha
X-Request-ID da requisição atual sem cookies; API mantém ID canônico recebido. Não
encaminha Authorization/Cookie externos como evidência de contexto confiável.

Não propaga identificador em redirects OIDC, state, nonce ou parâmetros de login.
Login e callback são HTTP distintos e recebem IDs distintos, sem vínculo causal
persistido entre eles. Assets excluídos do Proxy conservam comportamento preexistente.
Não implementa tracing distribuído nem associação confiável de request IDs por cliente.

## Privacidade e política operacional de armazenamento

Somente campos tipados acima são permitidos. Excluir Authorization, Cookie, Set-Cookie,
access/refresh/ID tokens, client_secret, password, code, state, nonce, code_verifier,
CSRF, session_id bruto ou hash, bodies, query integral e raw claims. Não incluir nomes,
e-mail, endereço IP, URL de callback ou exceções externas. Tokens de teste sentinela
são procurados no JSON emitido e na saída nativa efetiva. Não há endpoint ou UI de
consulta, nem envio desses envelopes para Client Components/debug logs.

Proposta **sujeita à aprovação institucional**, sem automatização no Libris:

| Responsável | Controle requerido |
| --- | --- |
| Segurança institucional | Aprovar finalidade, prazo, pessoas autorizadas, preservação de incidente e auditoria de acessos aos registros |
| Operação de infraestrutura | Coletar JSON stdout BFF e stderr logger libris.security_audit.events; separar fluxos de debug/access; TLS, storage/backups restritos, rotação e alertas de perda/volume |
| Operador de segurança autorizado | Consultar somente registros necessários; leitura segregada, sem credenciais de administração do provedor ou DML M03 por consequência |
| Administrador Libris | system:admin não concede leitura do collector; atribuição externa separada e aprovada |
| Usuário comum | Sem acesso aos eventos/streams/collector |

Prazo proposto: **90 dias** de eventos ordinários, configurável no collector pela
política operacional `security_audit_retention_days` (inteiro positivo aprovado).
Esse parâmetro pertence ao **collector**, não é variável implementada/lida pela API
ou Next.js. Configurar mesma política em índices, réplicas, arquivos, exportações e
backups; documentar eventual prazo distinto dos backups. A instituição deve aprovar
valor antes da implantação. Nesta entrega não há collector provisionado nem expurgo
agendado; somente emissão e contrato operacional verificáveis.

Procedimento de expurgo: operador autorizado aplica lifecycle/rotação do destino por
occurred_at, valida corte/relógio e retenção, remove índices/arquivos/exportações vencidos,
verifica réplicas e prazo de backups, registra evidência sanitizada (corte/contagem/
resultado/executor) fora dos dados expurgados. Exclusão lógica não comprova destruição
física em SSD, cópias, snapshots ou backups; criptografia e descarte de chaves exigem
política do destino. Nunca expurgar tabelas M03 para cumprir retenção de segurança.

Preservação excepcional para incidente: aprovação formal de segurança, finalidade,
conjunto mínimo, prazo de revisão e responsável; cópia restrita separada/lifecycle
suspenso explicitamente, registro de acesso e expurgo ao terminar a preservação.
Não há legal hold automatizado. Não se presume retenção infinita ou acesso universal.

Logs Uvicorn/Next/proxy/Keycloak/Docker/cloud podem incluir paths/queries/IPs ou outros
metadados independentemente deste contrato. Configurar para omitir queries callback,
headers sensíveis e bodies; desativar logs de debug sensíveis do provedor. Não se
homologa esses destinos pelo teste do envelope. Ataques podem gerar muitos eventos
mesmo com quotas; controlar tamanho/rotação/capacidade no ingresso e collector, sem
truncar credenciais como forma de sanitização. Volume e bloqueio do stream podem
impactar disponibilidade; ensaio de carga operacional permanece pendente.

## Preservação e validação

Nenhuma alteração em AuditEvent/AuditStore M03, Revision/SemanticRevision/Provenance,
CAS, snapshots, RDF/perfis/SHACL, machine editorial, transações ou migrações históricas.
As únicas mudanças de chamadas bibliográficas propagam UUID ao contrato de autorização.
Eventos de segurança não entram em experimental_semantic_audit_events; não existe
backfill, identidade retroativa ou revisão provocada por login/negação.

Testes específicos: `tests/api/identity/test_security_audit.py`,
`tests/integration/test_security_audit_postgres.py`,
`apps/web/tests/security-audit.test.ts` e asserções de eventos no ensaio PostgreSQL
`apps/web/tests/store.integration.ts`. Regressões #28/#38/#43 e gate obrigatório
constam do relatório com comandos/resultados, sem contar skips como aprovação.
Homologação #42, retenção/coleta durável/acesso do collector e produção são pendências
operacionais; configuração Keycloak existente não foi administrada nesta execução.
