# Baseline de segurança — M04.01 / #34

Avaliação: **2026-10-13**, America/Manaus. Branch examinada: `main`.
HEAD: `21f055ac5b7eb4130bc62068512f2739f54b8414`.
`git status --short` inicial vazio; `git branch --show-current` e
`git log -12 --oneline` executados antes das alterações. Esta documentação e as
referências acrescentadas estão no working tree, **não naquele HEAD**.

## Objetivo e escopo

Inventariar a Entrega A OIDC e sua relação com M03, consolidando a
[matriz de acesso](security-access-matrix.md), o
[modelo de ameaças](security-threat-model.md) e os
[critérios de saída](security-m04-exit-criteria.md). A
[verificação desta execução](security-m04-01-verification.md) registra resultados
atuais; [identity-verification.md](identity-verification.md) permanece evidência
histórica de 2026-10-10. Testes de assinatura local e HTTPX MockTransport não
comprovam integração real com Keycloak.

Estados usados em todos os documentos:

| Estado | Significado |
| --- | --- |
| IT — implementado e testado | Código e testes identificados para a garantia delimitada; execução atual discriminada no relatório |
| IO — implementado sem validação operacional completa | Código/configuração presente, mas falta integração relevante ou homologação |
| EP — especificado ou planejado | Contrato ou requisito sem implementação correspondente |
| ND — não implementado ou diferido | Capacidade fora da entrega atual, dependente de marco posterior |

IT não significa aprovação institucional, produção ou cobertura exaustiva.
Persistência PostgreSQL tem testes físicos identificáveis e relatórios históricos;
sua execução atual é separada da suíte padrão.

## Componentes e responsabilidades

FastAPI é Resource Server, conforme [ADR 0016](../decisions/0016-oidc-resource-server.md).
O provedor externo autentica pessoas, mantém credenciais e emite tokens. O módulo
identity valida access tokens e traduz papéis para permissões; não faz login,
refresh ou cadastro de usuários. Next.js renderiza páginas bilíngues sem sessão.
Bibliographic coordena conteúdo, revisões, estados e auditoria no PostgreSQL;
autoridades Agent/Subject não são identidades de usuários. Elasticsearch é futura
projeção reconstruível, sem cliente de indexação operacional.

Nas tabelas, `I` refere-se a
[`apps/api/src/libris/modules/identity/`](../../apps/api/src/libris/modules/identity/),
`B` a [`apps/api/src/libris/modules/bibliographic/`](../../apps/api/src/libris/modules/bibliographic/).
São atalhos de caminhos, não novos módulos ou fontes normativas.

## Inventário técnico

| Mecanismo | Estado e comportamento observado | Evidência no checkout / teste |
| --- | --- | --- |
| Configuração | IT: desabilitado por padrão; issuer absoluto sem credenciais/query/fragment; HTTPS quando OIDC ativo em production; audience/client/discriminador não vazios | [Settings.validate_oidc](../../apps/api/src/libris/core/config.py); `test_settings_fail_closed` em [test_identity.py](../../tests/api/identity/test_identity.py) |
| Assinatura e algoritmos | IT: PyJWT/cryptography; RS256 padrão; allowlist configurável RS256/384/512, ES256/384/512, EdDSA; rejeita none/HS256, kid ausente e crit não vazio | `I/infrastructure/oidc.py::validate`; `test_disallowed_algorithm`, `test_signature_and_manipulated_roles`, `test_incompatible_keys`; sucesso criptográfico testado com RSA/RS256, não com todos os algoritmos permitidos |
| Claims assinadas | IT: iss/aud/exp/sub obrigatórios; emissor exato, subject não vazio; exp/nbf/iat numéricos finitos; PyJWT valida datas com tolerância padrão 30 s; typ=Bearer no payload obrigatório por padrão | `OIDCValidator.validate`; `test_invalid_claims`, `test_expiration_infinity` |
| Access versus ID token | IT: claim/valor configuráveis; typ do header JOSE não substitui discriminador assinado; ID/ausência rejeitados | `test_invalid_claims`; não comprova formatos efetivamente emitidos por Keycloak |
| Descoberta e confiança | IT para emissor incompatível: descoberta sob demanda no issuer configurado; jwks_uri vem da descoberta confiável; jku/x5u do token não são usados; redirects desativados, proxies do ambiente desativados no cliente real | `OIDCValidator._refresh/_document`, [create_app](../../apps/api/src/libris/main.py); `test_provider_failure_and_backoff`, `test_cache_expiration_rotation_and_refresh_limit` verifica jku; x5u/redirect/proxy são inspeção de código, sem teste específico identificado |
| Limites de entrada | IT para JWT malformado/16 KiB; limites implementados de 1 MiB por documento e 100 chaves JWKS, timeout padrão 5 s | `_document/_refresh/validate`; `test_malformed`; limites de documento/chaves e key_ops não têm teste dedicado identificado |
| Seleção de chave | IT: única chave compatível kid/alg/use/key_ops, tipo RSA/EC/OKP; ambiguidade/chave inválida recusadas | `_matching_key`; `test_incompatible_keys` cobre use/alg/duplicação/chave inválida |
| Cache e rotação | IT: TTL padrão 300 s, lock por instância, intervalo mínimo 10 s inclusive falhas; kid desconhecido provoca refresh limitado; sem fallback de chave expirada | `test_cache_expiration_rotation_and_refresh_limit`, `test_concurrent_initial_requests_share_refresh`, `test_no_stale_keys_after_expiration`, `test_unknown_key_after_refresh` |
| Indisponibilidade OIDC | IT: AuthenticationError/ProviderUnavailable não libera anonimato; chave conhecida em cache válido ainda pode autenticar sem consulta; cache expirado/sem chave falha | `test_provider_failure_and_backoff`, `test_no_stale_keys_after_expiration`; dependência converte AuthenticationError em 401 |
| RBAC centralizado | IT: 17 permissões, seis papéis; união de concessões conhecidas, desconhecidos concedem zero; admin recebe enum completo, sem bypass por system:admin | `I/domain/permissions.py`, `I/infrastructure/role_mapper.py`; `test_role_mapping`, `test_union_and_trusted_role_source`; [matriz](security-access-matrix.md) |
| Identidade estável | IT: SHA-256 de JSON canônico do par issuer/sub com prefixo oidc:sha256; não usa e-mail/nome nem normaliza o par | `I/domain/models.py::actor_identifier`; `test_identifier_stability`, `test_valid_token_and_actor`; hash não é anonimização |
| Enforcement HTTP | IT: /identity/me autenticado; require_permissions exige todas as permissões solicitadas, 401 com WWW-Authenticate: Bearer e 403 quando insuficiente | `I/api/dependencies.py`, `I/api/router.py`; `test_fastapi_authentication_authorization_and_override`; rotas test-protected/test-admin existem somente no teste |
| Superfície pública | IT: GET /health liveness, GET /api/v1/identity/me; FastAPI também registra /openapi.json, /docs, /docs/oauth2-redirect e /redoc públicos; middleware responde preflight CORS | `create_app`; [test_startup.py](../../tests/api/test_startup.py)::test_openapi_exposes_health_contract; documentação automática não está na lista paths de negócio do OpenAPI |
| CORS | IT: origens explícitas, GET, Authorization e X-Request-ID permitidos; allow_credentials=False | `create_app`; `test_bearer_cors_preflight`, `test_cors_allows_only_configured_origin`; CORS não autentica clientes fora do navegador |
| Ator e auditoria | IT interno: audit_actor confere tipo e hash; payload dict/ator divergente recusados; atores técnicos explicitamente configurados; histórico NULL preservado | `B/application/audit.py`; [test_audit_history.py](../../tests/api/test_audit_history.py)::test_trusted_human_unknown_and_privacy, test_service_rejects_payload_actor_before_storage |
| Conteúdo de baixo nível | IT como serviço interno: create/revise/read aceitam chamador confiável; create/revise admitem actor=None e não exigem bibliographic:create/update | `B/application/service.py`; autorização geral no boundary é EP para #38/M05; não expor read como leitura pública de rascunhos |
| Histórico/restauração | IT interno: HistoryService autoriza revisões/auditoria, restore_content exige metadata_revision:read/create; read_editorial exige read de revisão e auditoria | `B/application/history.py`, `service.py`; `test_history_denial_precedes_storage`, `test_history_permission_policy`; testes físicos em [test_audit_postgres.py](../../tests/integration/test_audit_postgres.py) |
| Editorial persistente | IT de domínio, IO operacional: permissões por transição, perfil/SHACL/referências, candidata isolada, CAS de conteúdo/estado e auditoria no mesmo commit | `B/application/editorial.py`, `editorial_postgres.py`, `infrastructure/editorial.py`; [test_editorial.py](../../tests/api/test_editorial.py), [test_editorial_postgres.py](../../tests/integration/test_editorial_postgres.py); ADR 0028 |
| Persistência experimental | IO: migrações 0001–0004 incrementais, nullable actor sem backfill; triggers/constraints protegem DML normal; startup não migra nem conecta para saúde | [migrações](../../apps/api/migrations/versions/), `test_lifespan_and_health_without_external_services`; testes físicos não equivalem a homologação |
| Keycloak | IO: overlay e realm sem usuários; API bearer-only; web público PKCE S256; implicit/password grant desativados; audience/client roles no access token | [realm](../../infrastructure/keycloak/libris-realm.json), [overlay](../../docker-compose.oidc.yml); quatro papéis provisionados, faltam reviewer/publisher; #35 |
| Next.js e sessão | ND: / redireciona a /pt; /pt e /en institucionais; callback registrado no realm não existe no App Router; sem login/logout/sessão/refresh ou consumo de /me | [apps/web/src/app](../../apps/web/src/app/); #36/#37 |
| Segurança HTTP/operacional ampliada | EP: CSP/HSTS, CSRF de sessão futura, quotas/rate limit, observabilidade e retenção de segurança, readiness, TLS/rede/backup de produção | #40/#41/#42; Compose local não satisfaz esses requisitos |
| Descoberta e demais domínios | ND: sem índice funcional, APIs CRUD, editor ou circulação | [domínios](domains.md), [overview](overview.md); M05–M15, atribuição detalhada somente quando houver escopo aprovado |

## Coerência com M03 e riscos conhecidos

Os [contratos v1](catalogographic-contract.md) e sua
[rastreabilidade](catalogographic-contract-traceability.md) permanecem intactos.
Revisões/snapshots imutáveis, UUID/URI armazenados e CAS seguem ADRs
[0011](../decisions/0011-independent-revisions-concurrency.md) e
[0015](../decisions/0015-transactional-rdf-consistency.md). Estado e revisão editorial
são independentes; publicação seleciona aprovada exata, nunca a candidata
automaticamente. [ADR 0028](../decisions/0028-editorial-transactions.md) concretiza
as pendências originais dos ADRs 0026/0027, inclusive RETURN/ARCHIVE.
Os textos históricos desses ADRs e da #28 não devem ser lidos como inexistência
atual de persistência editorial: o adaptador e a migração 0004 estão no checkout.

Principais limites: confiança no chamador interno que constrói AuthenticatedActor;
create/revise/read sem autorização geral; ausência de escopo por instituição/recurso;
revogação de JWT não instantânea; caches por worker e descoberta fixada no lifespan;
401 temporário em rotação; privilégio administrativo amplo; SQL privilegiado pode
contornar triggers/gate; textos source/process/reason não detectam PII automaticamente.
Não há regra de quatro olhos que impeça acumular cataloger/reviewer/publisher.
O gate editorial conservador serializa decisões e requer avaliação de carga futura.

Produção exige configuração específica: Compose local usa HTTP, start-dev e
Elasticsearch sem segurança. APP_ENV validado não transforma automaticamente
defaults de banco/CORS/infraestrutura em uma implantação segura. jwks_uri pode usar
host distinto autorizado pela descoberta; não há allowlist adicional de egress.
Comprometimento do provedor/configuração/host não é resolvido pela assinatura JWT.

## Fontes, decisões e dependências

Foram lidos AGENTS.md, README, overview, domains, contrato/rastreabilidade, identidade
e verificação histórica, contratos editorial/persistência/proveniência, ADRs
0016/0026/0027/0028 e os ADRs de concorrência/consistência citados.
Inspeção de código, testes e migrações precedeu esta escrita.

Consulta somente de leitura ao GitHub em 2026-10-13:
[issue #34](https://github.com/inacioigne/libris/issues/34) aberta, milestone 4;
[#27](https://github.com/inacioigne/libris/issues/27),
[#28](https://github.com/inacioigne/libris/issues/28),
[#43](https://github.com/inacioigne/libris/issues/43),
[#30](https://github.com/inacioigne/libris/issues/30) e
[#31](https://github.com/inacioigne/libris/issues/31) fechadas, milestone 3.
Issues #35–#42 abertas, milestone 4, com dependências listadas no
[checklist](security-m04-exit-criteria.md). Esses estados são evidência de planejamento,
não prova de funcionalidade. A consulta não alterou issues/milestones/remoto.

**Nenhum ADR novo necessário:** a entrega explicita controles, lacunas e uso das
decisões vigentes; não escolhe novo mecanismo, armazenamento ou arquitetura.
Mitigações futuras do modelo são recomendações vinculadas a issues, sem declarar
que já foram implementadas. ADRs históricos e evidências anteriores permanecem intactos.

## Atualização M04.03 — 2026-10-13

A baseline/tabelas acima representam o diagnóstico M04.01 datado; não foram
reescritas como evidência de testes posteriores. O App Router agora contém
[BFF OIDC e sessões compartilhadas](identity-web.md), decisão
[ADR 0030](../decisions/0030-web-oidc-sessions.md), com
[resultados próprios](identity-web-verification.md).

| Fronteira/ameaça | Controle implementado M04.03 | Limite restante |
| --- | --- | --- |
| F1/F3/F4, TH13 | Tokens somente server-only, PostgreSQL cifrado, cookie ID opaco, no-store/referrer | Logs do proxy, host/secret manager e backups exigem configuração operacional |
| TH15 | Code/S256, state/binding por tentativa, nonce/assinatura/aud/issuer, uso único, novo ID; POST Origin/Host + CSRF no logout | XSS pode executar ações no contexto da vítima; revisão CSP/pentest #40/#42 |
| TH16 | Redirect URI fixa, retorno /pt ou /en canônico, endpoints discovery restritos à origem do issuer | Confiança no provedor/configuração; homologação navegador real pendente |
| TH07/TH22 | Timeout/limite de resposta, locks PG e backoff por sessão, fail closed | Quotas globais, avaliação de carga/pool/locks e disponibilidade pendentes |
| TH21/TH23 | HTTPS obrigatório em production, cookies Secure/__Host-, logout local commit antes de RP logout | Compose é local; JWT previamente emitido não tem revogação global instantânea |
| M04 sessão web | Código e testes negativos; persistência real isolada e ensaio HTTP próprio | Keycloak web real, leitores de tela e produção não homologados |

/health permanece público; /identity/me continua Bearer da API. Páginas públicas
não dependem de login; identidade renderizada provém somente da API. Nenhuma
permissão de CRUD/shell M05/#37 foi introduzida. Auditoria de segurança #41,
autorização contextual #38/#39 e homologação abrangente #42 continuam separadas.
