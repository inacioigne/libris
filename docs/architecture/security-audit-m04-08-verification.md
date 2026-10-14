# Verificação M04.08 / #41 — auditoria de segurança

Data: **2026-10-14**, America/Manaus. Entrega exclusivamente local, branch `main`.
HEAD inicial: `428a9e30754792beaf973bccbbd16ef3365d8685`.
Estado inicial: somente `?? scripts/commands.md`, preservado sem edição.
Contrato: [security-audit.md](security-audit.md); decisão:
[ADR 0035](../decisions/0035-security-audit-emission.md).

## Diagnóstico e fontes

Antes de editar: git branch --show-current, status --short, log -12 --oneline
--decorate e rev-parse HEAD. Inspecionados commits 75c3759 (#38), 20b8bd6 (#39),
a12908c (#40), 3f03eeb (shell), ad6dbec (Compose) e HEAD 428a9e3 (Alembic web).
README, AGENTS, overview/domains, contrato catalográfico, identidade web/API,
governança, autorização, proveniência/auditoria, persistência editorial, controles
HTTP, baseline/matriz/ameaças/critérios M04 e ADRs pertinentes foram consultados.
Código e testes atuais prevalecem sobre descrições históricas.

GitHub somente leitura: #41 aberta, milestone M04; #28, #38, #39, #40 e #43 fechadas.
#28/#43 fornecem auditoria catalográfica/transações; #38 fornece guard/políticas;
#39 fornece hash e cliente humano permitido; #40 fornece HTTP, quotas e BFF seguros.
Issue fechada não substitui evidência: essas dependências foram verificadas no
checkout e por regressões, com execução física separada abaixo.
`git ls-remote origin refs/heads/main` retornou o mesmo SHA do HEAD inicial;
nenhum fetch/pull ou atualização de refs foi realizado.

| Requisito | Estado inicial | Evidência no HEAD | Implementação necessária e entregue |
| --- | --- | --- | --- |
| Rastreabilidade de autorização | ausente | AuthorizationGuard.require/POLICIES decidem sem observador | SecuritySink injetável; ação/recurso/ator/categoria; decisão preliminar |
| Eventos de autenticação | parcialmente implementado | OIDCValidator mensagens warning/debug sem envelope | IdentityService sucesso/falha, dependência Bearer e HTTP permissions; sem diferenças novas na resposta |
| Eventos de sessão | ausente | AuthService/handlers/store confirmam estado sem eventos | criação, rotação, refresh/expiração/revogação/logout e falhas; emissão posterior ao COMMIT |
| Correlação | parcialmente implementado | RequestCorrelationMiddleware + ContextVar na API; sem propagação BFF | UUID canônico limitado, duplicatas recusadas, middleware externo, Proxy/AsyncLocalStorage e BFF → API |
| Privacidade dos logs | parcialmente implementado | logs OIDC genéricos sem token, logger Problem Details omite mensagens | allowlist de campos/valores, validação runtime, captura real com sentinelas |
| Retenção e acesso | ausente | sem política de segurança específica | contrato de collector, proposta 90 dias configurável, segregação e expurgo; implantação operacional ainda pendente |
| Preservação da M03 | implementado | AuditStore/HistoryService/CAS/snapshots e editorial transacionais | preservar contratos; somente UUID propagado ao ResourceContext; testes de regressão físicos |

Nenhum conflito arquitetural impeditivo ou risco de mutação de dados de trabalho
foi encontrado. Nenhuma dependência/lock, nova tabela, endpoint ou migração criada.

## Implementação e garantias

Envelope 1.0 fechado, UTC, event UUID e correlação; atores opacos human/technical/
unknown com null legítimo. Perfil Python Pydantic frozen/extra=forbid; TypeScript
server-only com validação e chaves exatas. Ações/outcomes/razões fechados.
SecuritySink injetável e logging nativo, sem serializar request/session/exception.

Guard conserva permissões/exceções/deny-by-default e não transforma granted em
commit de escrita. Dependência HTTP registra capacidades exigidas. Falhas de token
não dependem de ator; indisponibilidade JWKS conserva 401 Bearer e é categorizada
inclusive durante backoff. Ator validado só é ligado após boundary confiável.

BFF confirma estado depois do store; array local descarta eventos de confirmação
em rollback. Sessão criada representa callback aceito efetivamente persistido.
Refresh falho e revogação descrevem fatos separados; logout confirma revogação local,
sem afirmar logout global. Quota/CSRF/callback/admin continuam protegidos no servidor.
Falhas incertas de rede são operacionais, sem repetir code/refresh ou mudar decisões.

O logger é best effort; falha do sink tem sinal fixo sem detalhes e nunca concede
acesso ou interfere na transação M03. Não há durabilidade/imutabilidade/atomicidade
com collector nem retenção automática. Política institucional e produção pendentes.

## Comandos e resultados executados

| Comando | Resultado |
| --- | --- |
| Git inicial e git ls-remote origin refs/heads/main | main, SHA registrado, remoto igual; leitura somente |
| uv run pytest ../../tests/api/identity ../../tests/api/test_audit_history.py ../../tests/api/test_editorial.py | 542 passed, 16 warnings, 21,28 s; regressão após instrumentação inicial |
| uv run pytest -c pyproject.toml ../../tests/api/identity/test_security_audit.py (primeira suíte específica) | 60 passed, 2 warnings, 4,10 s; quatro casos adicionais incluídos na suíte completa |
| uv run pytest | 1642 passed, 477 warnings, 134,84 s; sem falhas/skips |
| uv run ruff check . ../../tests | passou no diretório apps/api |
| uv run mypy src | passou, 86 arquivos fonte |
| npm test (após instrumentação inicial) | 120 passed, 0 failed/skipped |
| npm test (com primeiros casos novos) | 143 passed, 0 failed/skipped |
| npm test (com captura nativa/admin adicionais) | 148 passed, 0 failed/skipped; caso adicional de rede incluído no gate final |
| npm run build (primeira tentativa da suíte nova) | compilação passou; typecheck falhou em anotação de array de UUID no teste; corrigido |
| Alembic upgrade head com DATABASE_URL descartável | executado exclusivamente no banco libris_m0408; migrações existentes |
| TEST_DATABASE_URL descartável: pytest -c pyproject.toml test_audit_postgres.py test_authorization_postgres.py test_editorial_postgres.py | 48 passed, 201 warnings, 14,48 s; zero skips |
| TEST_DATABASE_URL descartável: pytest -c pyproject.toml test_security_audit_postgres.py | 2 passed, 2 warnings, 1,33 s; sink normal e falho preservam M03/negação |
| TEST_WEB_ISOLATED=1, TEST_WEB_DATABASE_URL descartável: npm run test:integration | 1 passed, 0 failed/skipped, 2,67 s; refresh/logout/correlação entre stores reais e privacidade |
| PATH com Node 24.16.0: bash scripts/check.sh | exit 0: 1642 testes API (126,00 s), Ruff, mypy (86 arquivos), 149 testes web, build Next.js, typecheck e Compose estático; zero falhas/skips |
| npm run build, pelo gate final | passou: Next.js 16.4.0, compilação/TypeScript/rotas/Proxy concluídos |
| npm run typecheck, pelo gate e após restauração de next-env.d.ts | passou nas duas execuções |
| git diff --check | passou |
| docker stop libris-m0408-postgres-isolated; docker ps | container exclusivo encerrado; cinco containers de trabalho continuam ativos |

As variáveis de integração apontaram explicitamente para o container novo abaixo;
nunca foram inferidas do DATABASE_URL/WEB_SESSION_DATABASE_URL de trabalho.
Não foi executado downgrade, pois nenhuma migração foi introduzida. Testes de
migração antigos, Keycloak real, navegador E2E/TLS/carga e homologação #42 não foram
reexecutados e não são inferidos do gate. Warnings preexistentes Starlette/httpx e
RDFLib não foram suprimidos nem tratados como falha.

Ocorrências e correções:

1. uv via snap não inicia no sandbox (snap-confine/AppArmor). Execuções autorizadas
   fora desse sandbox passaram; não mudou dependências ou versões para contornar.
2. Primeira execução npm test no sandbox falhou no arquivo auth.test.ts sem diagnóstico
   detalhado; repetição fora do sandbox passou. Não se atribui causa específica sem evidência.
3. Ruff da raiz usou configuração externa e aplicou estilo em testes fora do escopo.
   Restauração ampla foi recusada pelo auto-review pelo risco de sobrescrever trabalho.
   Foi demonstrado por leitura que cada arquivo afetado estava inicialmente limpo e
   correspondia **exatamente**, byte a byte, ao HEAD transformado pelo mesmo Ruff.
   Restauração condicionada a essa igualdade foi autorizada e removeu somente essas
   alterações incidentais. scripts/commands.md permaneceu intocado.
4. Um comando posterior com --fix geral foi recusado pelo auto-review antes de executar;
   substituído por --fix somente no teste novo e verificação geral sem escrita.
5. Tentativa de criação de teste usou caminho relativo ao diretório errado e não criou
   arquivo; pytest coletou zero itens. Refeito no diretório correto; não conta como aprovação.
6. Build apontou string versus tipo template literal de randomUUID no teste concorrente;
   array foi anotado string[] sem alterar comportamento funcional. Gate final repete build.
7. Build regenera next-env.d.ts; restauração pontual ao conteúdo inicial feita e typecheck final
   passou, sem restaurar arquivos de trabalho do usuário.

## Isolamento PostgreSQL

Container criado exclusivamente para esta entrega:
`libris-m0408-postgres-isolated`, ID
`d68b49c1d3921b7cc178a7d46252dd980c588ddbf03ba34fd927250e8f542230`,
imagem local `postgres:17-bookworm`, tmpfs `/var/lib/postgresql/data`, `--rm`,
porta **127.0.0.1:32768**. Trust restrito a esse container de dados sintéticos;
não é configuração de produção. pg_isready confirmou prontidão.

Banco novo libris_m0408: Alembic existente e regressão API. Segundo banco inicialmente
vazio libris_m0408_web: integração BFF, que também aplica Alembic explicitamente.
Não usou SQLite ou volume compartilhado. Containers de trabalho observados:
libris-api-1, libris-web-1, libris-postgres-1, libris-keycloak-1, libris-elasticsearch-1.
Limpeza final encerrou apenas o container exclusivo pelo nome exato, sem prune,
remoção de volumes, migrations/DDL ou administração do realm de trabalho.

## Critérios de aceite

“Atendido” refere-se ao código e evidência local indicada; não equivale a aprovação
institucional/produção. A emissão observacional é o escopo implementado da #41.

| Critério #41 / missão | Estado | Evidência |
| --- | --- | --- |
| Ator/ação/resultado nas operações sensíveis e logs sem segredos | atendido localmente | API identity/guard, BFF sessão/admin/quota; captura real JSON e sentinelas nos testes novos |
| Falhas de autenticação sem identidade fictícia | atendido | missing/malformed/JWT/cliente/JWKS/callback: actor null; HTTP genérico preservado |
| Não reimplementa histórico nem altera semântica #28 | atendido | nenhum diff em AuditEvent/AuditStore/snapshots/migrações; regressão padrão e 50 casos PG, separados |
| Contrato estruturado, IDs e timestamps UTC | atendido | modelos/validação fechados, enum/outcome, data ingênua recusada, serialização determinística |
| Correlação segura e isolamento concorrente | atendido | duplicatas/controles/excesso, preflight/500, ContextVar/AsyncLocalStorage, Proxy e header BFF → API |
| Falha de auditoria não muda autorização/rollback | atendido | sinks falhos nos testes unitários e PG; negação preservada e M03 confirmada pela própria transação |
| 401/403, WWW-Authenticate e Problem Details v1 | atendido | testes de endpoints reais/probes e regressão identidade; /health público |
| Sessões e acesso administrativo rastreáveis | atendido no escopo observado | criação/rotação/refresh/expiração/logout/quota/admin; nenhum ID de sessão emitido; prune não fabrica eventos individuais |
| Retenção/restrição de acesso documentadas | atendido documentalmente; parcial operacional | proposta configurável no collector, menor privilégio e expurgo em security-audit.md; nenhum collector/grant/lifecycle implantado |
| Durabilidade/imutabilidade centralizada | não verificável nesta entrega | logging best effort explícito; não requerido como ledger pela issue; depende de implantação/mecanismo posterior |
| Snapshots/CAS/históricos/NULL preservados | atendido | testes M03 e PG de transações/negação/CAS; somente UUID no ResourceContext |
| Testes e documentação datada | atendido | este relatório independente e docs/ADR, sem sobrescrever relatórios históricos |
| Homologação real de produção/Keycloak/browser | não verificável | não executada nesta entrega; limites registrados |
| Working tree main, sem staging/publicação | atendido | branch/HEAD iguais, diff --check passou, diff --cached vazio; inspeção final abaixo |

## Arquivos da entrega

Novos:

- `apps/api/src/libris/modules/security_audit/`: quatro __init__.py, contrato
  domain/events.py, aplicação emission.py e adaptador infrastructure/logging.py.
- `apps/web/src/server/security-audit.ts`: contrato runtime, sink e correlação BFF.
- `tests/api/identity/test_security_audit.py`: contrato, HTTP, sink, privacidade e M03.
- `tests/integration/test_security_audit_postgres.py`: sink/negação/M03 em banco real.
- `apps/web/tests/security-audit.test.ts`: sessões, logs, concorrência, admin e quotas.
- `docs/architecture/security-audit.md`, este relatório e ADR 0035.

Modificados:

- `apps/api/src/libris/api/problems.py` e `main.py`: validação/correlação ASGI externa,
  mantendo suporte de install_problem_handlers para apps isoladas de teste.
- `identity/api/dependencies.py`, `application/service.py`,
  `application/authorization.py`: observação de autenticação e autorização.
- `identity/domain/authorization.py` e `domain/exceptions.py`: UUID opcional de
  recurso e razão fechada de recusa do cliente, sem mudar POLICIES/concessões.
- `identity/infrastructure/oidc.py`: conservar categoria de indisponibilidade no backoff.
- `bibliographic/application/service.py`, `history.py` e `editorial.py`: apenas
  propagação de UUID ao guard; nenhum novo evento catalográfico/efeito transacional.
- `apps/api/src/libris/modules/README.md`: inventário do contrato transversal novo.
- `apps/web/src/server/auth/service.ts`, `handlers.ts`, `request.ts`: eventos de
  sessão/autenticação/quotas e correlação; confirmação posterior ao COMMIT.
- `apps/web/src/server/auth/oidc.ts`: categoria operacional tipada, sem alterar retries,
  validação de tokens, comportamento de revogação ou timeout.
- `apps/web/src/server/admin/access.ts` e `http-security.ts`: negação administrativa
  observada e ID gerado pelo Proxy antes do SSR.
- `apps/web/tests/store.integration.ts`: asserções de eventos e privacidade em PG real.
- README e docs identity, identity-web, security-baseline, security-access-matrix,
  security-threat-model e security-m04-exit-criteria: links e atualização datada M04.08;
  tabelas/relatórios históricos preservados.

## Limitações e dependências operacionais

Logs podem se perder depois do commit; nenhum ledger, outbox, imutabilidade ou
atomicidade com o provedor/collector. Retenção de 90 dias é proposta configurável no
destino, não expurgo automático implementado. Segurança institucional deve aprovar
prazo, acesso, preservação de incidente e descarte; operador deve coletar streams,
monitorar perda/volume e proteger backups. system:admin não concede acesso ao collector.

Correlação é metadado, não prova criptográfica; cliente pode reutilizar UUID na API.
Login/callback não recebem vínculo persistido entre requisições. Prune não emite evento
por sessão removida; só se afirma expiração efetivamente observada pelo serviço.
Auditoria de administração de contas no Keycloak continua externa ao Libris.
Logs de Uvicorn/Next/proxy/Keycloak/Docker exigem configuração própria; o envelope
não sanitiza automaticamente esses destinos. Revogação de JWT não é instantânea.
M2M, multiunidade, APIs CRUD, testes de carga/TLS e homologação #42 permanecem separados.


## Fechamento e estado Git

Branch final main; HEAD final igual ao inicial:
`428a9e30754792beaf973bccbbd16ef3365d8685`.
Nenhum staging/commit/push/branch/worktree/tag/release/PR/publicação, merge/rebase/reset,
pull ou alteração de issue remota. next-env.d.ts gerado foi restaurado pontualmente;
scripts/commands.md preexistente permanece não rastreado e sem edição.
Todas as alterações da entrega ficam exclusivamente no working tree para revisão.

Comandos finais: git branch --show-current, git status --short, git diff --check,
git diff --stat, git diff --name-only, git diff --cached --name-only,
git log -1 --format="%h %s" e git rev-parse HEAD. Snapshot abaixo inclui este relatório
novo; git diff --stat/name-only não enumeram arquivos novos não rastreados.

A coleta/logs desta execução está em /tmp/libris-m0408-*.log, fora do versionamento;
o relatório registra resultados duráveis em documentação, sem copiar segredos.
Nenhum resultado histórico de verificação foi sobrescrito. Critérios técnicos locais
da #41 atendidos; retenção/acesso/durabilidade do collector e homologação institucional
continuam explicitamente pendentes e não são anunciados como entrega operacional integral.


```text
$ git branch --show-current
main

$ git status --short
 M README.md
 M apps/api/src/libris/api/problems.py
 M apps/api/src/libris/main.py
 M apps/api/src/libris/modules/README.md
 M apps/api/src/libris/modules/bibliographic/application/editorial.py
 M apps/api/src/libris/modules/bibliographic/application/history.py
 M apps/api/src/libris/modules/bibliographic/application/service.py
 M apps/api/src/libris/modules/identity/api/dependencies.py
 M apps/api/src/libris/modules/identity/application/authorization.py
 M apps/api/src/libris/modules/identity/application/service.py
 M apps/api/src/libris/modules/identity/domain/authorization.py
 M apps/api/src/libris/modules/identity/domain/exceptions.py
 M apps/api/src/libris/modules/identity/infrastructure/oidc.py
 M apps/web/src/server/admin/access.ts
 M apps/web/src/server/auth/handlers.ts
 M apps/web/src/server/auth/oidc.ts
 M apps/web/src/server/auth/request.ts
 M apps/web/src/server/auth/service.ts
 M apps/web/src/server/http-security.ts
 M apps/web/tests/store.integration.ts
 M docs/architecture/identity-web.md
 M docs/architecture/identity.md
 M docs/architecture/security-access-matrix.md
 M docs/architecture/security-baseline.md
 M docs/architecture/security-m04-exit-criteria.md
 M docs/architecture/security-threat-model.md
?? apps/api/src/libris/modules/security_audit/
?? apps/web/src/server/security-audit.ts
?? apps/web/tests/security-audit.test.ts
?? docs/architecture/security-audit-m04-08-verification.md
?? docs/architecture/security-audit.md
?? docs/decisions/0035-security-audit-emission.md
?? scripts/commands.md
?? tests/api/identity/test_security_audit.py
?? tests/integration/test_security_audit_postgres.py

$ git diff --check
(sem saída; exit 0)

$ git diff --stat
 README.md                                          |   6 ++
 apps/api/src/libris/api/problems.py                |  17 +++-
 apps/api/src/libris/main.py                        |   8 +-
 apps/api/src/libris/modules/README.md              |   7 ++
 .../modules/bibliographic/application/editorial.py |   8 +-
 .../modules/bibliographic/application/history.py   |  13 +--
 .../modules/bibliographic/application/service.py   |  38 +++++---
 .../libris/modules/identity/api/dependencies.py    |  40 +++++++-
 .../modules/identity/application/authorization.py  |  89 ++++++++++++++++++
 .../libris/modules/identity/application/service.py |  63 ++++++++++++-
 .../modules/identity/domain/authorization.py       |   2 +
 .../libris/modules/identity/domain/exceptions.py   |   9 ++
 .../libris/modules/identity/infrastructure/oidc.py |  10 +-
 apps/web/src/server/admin/access.ts                |  15 +++
 apps/web/src/server/auth/handlers.ts               |  36 ++++++-
 apps/web/src/server/auth/oidc.ts                   |  22 ++++-
 apps/web/src/server/auth/request.ts                |   8 +-
 apps/web/src/server/auth/service.ts                | 104 +++++++++++++++++----
 apps/web/src/server/http-security.ts               |   6 +-
 apps/web/tests/store.integration.ts                |  12 ++-
 docs/architecture/identity-web.md                  |  12 +++
 docs/architecture/identity.md                      |  12 +++
 docs/architecture/security-access-matrix.md        |  12 +++
 docs/architecture/security-baseline.md             |  12 +++
 docs/architecture/security-m04-exit-criteria.md    |  12 +++
 docs/architecture/security-threat-model.md         |  12 +++
 26 files changed, 525 insertions(+), 60 deletions(-)

$ git diff --name-only
README.md
apps/api/src/libris/api/problems.py
apps/api/src/libris/main.py
apps/api/src/libris/modules/README.md
apps/api/src/libris/modules/bibliographic/application/editorial.py
apps/api/src/libris/modules/bibliographic/application/history.py
apps/api/src/libris/modules/bibliographic/application/service.py
apps/api/src/libris/modules/identity/api/dependencies.py
apps/api/src/libris/modules/identity/application/authorization.py
apps/api/src/libris/modules/identity/application/service.py
apps/api/src/libris/modules/identity/domain/authorization.py
apps/api/src/libris/modules/identity/domain/exceptions.py
apps/api/src/libris/modules/identity/infrastructure/oidc.py
apps/web/src/server/admin/access.ts
apps/web/src/server/auth/handlers.ts
apps/web/src/server/auth/oidc.ts
apps/web/src/server/auth/request.ts
apps/web/src/server/auth/service.ts
apps/web/src/server/http-security.ts
apps/web/tests/store.integration.ts
docs/architecture/identity-web.md
docs/architecture/identity.md
docs/architecture/security-access-matrix.md
docs/architecture/security-baseline.md
docs/architecture/security-m04-exit-criteria.md
docs/architecture/security-threat-model.md

$ git diff --cached --name-only
(sem saída; exit 0)

$ git log -1 --format=%h %s
428a9e3 M04.07.1

$ git rev-parse HEAD
428a9e30754792beaf973bccbbd16ef3365d8685
```
