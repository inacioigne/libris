# Verificação M04.09 — issue #42

## Inspeção inicial, antes das alterações de código

Data: 2026-10-14, America/Manaus. Branch `main`; HEAD inicial
`cec0be2acaef2af724c7fbf6785306df7e4c2a06`. Working tree limpo; diff check
sem erros. Nenhuma alteração preexistente. Refs locais main/origin/main coincidem;
não foi feito fetch/pull. GitHub consultado em modo leitura: #42 aberta, milestone 4;
#35–#41 fechadas, sem inferir aprovação pelo estado remoto.

Leitura: AGENTS, README, overview, domains, contrato catalográfico, identity,
identity-web, identity-keycloak-local, baseline, access-matrix, threat-model,
exit-criteria, operation-authorization, governance, http-security, security-audit,
identity-verification, ADRs 0016 e 0030–0035 e relatórios M04.01–M04.08.

| Componente | Implementado | Offline existente | Infraestrutura real histórica | Lacuna inicial / classificação |
| --- | --- | --- | --- | --- |
| JWT/JWKS | validator limitado, cache/lock/backoff | test_identity.py | M04.02/06 | parcial: ampliar tipos nbf/iat e reproduzir provedor |
| OIDC/Keycloak | realm, clientes e harness | assinatura RSA/MockTransport | M04.02/03/06 | parcial: execução atual pendente |
| Login PKCE | OpenIdProvider + state/nonce/binding | auth.test.ts | M04.03 | parcial: reproduzir S256 real |
| Callback | consumo único antes da troca | auth/http-security/security-audit | M04.03 | parcial: resposta incompleta, URI e falha de persistência |
| Sessões | PostgreSQL cifrado, refresh/locks | auth.test.ts | M04.03/07/08 | parcial: execução atual, falha após validação |
| Logout | Origin/CSRF e revogação local | auth/http-security | M04.03/07 | parcial: reproduzir; não equivale a revogação global |
| RBAC | seis papéis, 17 permissões | test_identity/authorization | M04.02/06 | parcial: execução atual |
| Autorização por operação | guard nos serviços internos | matriz parametrizada | M04.05/08 PostgreSQL | parcial: regressão atual; nenhum CRUD HTTP M05 |
| CORS/CSRF | allowlist, state/binding, POST Origin/CSRF | test_http_security, auth | M04.07 HTTP | parcial: execução atual |
| Cookies/CSP | HttpOnly, Secure HTTPS, nonce, no-store | auth/http-security | M04.07 Chromium com OIDC simulado | parcial: navegador atual e Keycloak real |
| Quotas | três rotas, PostgreSQL compartilhado | relógio controlado | M04.07/08 | parcial: concorrência entre pools atual |
| Auditoria/logs | envelope fechado e sink best effort | test_security_audit, security-audit | M04.08 PostgreSQL | parcial: atual; coleta/retenção operacional não implementadas |
| Persistência | Alembic 0005 + M03 experimental | regressões internas | M04.05/07/08 | parcial: bancos vazios separados atuais |
| SSR administrativo | guard server-side, pt/en | admin.test.ts | M04.04 FastAPI + issuer simulado | parcial: encadear navegador e Keycloak real |

Esta matriz registra o diagnóstico, não resultados desta execução. Testes históricos
não foram contados como aprovação atual. Infraestrutura disponível: imagens locais
PostgreSQL 17/Keycloak 26.8.0 e Chrome; Node 24 instalado fora do PATH inicial.
Containers preexistentes libris-api-1, libris-postgres-1, libris-keycloak-1 e
libris-elasticsearch-1 devem permanecer intactos.

## Revisão dos commits solicitados

| Commit | Componentes/contratos e testes | Risco de integração / ação |
| --- | --- | --- |
| cec0be2 | envelope, correlação, observadores identity/guard/BFF; security-audit e regressão PostgreSQL | confirmação antes/depois de COMMIT, privacidade e sink falho; reutilizar testes |
| 428a9e3 | Alembic 0005 cria/adota libris_web; harnesses usam Alembic; test_web_migrations_postgres | drift legado, índices, rollback preservador; usar banco exclusivo |
| a12908c | CORS/headers externos API, CSP nonce/Proxy, limites e quotas BFF; HTTP/Chrome | hidratação/CSP, quota compartilhada, fail closed; reproduzir build e HTTP |
| 20b8bd6 | azp humano assinado, governança externa e harness real | cliente técnico promovido indevidamente, revogação de JWT pré-emitido; testar sem prometer revogação instantânea |
| 75c3759 | Operation/ResourceContext e guard M03, mapa explícito; matriz e PostgreSQL | kind persistido, seleção publicada/CAS/NULL, ausência de bypass admin; regressão sem endpoints novos |

Os diffs, testes e evidências foram confrontados com o código atual. Não há
necessidade demonstrada de nova arquitetura, dependência ou ADR.

## Cobertura executável consolidada

Os nomes abaixo identificam asserções efetivas, não endpoints novos. Resultado
das execuções aparece na próxima seção; parametrizações reutilizam a infraestrutura
existente. Condições equivalentes não foram duplicadas artificialmente.

| Requisito | Teste / boundary |
| --- | --- |
| JWT válido, assinatura/adulteração | test_identity::test_valid_token_and_actor / test_signature_and_manipulated_roles |
| JWT vazio/malformado/16 KiB, Bearer ausente/malformado | test_malformed; test_fastapi_authentication_authorization_and_override; test_security_audit de autenticação HTTP |
| alg none/HS256/confusão simétrica, allowlist | test_disallowed_algorithm / test_settings_fail_closed; test_incompatible_keys |
| kid ausente/desconhecido/duplicado/alg/use/key_ops | test_incompatible_keys / test_unknown_key_after_refresh |
| iss/aud/exp/nbf/iat ausentes/incorretos/malformados/futuros | test_invalid_claims (tipos adicionais), test_signed_non_string_issuer; PyJWT + política numérica finita |
| ID versus access, discriminador assinado/header typ | test_negative_tokens_have_http_bearer_challenge; test_invalid_claims |
| Cliente humano azp confiável | test_only_signed_interactive_client_can_enter_human_boundary / test_client_binding_requires_signature_and_does_not_classify_subject_prefix |
| JWKS/discovery inválidos/limites/timeout/redirect | test_invalid_provider_documents_fail_closed / test_provider_failure_and_backoff |
| Cache/rotação/refresh falho/backoff/concorrência | test_cache_expiration_rotation_and_refresh_limit / test_refresh_failure_recovery_and_removed_key / test_no_stale_keys_after_expiration / test_concurrent_initial_requests_share_refresh |
| Seis papéis × 17 permissões, união/negação | test_authorization::test_six_roles_seventeen_permissions / test_role_unions_have_no_fallback |
| Operação/recurso, admin sem bypass, técnica restrita | test_system_admin_alone_has_no_functional_bypass / test_unknown_permission_and_wrong_resource_are_denied / test_technical_scope_and_grants_are_independent / test_composed_permissions_require_all |
| Header/body/actor não concedem acesso | test_operation_guard_ignores_forged_http_authority; test_direct_application_denies_before_storage |
| Revisões/auditoria/editorial/publicada/candidata | test_read_public_uses_selected_revision_never_current; test_public_requires_exact_published_projection; test_audit_history/test_editorial e equivalentes PostgreSQL |
| S256/state/nonce/binding/abas independentes | auth.test.ts: valid signed OIDC flow, independent transactions, callback rejects; http-security: concurrent replay |
| Callback URI, duplicatas, ausência, erro, incompletude | auth.test.ts: callback rejects mismatched URI, incomplete token response; falha não cria sessão nem repete grant |
| Persistência após autenticação/reautenticação | auth.test.ts: reauthentication persistence failure; security-audit: session creation storage failure / commit failure |
| Cifra/AAD/corrupção/keyring e banco indisponível | auth: encryption authenticated; store.integration: ciphertext/corrupted payload/rollback; security-audit: storage failures |
| Fixation/replay/expiração/refresh/API 401/logout | auth.test.ts: session fixation, concurrent refresh, invalid/no/expired refresh, API 401, logout replay; store.integration entre pools |
| Origin/CSRF/cookies duplicados/form malformado | auth/http-security.test.ts: handlers, absent CSRF, duplicate cookies/forms, wrong-session CSRF, bounds |
| CORS/preflight/401/403/500/HSTS | test_http_security.py; test_identity HTTP; nunca é autorização por cookie |
| CSP/nonces/cache/headers e hidratação | http-security.test.ts + http.e2e.ts/Chrome: script sem nonce bloqueado e Link hidratado |
| Quotas/429/Retry-After/clock/503/concorrência | http-security.test.ts e store.integration (dois pools PostgreSQL reais) |
| Envelope/UTC/ator/recursos/correlação/sink/logs | test_security_audit.py, security-audit.test.ts, test_security_audit_postgres.py; real Keycloak SSR correlaciona refresh BFF e autenticação API |
| Migrações/legado/NULL/CAS/transações | todos os testes tests/integration/*postgres.py em bancos exclusivos, incluindo 0005 adoção/re-upgrade |
| Provedor e governança reais | test_keycloak_oidc.py: Code/PKCE/token/rotação, concessão/revogação/disable/refresh/expiração/admin events |
| Browser/SSR pt/en real | keycloak.real.ts + browser.ts: reader negado, cataloger autorizado, callback inválido, sessão expirada, logout e provedor pausado somente pelo dono do ensaio |

JWT RS256 é a política realmente adotada neste ensaio. A allowlist admite outros
algoritmos assimétricos por configuração, sem declarar ensaio positivo completo
de ES*/EdDSA. Role desconhecida autentica /me com zero concessões; 403 exige
operação com permissão adicional, testada nos boundaries internos/TestClient.
Nenhum endpoint CRUD/probe foi acrescentado à API implantada.

## Alterações e defeitos comprovados

- Serviço BFF: valida URI de callback antes do consumo/troca. Três testes novos
  demonstraram consumo prematuro em origem/path incompatíveis e aceitação de
  fragmento na chamada direta. O handler HTTP já fixa a URI; fragmentos não são
  enviados por browsers. Trata-se de endurecimento verificável do boundary,
  sem alegar exploração remota ou alteração do DTO/ADR.
- Testes API: 26 casos adicionais de claims, incluindo issuer assinado não textual
  e exp/nbf/iat não numéricos/não finitos. Sem mudança da política JWT vigente.
- Testes web offline: oito casos novos de URI, resposta incompleta e falha de
  reautenticação após revogação. Garantem ausência de sessão e de retry do code.
- Harness Python real: CookieJar não enviava cookies Secure do Keycloak em
  HTTP 127.0.0.1. Adaptação restrita ao host/path do provedor e flag de isolamento;
  cinco testes verificam condições e preservam HTTPS/outros hosts/paths. Não muda
  cookies do produto nem configuração de segurança do Keycloak.
- Browser/harness real: quatro percursos em perfis temporários; provas SSR/RBAC,
  expiração e indisponibilidade, além da correlação emitida BFF → API e privacidade.
- Script opt-in: recursos novos/tabelas isoladas, Alembic explícito, captura privada,
  cleanup por nome, propagação de erro e recusa de skips inesperados. Gate mantém
  suíte offline e inclui análise estática do script novo.

## Falhas e repetições

| Execução inicial | Resultado / causa | Correção e repetição |
| --- | --- | --- |
| npm test baseline | 149 passaram | nenhuma falha; baseline antes dos novos casos |
| npm test novos casos de URI | 154 passaram, 3 falharam | URI verificada no AuthService antes do consumo; 157 passaram |
| pytest test_identity.py inicial | 114 passaram, 1 falhou na geração da fixture iss=42 | encoder PyJWT rejeita issuer não textual; fixture passa por JWS assinado, sem desligar validação; gate posterior 1668 passou |
| Primeira integração isolada | 66 passaram, 2 falharam, 261 warnings | CookieJar loopback; corrigido harness, cinco testes novos; segunda integração 73 passaram, zero skips |
| Ruff chamado inicialmente da raiz | regras/contexto de imports diferentes e script com linhas longas | usar diretório apps/api conforme AGENTS, formatar somente arquivos novos/alterados; Ruff passou |
| npm typecheck chamado inicialmente na raiz | package.json ausente (exit 254) | executado em apps/web; passou, sem mudança de dependências |
| Terceira integração, caso adicional de expiração no Chrome | API 73, store 1 e HTTP 2 passaram; Keycloak web 1 falhou por timeout da asserção | fixture alterava só expires_at usado para prune; corrigida para expirar também expiresAt no ciphertext conforme contrato; sem mudança do store |

Ruff format corrigiu comprimento do script; uma linha restante foi corrigida
manualmente. Warnings Starlette/httpx e RDFLib não foram ocultados. Nenhuma falha
de provedor real foi classificada como skip/aprovação. Novas repetições sempre usam
bancos e realm novos, sem reset de bases anteriores.

## Ferramentas, artefatos e isolamento

| Ferramenta | Versão observada |
| --- | --- |
| Python | 3.13.15 |
| Node / npm / uv | 24.16.0 / 11.15.0 / 0.12.21 |
| Docker Engine / Compose | 29.8.2 / 5.6.0 |
| PostgreSQL real | 17.11, Debian 17.11-1.pgdg12+2, imagem postgres:17-bookworm |
| Keycloak real | 26.8.0 (startup observado), start-dev/H2 descartável |
| Chrome real | 155.0.8059.39 |
| FastAPI / Next.js | 0.143.0 / 16.4.0 |
| SQLAlchemy / Alembic / PyJWT | 2.0.54 / 1.20.0 / 2.15.1 |
| pytest / HTTPX | 9.1.1 / 0.28.1 |

Imagem PostgreSQL observada:
`sha256:3645570cccdfa447589da9f57dd740faa29b30938e861289a5574b6ca6b03826`.
Nenhum lock/dependência foi alterado; ferramentas existentes reutilizadas. Sem
instalação de framework de browser ou novo serviço de produção. O build lê os
arquivos .env locais ignorados já existentes; nenhum conteúdo secreto foi lido
para o relatório ou modificado. Os harnesses fornecem configuração de ensaio
explicitamente e o runner descarta variáveis de aplicação/teste/proxy herdadas.

Recursos de trabalho observados e preservados:
`f4afe5fd8c14 libris-api-1`, `e0f3b27b3d2a libris-postgres-1`,
`84179d1c6f3a libris-keycloak-1`, `93ffc0fbb72b libris-elasticsearch-1`.
Portas 8000/5432/8081/9200 desses serviços não foram usadas para os ensaios.
Todos os testes usam portas loopback efêmeras e nomes `libris-m0409-<aleatório>`.
O runner cria oito bancos exclusivos: semantic, audit_migration,
editorial_migration, web_migration, web_store, web_http, web_admin, web_keycloak.
DDL/downgrade/fixtures são limitados a esses bancos novos em PostgreSQL tmpfs.
Keycloak novo usa data tmpfs e cópia de realm importável sem usuários; credenciais
aleatórias apenas em ambiente/memória. Não há import sobre realm de trabalho.

Logs completos de comandos ficam privados em /tmp (diretórios 0700/arquivos
0600). Artefatos sanitizados nesta documentação incluem somente contagens,
comandos/etapas, versões, limitações e identidade de recursos não secretos.
Não publicar logs brutos sem revisão: falhas de bibliotecas/test runners podem
conter contexto sensível mesmo quando envelopes do produto são minimizados.

## Resultados do gate e ensaios concluídos

| Comando efetivamente executado | Aprovados | Falhas | Skips / resultado |
| --- | ---: | ---: | --- |
| npm test baseline | 149 | 0 | 0 |
| npm test após correção URI | 157 | 0 | 0 |
| bash scripts/check.sh, primeiro gate | API 1668 + web 157 | 0 | 0; Ruff/mypy/build/typecheck/Compose passaram |
| bash scripts/check.sh, gate final | API 1668 + web 157 | 0 | 0; API 477 warnings, 76,88 s; mypy 86 arquivos; demais checks passaram |
| uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py, apps/api | — | 0 | passou após ajustes |
| uv run pytest -c pyproject.toml ../../tests/integration/test_keycloak_oidc.py -m 'not keycloak' | 12 | 0 | 2 deselected, 0 skips; 1 warning; nenhum provedor necessário |
| npm run typecheck, apps/web após testes finais | — | 0 | passou |
| verify-m04-integration.py --isolated --keycloak --browser, segunda execução | API 73 + store 1 + HTTP 2 + Keycloak web 1 | 0 | 0; API 257 warnings/34,57 s; Chrome real com reader/cataloger/logout |
| verify-m04-integration.py --isolated --keycloak --browser, quarta/final execução | API 73 + store 1 + HTTP 2 + Keycloak web 1 | 0 | 0; API 259 warnings/37,23 s; Chrome real com callback inválido/expiração/provedor pausado e correlação BFF/API |

Cada runner invoca explicitamente Alembic upgrade head, Python -m pytest
tests/integration, npm run test:integration, npm run test:http e npm run
test:keycloak nos diretórios apropriados. A suíte real não pertence ao gate padrão.
Nenhum skip constitui prova. Números acima são desta sessão, sem reutilização das
contagens históricas. Testes pure PKCE/cookie dentro da integração são incluídos
no total 73; não são todos chamadas a infraestrutura. Um teste Node integra muitas
asserções/cenários; não inflar a contagem por etapas.

A quarta execução foi concluída com exit 0 e cleanup aprovado para PostgreSQL e
Keycloak `libris-m0409-a13a94425094f8d9-*`. Ensaio Keycloak web: 1 teste Node
incluindo quatro percursos Chrome com perfis novos (reader, cataloger, expiração,
refresh durante pausa), frontend construído, PostgreSQL/FastAPI/provedor reais.
HTTP mock: 2 testes Node, um com API real/issuer simulado e outro com API/OIDC
simulados e Chrome CSP/hidratação. Não confundir os emissores simulados com Keycloak.
Os logs finais privados estão em `/tmp/libris-m0409-a13a94425094f8d9-uuu8sidc`;
gate em `/tmp/libris-m0409-gate-final.log` e resumo de integração em
`/tmp/libris-m0409-integration-4.log`. Esses caminhos são temporários locais, não
artefatos públicos/duráveis. O relatório versionável preserva as evidências sanitizadas.

## Matriz de saída M01–M12

Referência: security-m04-exit-criteria.md. “Atendido tecnicamente local” descreve
software/ensaio, sem presumir decisão institucional ou implantação de produção.

| ID / descrição | Estado | Evidência / teste / resultado | Risco / dependência / condição de aprovação |
| --- | --- | --- | --- |
| M01 arquitetura/confiança | atendido tecnicamente local | ADRs revisados, diff sem nova arquitetura/CRUD; gate aprovado | revisão do mantenedor; mudanças futuras exigem nova avaliação |
| M02 identidade OIDC | atendido tecnicamente local | test_identity offline + Keycloak Code/PKCE/RS256/ID recusado e /me real aprovados | root de confiança, relógios e outro algoritmo/provedor exigem novo ensaio |
| M03 Keycloak | atendido no ambiente isolado | discovery/JWKS/clientes/S256/aud/typ/papéis/rotação reais; 73 testes integração sem skips | DNS/realm persistido/implantação canônica não homologados; validar configuração alvo |
| M04 sessão web | atendido no ambiente isolado | state/binding/nonce/uso único/cifra/refresh/fixation/logout e PostgreSQL/BFF real aprovados | bearer roubado/commit incerto/SSO confirmado; TLS/cookies HTTPS runtime exigem implantação |
| M05 interface administrativa | atendido no ambiente isolado | SSR API real e Chrome reader/cataloger pt/en, guarda não renderiza capabilities sem permissão | leitor de tela/teclado/auditoria visual completos requerem revisão humana |
| M06 autorização backend | atendido tecnicamente local | seis papéis×17 e guard por operação/recurso; PostgreSQL/regressões aprovados | futuros endpoints M05 devem propagar contexto e usar políticas existentes |
| M07 governança | parcial operacionalmente | ensaio real revogação/disable/refresh/expiração/admin events; menor privilégio | instituição deve aprovar papéis, responsáveis, prazos; M2M/multiunidade diferidos |
| M08 HTTP/proteção | atendido tecnicamente local; parcial implantação | CORS/CSRF/CSP/cookies/no-store/limites/quotas e Chrome aprovados | TLS/ingress real, disponibilidade/carga e logs externos dependem da implantação |
| M09 auditoria/proveniência | atendido contrato de emissão; parcial operação | envelope/correlação/ator NULL/privacidade/sink falho/M03 aprovados | best effort permite perda; collector/retenção/expurgo/acesso não implementados pelo Libris |
| M10 testes/E2E | atendido tecnicamente local; aceite pendente | gate offline + roteiro/runner opt-in e browser/provedor reais | mantenedor precisa revisar resultados e aceitar riscos delimitados; não é pentest |
| M11 persistência | atendido tecnicamente local | Alembic/legado/rollback/CAS/revisão/auditoria/publicada/draft em PostgreSQL real aprovados | esquema experimental; backups/recuperação operacionais fora deste ensaio |
| M12 operação/infraestrutura | parcial, sem aprovação institucional | dev/produção separados, secrets efêmeros, tmpfs/isolamento e /health público | revisão TLS/rede/segredos/logs/backups/capacidade da implantação alvo e responsável; Compose não é produção |

## Aceite #42 e riscos residuais

| Critério remoto | Estado | Justificativa |
| --- | --- | --- |
| Suíte principal offline determinística e integração real documentada | atendido tecnicamente | gate sem serviços, runner opt-in e roteiro, positivos/negativos reais separados |
| Resultado em identity-verification ou sucessor com falhas e riscos | atendido tecnicamente | relatório independente linkado, histórico preservado, falhas/repetições identificadas |
| Critérios de saída M04 atendidos antes de rotas protegidas M05 | parcial | M07/M08/M09/M12 têm condições operacionais/institucionais explícitas; não houve aceite desses riscos pelo mantenedor |

Aceite técnico das implementações/testes/documentos: entregas verificáveis localmente.
**Recomendação de fechamento #42: ainda não**, pois seu terceiro critério exige
revisão/aceite dos critérios de saída, não apenas testes verdes. **M04 integralmente
homologada: não**; o fluxo integrado local tem evidências reais, mas não substitui
aprovação operacional/institucional. **Produção: não aprovada** por esta execução.
Não há bloqueio atual de ferramenta para os ensaios implementados; pendências não
são apresentadas como infra indisponível.

| Risco restante | Impacto | Ação / responsável |
| --- | --- | --- |
| Logs best effort, sem collector/retention aprovados | perda de trilha ou acesso indevido operacional | segurança/operação aprovam destino, retenção, acesso, expurgo, monitoramento e backups |
| HTTP/start-dev/H2 local; TLS/ingress/DB runtime não ensaiados | configuração alvo pode expor tráfego ou DDL excessivo | operador valida HTTPS/TLS/grants DML, secret manager e rede da implantação |
| JWT pré-emitido permanece até exp+skew; SSO global não confirmado | token roubado/papel revogado mantém capacidades temporariamente | governança aprova prazos/MFA/procedimento; não prometer revogação instantânea |
| Quota global, pool/locks e streams sob carga | atacante pode prejudicar disponibilidade | ingress/capacidade/carga e limites globais/monitoramento em implantação própria |
| Root/provedor/DBA/código interno confiáveis | comprometimento privilegiado ultrapassa fronteiras do teste | segregação e procedimentos operacionais; não inferir resistência universal |
| Acessibilidade e browsers adicionais | ensaio Chrome não cobre leitor de tela nem todos os usuários | revisão manual pt/en/teclado/leitor de tela e browsers alvo |
| Novos CRUD/M05, M2M/multiunidade/índice | controles existentes não autorizam operação futura automaticamente | reutilizar guard e avaliar cada fronteira/contrato antes de disponibilizar |

Não executados: produção/TLS/ingress real, carga/pentest, destino durable/expurgo/
backups/recuperação, browsers além do Chrome e auditoria manual de acessibilidade.
Cookies Secure/HSTS/configuração produção têm testes offline, não ensaio TLS real.
RP logout alcança provedor e revoga sessão local, mas não confirma logout global
de todas as sessões do usuário. Fluxos de assinatura inválida/timeout/cache dependem
também de simuladores determinísticos; não chamar todo caso negativo de Keycloak real.

## Arquivos e estado final

Encerramento documentado: **2026-10-14 14:00:19 America/Manaus (18:00:19 UTC)**.
Branch inicial/final main; SHA inicial/final
`cec0be2acaef2af724c7fbf6785306df7e4c2a06`. Status inicial limpo, nenhum arquivo do
usuário sobrescrito. Status final: 12 arquivos rastreados modificados e 3 novos,
todos não staged. Diff rastreado: 286 inserções/9 remoções; stat não inclui os
novos arquivos. `git diff --check` aprovado; `git diff --cached --stat` vazio.

| Arquivo | Finalidade |
| --- | --- |
| apps/web/src/server/auth/service.ts | rejeitar URI incompatível antes do consumo/troca |
| apps/web/tests/auth.test.ts | callback URI/incompletude/persistência e não replay |
| apps/web/tests/browser.ts | percursos reais pt/en/admin, CSP, negação/logout/expiração/indisponibilidade |
| apps/web/tests/keycloak.real.ts | integrar Chrome/roles/expiração/pausa por ownership e correlação BFF/API |
| tests/api/identity/test_identity.py | matriz adicional de claims JWT assinadas |
| tests/integration/keycloak_harness.py | CookieJar restrito ao ensaio loopback opt-in |
| tests/integration/test_keycloak_oidc.py | cinco casos da exceção restrita de cookies |
| scripts/verify-m04-integration.py (novo) | runner real isolado sem reutilizar bancos/volumes |
| scripts/check.sh | Ruff do runner, sem serviços adicionais no gate |
| scripts/commands.md | comando opt-in de homologação |
| docs/architecture/identity-m04-09-verification.md (novo) | diagnóstico, resultados, falhas, matriz e riscos desta sessão |
| docs/architecture/identity-m04-09-homologation.md (novo) | preparação/comandos/checklists/isolamento/encerramento |
| docs/architecture/identity-verification.md | ponte para sucessor, relato histórico preservado |
| docs/architecture/identity-web.md | contrato reforçado do boundary callback |
| docs/architecture/security-m04-exit-criteria.md | avaliação atual M01–M12 separada das tabelas históricas |

next-env.d.ts foi atualizado automaticamente pelo build; suas duas referências
geradas foram repostas ao conteúdo inicial registrado, com typecheck posterior
aprovado. Não foi usado git restore/reset. Dependências, migrações históricas,
contratos M03, perfis/SHACL, dicionários pt/en e dados de trabalho não foram alterados.

Verificação final Docker: os quatro IDs de containers de trabalho acima permaneceram
iguais; nenhum container com label libris.verification ficou registrado. Os 17
volumes inventariados antes da repetição final continuam presentes, sem alteração
da lista; os ensaios usam tmpfs, sem remoção de volumes. Recursos de cada tentativa
foram encerrados no finally; Keycloak pausado foi retomado pelo harness antes do
encerramento. Os perfis Chrome temporários foram removidos pelo harness.

Nenhuma branch criada/trocada, nenhum add/commit/push/merge/rebase/pull, nenhum PR
criado/atualizado e nenhuma issue remota modificada. Nenhum banco/volume de trabalho
foi usado por testes destrutivos. Todas as mudanças permanecem exclusivamente locais.
