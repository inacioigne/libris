# Verificação HTTP — M04.07 / issue #40

Data: **2026-10-14**, America/Manaus. Branch inicial/final: **main**.
HEAD inicial: `20b8bd6145390422c93a6a07f2eae26358668ba6`.
Working tree inicialmente limpo (`git status --short` vazio). Lidos branch, status,
log dos dez commits e rev-parse antes das edições. Checkout local é a referência;
nenhum pull/fetch ou alteração de histórico. HEAD coincide com a referência do pedido;
atraso frente a novos commits remotos não foi medido. GitHub consultado somente
para leitura: #40 aberta/M04, #36 fechada/M04, #41 e #42 abertas/M04. Dependência
#36 comprovada por código, testes e novas execuções, sem inferência pela issue.

## Diagnóstico inicial das fronteiras

| Categoria | Achado antes das alterações | Tratamento |
| --- | --- | --- |
| Existente e adequado | API Resource Server, assinatura/issuer/aud/exp/sub/azp/typ, JWKS limitado/cache/backoff; 401 Bearer/403 Problem Details | Preservar, regressão API completa |
| Existente e adequado | BFF Code + PKCE S256, nonce/ID token assinado, state/binding por aba, consumo atômico, sessão AES-GCM PostgreSQL, cookies opacos, refresh/rotation/expiração | Reutilizar; regressão unitária/PG/HTTP/Keycloak |
| Existente e adequado | POST Origin/Host, CSRF sessão no logout, retorno canônico, timeouts HTTP/PG, no-store/referrer em handlers/admin | Reutilizar e completar |
| Existente, insuficiente | CORS allowlist aceita strings não validadas, default localhost; GET/header mínimo mas sem validação ambiente/erros externos | Validar; default vazio; política externa ASGI e preflight somente endpoints reais |
| Existente, insuficiente | Form 4096 bytes efetivos, mas excedentes devolvem 403; callback só limita code após consumo; cookies do framework colapsam duplicatas | 413, limites antecipados e header Cookie bruto |
| Existente, insuficiente | Falha de discovery apaga promise e admite novas tentativas imediatas; ausência de quota | Backoff local discovery + quota global PostgreSQL |
| Ausente | CSP nonce/hidratação, nosniff/permissions/frame/HSTS consistentes, cache explicitamente privado nas demais páginas | Proxy Next dinâmico e middleware API |
| Descoberto durante testes | no-referrer já usado em admin, inicialmente uniformizado nas demais páginas, faz Origin=null no POST nativo e bloqueia login legítimo | same-origin nos documentos; no-referrer nas rotas OIDC/API; CSRF exato preservado |
| Exigindo configuração operacional | TLS/rede/proxy confiável, IP de origem, proteção volumétrica, logs externos, limites de conexão, pool/carga e secret manager | Contrato em http-security.md e riscos abaixo |
| Fora do escopo | Pentest/homologação M04 #42, auditoria ampliada #41, CRUD M05, M2M e isolamento institucional | Não implementados nem declarados aprovados |

Inspecionados arquivos obrigatórios existentes, ADRs 0016/0030/0031/0032 e relatórios
históricos identity-web/admin-access/identity-m04-06. Relatórios anteriores não
foram sobrescritos. Browser usa sessão; BFF chama /me server-side com Bearer sem
CORS nem cookies de browser; API não autentica cookies e /health continua público.
Rotas mutáveis expostas são POST /oidc/login e /oidc/logout; callback é GET.

## Implementação efetiva e políticas

Contrato completo: [http-security.md](http-security.md). Decisão duradoura das
quotas compartilhadas: [ADR 0033](../decisions/0033-http-auth-quotas.md).

- CORS_ORIGINS default []; lista JSON exata, sem wildcard/null/userinfo/path/query/
  fragment/porta inválida/host inválido/duplicatas. HTTP só loopback/*.localhost fora
  de production; HTTPS em production. GET, Authorization/X-Request-ID mais headers
  safelisted do padrão; sem credenciais. Expor Request-ID/WWW-Authenticate. Preflight
  somente /health e /api/v1/identity/me; origens desconhecidas sem concessão CORS.
- Middleware externo à cadeia de ServerErrorMiddleware conserva CORS/headers/cache
  inclusive no 500 genérico, sem modificar Problem Details v1.
- Origin/Host POST exatos e Fetch Metadata presente somente same-origin/none;
  logout exige CSRF da sessão. Callback GET preserva protocolo, state/binding/nonce/
  PKCE/consumo único/multitab; cookies relevantes duplicados não são aceitos.
- Cookies host-only/HttpOnly/SameSite Lax, Secure/__Host-/Path=/ em HTTPS; tokens e
  transações cifrados no PostgreSQL, prazo absoluto e rotation existentes intactos.
  Redirects exclusivamente canônicos; nenhuma URL pública recebe tokens do servidor.
- CSP nonce aleatório de 32 bytes em request/response, headers recebidos sobrescritos,
  SSR dinâmico e nonce em scripts Next/React. Sem unsafe-inline/eval no build ou
  WEB_AUTH_ENV=production. next dev local tem exceções HMR explícitas. form-action
  inclui self e origem exata do issuer para redirects OIDC. Assets mantêm immutable.
- Nosniff/referrer/permissions/frame; no-store/private + Pragma para documentos,
  auth/erros/redirects; API /api/* e entrada Bearer/Cookie/erros privados. API docs
  interativas só em desenvolvimento (exceção CDN/inline restrita); /health sem
  no-store global. poweredBy removido; Server do ASGI removido, Uvicorn/proxy externo
  ainda requer configuração própria.
- HSTS sem includeSubDomains/preload: API somente APP_ENV production/scheme HTTPS;
  web somente production, Host público e WEB_HTTPS_TERMINATED=1 (afirmação de ingresso
  TLS confiável/rede fechada). Forwarded arbitrário não infere HTTPS nem IP cliente.
- Form real até 4096 bytes/oito pares/campos permitidos, prazo cinco segundos;
  callback query até 8192 bytes/oito pares, nomes 64/valores 4096; excedentes 413.
  Content-Length não determina o limite. Timeouts JWT/JWKS/provider/PG preservados;
  discovery adiciona backoff dez segundos local. Sem retry de grants/refresh incerto.
- Quota global por rota, janela fixa 60 segundos, 120 login/240 callback/240 logout;
  relógio PG, UPSERT atômico, contador saturado, três linhas no máximo. 429 com
  Retry-After limitado à janela; indisponibilidade/migração ausente → 503 sem provider.
  Configuração privada validada, igual entre réplicas; nenhuma chave/IP de header.
- Migração incremental web 0002 explícita; down somente quotas, preserva sessões/
  transações/legado. Scripts não logam texto completo de erro; runtime sem DDL.

Local: HTTP loopback autorizado explicitamente, Secure/HSTS ausentes no HTTP e CSP
sem upgrade de localhost mesmo em next start. Produção: origem/issuer/API web HTTPS,
ingresso confiável explícito; issuer API HTTPS mesmo OIDC desativado. Falha de
configuração HTTP resulta 503 privado. Compose continua somente desenvolvimento;
nenhuma credencial/realm persistido/volume de trabalho alterado. Sem dependências
novas, alterações de locks, mapas RBAC, contratos M03 ou migrações históricas.

Fontes primárias: [CSP Next.js 16.4](https://nextjs.org/docs/app/guides/content-security-policy)
e [Fetch/Origin e Referrer Policy](https://fetch.spec.whatwg.org/#append-a-request-origin-header).
O teste Chrome comprovou hidratação antes da correção de Referrer; as novas execuções
abaixo são a evidência final, não a recomendação documental sozinha.

## Execuções e resultados

Ambiente efetivo: Python 3.13.15, Node 24.16.0, Next.js 16.4.0 e Chrome
155.0.8059.39. Todas as linhas aprovadas abaixo foram executadas nesta sessão.
O gate padrão não exige serviços externos; suites opcionais foram ativadas com
ambientes privados isolados, sem skips.

| Comando/ensaio | Resultado efetivo | Evidência |
| --- | --- | --- |
| bash scripts/check.sh (final) | exit 0 | /tmp/libris-m0407-check-complete.log |
| uv run pytest (pelo gate) | 1578 passed, 476 warnings, 118,03 s; zero skips/falhas | Mesmo log; inclui 45 novos testes HTTP/configuração |
| uv run ruff check . ../../tests | All checks passed | Gate e execução estática independente |
| uv run mypy src | Success, 79 arquivos | Gate e execução independente |
| npm test | 120 passed, zero skips/falhas | Gate; 29 testes adicionais, relógio controlado e concorrência |
| npm run build | exit 0; Next 16.4/webpack, Proxy e rotas dinâmicas | Gate; build real usado no HTTP final |
| npm run typecheck | exit 0 no gate e após restaurar next-env.d.ts | Typecheck final executado separadamente |
| docker compose --env-file .env.example config --quiet | exit 0, credenciais bootstrap efêmeras só para interpolação estática | Última etapa do gate, nenhum serviço iniciado/mutado |
| TEST_WEB_ISOLATED=1 TEST_WEB_DATABASE_URL=.../persistence_retry npm run test:integration | 1 passed, zero skips, 463 ms | /tmp/libris-m0407-persistence-final.log |
| TEST_WEB_ISOLATED=1 TEST_WEB_BROWSER_ENABLED=1 TEST_WEB_HTTP_DATABASE_URL=.../http_review TEST_ADMIN_API_DATABASE_URL=.../admin_review npm run test:http | 2 passed, zero skips, 12,65 s | /tmp/libris-m0407-http-review.log |
| npm run test:keycloak, pelo runner privado com flags/URLs isoladas | 1 passed, zero skips, 21,77 s | /tmp/libris-m0407-keycloak.log |
| Auditoria de src/logs e JS público compilado | Sem logs de tokens/headers completos; keyring/URL PG/active key e tokens sintéticos ausentes dos assets públicos | rg em identity/web/scripts + leitura somente de .next/static/*.js |
| git diff --check; git diff --cached --name-only | exit 0; staging vazio | Inspeção final abaixo |

Integração PG comprova migration up/down/re-up, legado e sessões preservados,
consumo atômico/refresh/logout, ciphertext/corrupção/rollback, quotas simultâneas
entre dois pools e recuperação por avanço explícito do timestamp da janela.
Não usou sleeps para quotas nem simulou PostgreSQL com SQLite.

HTTP final comprova HTML/SSR/RSC privado, todos os scripts com nonce compatível
com CSP, nonces distintos por documento, assets 200/immutable, login/callback/replay/
logout/CSRF, shell pt/en e cadeia real /me/JWT/JWKS/RBAC. O provider é mock HTTP
assinado nesses dois ensaios; FastAPI é processo real no harness administrativo.
413, 429/Retry-After, recuperação e quota storage indisponível/503 são testados nas
rotas construídas. Fake tokens não entram em HTML, erros, headers ou logs capturados.

Chrome opt-in comprovou hidratação React, Link /en → /pt sem reload, formulário
nativo → provider simulado → callback → identidade renderizada, logout/RP redirect
e ausência de violações CSP nesses fluxos. Para a negativa CSP, HTML hostil
**parser-inserted** é servido pelo mock com a CSP exata obtida do documento Next;
script sem nonce foi bloqueado (script-src-elem), sem execução. Não se confunde
Runtime.evaluate (debugger privilegiado que pode contornar CSP) com injeção atacante.
A sonda não adiciona endpoint no produto. Isso não é um browser autenticando no
Keycloak real: o ensaio real abaixo é HTTP separado.

Keycloak 26.8 real → Next compilado → PG → FastAPI real: Code/PKCE, ID token/nonce,
Bearer validado, reader efetivo, callback/replay, refresh com rotação persistida,
CSRF cross-origin recusado, revogação local e endpoint RP alcançado sem ID token na
URL. Usuário sintético removido pelo finally; sem senha/token no output.
Não foram repetidos o harness completo M04.02 de rotação JWKS/governança #39, a
integração editorial M03 em PG ou ensaios de carga: código correspondente não mudou;
suíte padrão testa regressão M03. Não são apresentados como executados aqui.

Não executados: produção real/TLS público/proxy de implantação, carga/pentest,
Keycloak real em browser e auditoria manual de acessibilidade/múltiplos browsers.
Não há topologia/certificados de produção nem critérios de capacidade fornecidos;
essas homologações ficam pendentes operacionalmente em #42, sem extrapolar os
ensaios locais. Nenhum teste skip ou execução anterior foi contado como aprovação.

## Falhas encontradas e corrigidas durante a execução

1. Sandbox: uv snap/TestClient e processos/servidores Node restringidos. Execuções
   necessárias autorizadas pela revisão automática fora do sandbox; nenhuma rejeição
   de aprovação. Inicialmente 5 testes startup passaram fora dele; typecheck passou.
2. Primeiro Ruff encontrou ordenação de imports/linhas longas nos testes novos;
   corrigidos antes do gate final. mypy só é aprovado após execução efetiva.
3. Primeiro teste PG encontrou Retry-After=61 em algumas requisições concorrentes de
   janela 60: timestamp inicial da instrução precedia espera por lock. Corrigido com
   clock_timestamp no retorno e clamp 1..janela; nova execução em banco vazio passou.
4. Primeiro gate: 1570 passed, 1 failed (fixture preflight esperava localhost default).
   Fixture agora fornece allowlist explicitamente; sem ampliar política para passar.
5. Harness administrativo HTTP já não emitia azp nos JWT sintéticos após M04.06;
   acrescentado libris-web à fixture, preservando a validação real (sem enfraquecimento).
6. Chrome identificou POST legítimo recusado, apesar de hidratação/Link funcionais;
   confirmado efeito de no-referrer/Origin=null pela especificação. Referrer de
   documentos mudou para same-origin. Asserções RSC passaram a usar política por
   caminho, não Content-Type. Proxy seleciona no-referrer explicitamente em /oidc/*
   para impedir sua precedência de headers sobre handlers. Perfil temporário teve
   uma corrida de limpeza ENOTEMPTY; remoção restrita ao perfil usa retries limitados.
7. Uma tentativa HTTP coincidiu com o gate substituindo .next e os servidores não
   iniciaram. Corrigida a ordem: o HTTP final só começou após o gate/build terminar.
   Nenhum resultado daquela tentativa é contado como aprovado.
8. Sonda inicial de injeção via Runtime.evaluate não era válida porque CDP é
   privilegiado; substituída por HTML parser-inserted com política exata do Next.
   Asserção antiga de referrer no harness admin também atualizada para same-origin.
9. Build regenera next-env.d.ts. Conteúdo original é restaurado somente nesse arquivo
   gerado da sessão (inicialmente limpo) e typecheck final é executado depois.

Avisos históricos Starlette/httpx e RDFLib não são falhas nem foram suprimidos.

## Isolamento e riscos residuais

PostgreSQL novo `libris-m0407-postgres-isolated`, imagem postgres:17-bookworm,
ID `5f16a76a2629348cca16851edfb4b91c647a3feaea3e7ce476327652e7828288`, tmpfs em
/var/lib/postgresql/data, porta somente 127.0.0.1:32768. Trust somente nesse container
sem dados reais, temporário, acessível no loopback do host; não é configuração de
produto. Cada repetição usa novo banco inicialmente vazio. Nenhum SQLite, downgrade
ou mutação em banco/volume de trabalho.

Keycloak novo `libris-m0407-keycloak-isolated`, imagem 26.8.0,
ID `2d8356e1660254418ff230196a35dbd3f96c122a9d2326019a8b37d91be6c75c`, data tmpfs,
porta 127.0.0.1:55474. Realm derivado sem usuários, callback web 127.0.0.1:55475;
credenciais bootstrap aleatórias somente em arquivos /tmp privados (0600) e ambiente
do subprocesso. Harness cria/remove usuário sintético e altera TTL/rotation somente
nesse realm descartável. Provedor de trabalho 8081 nunca administrado.

Chrome instalado, headless com perfil /tmp único; --no-sandbox somente nesse harness
local efêmero, nunca instrução de implantação do produto. Testa provedor simulado
assinado, não Keycloak no navegador. Keycloak real é ensaiado por HTTP separadamente.
Não testa Safari/Firefox/mobile/leitor de tela, TLS público, proxy real ou produção.

Quotas globais protegem operações custosas entre réplicas, mas atacante pode
consumi-las e negar serviço; janelas fixas permitem rajada na fronteira. Ainda há
consulta PG para 429 e contenção numa linha por rota. Sem garantia de fairness,
quota individual/IP/NAT ou proteção volumétrica. Configurar proxy confiável,
limites de conexão/header/read/pool e egress; medir capacidade/carga antes de produção.
WEB_HTTPS_TERMINATED é contrato operacional, não prova automática de TLS/rede.
Logs de proxy/servidor/IdP, backups/secret manager/TLS PG, retenção/auditoria #41,
revogação residual de JWT e homologação institucional/#42 continuam pendentes.

## Critérios de aceite da #40

“Atendido” significa garantia local no nível de implementação/teste indicado,
sem homologação institucional/produção inferida.

| Requisito | Estado | Evidência verificável |
| --- | --- | --- |
| CORS restritivo/validado por ambiente | atendido | Settings, middleware, test_http_security.py/preflight/origem/401/500 |
| Cookies/sessão revisados | atendido | atributos HTTPS/host-only, uniqueCookie, auth.test, PG e Keycloak real |
| CSRF efetivo nas mutações | atendido | Origin/Host/Fetch Metadata, CSRF outra sessão, HTTP/Chrome/logout |
| State/callback contra adulteração/replay | atendido | auth.test, consumo PG, concorrência, HTTP e Keycloak real |
| Open redirects rejeitados | atendido | returnPath, negativos absoluto/protocol-relative/encoded/double, HTTP |
| Headers de segurança aplicados | atendido | API headers inclusive 500/preflight; Proxy/headers Next; HTTP |
| CSP compatível Next/OIDC | atendido | nonce SSR, Chrome hidratação/Link/login/logout; parser-inserted bloqueado |
| HSTS condicionado a produção HTTPS | parcial operacional | testes scheme ASGI/configuração/Host; TLS/proxy de produção não fornecidos |
| Respostas privadas sem cache público | atendido | /me/401/500, admin/RSC/auth/redirect, assets immutable no HTTP |
| Payload e parâmetros limitados | atendido | 413 por leitura real, CL enganoso, query bytes/count/length, HTTP |
| Timeouts explícitos | atendido | boundedFetch/AbortSignal, form deadline, PG pool/query/lock/statement; testes timeout/refresh |
| Backoff preservado | atendido | JWT/JWKS existentes, refresh compartilhado, discovery local com relógio injetado |
| Proteção contra abuso implementada/testada | atendido como quota global | UPSERT PG entre dois pools, 429/Retry-After/window/concurrency/fail closed; não é quota individual |
| 401/403 corretos | atendido | suite API/RBAC e cadeia HTTP FastAPI real, Bearer/Problem Details intactos |
| Erros do provider sem vazamento | atendido | exchange/refresh/discovery negativos, feedback genérico, quota 503, Keycloak/logs |
| Sem segredo HTML/URLs/logs/NEXT_PUBLIC | atendido no código/ensaios locais | HTML/headers/logs reais capturados, auditoria src/assets; logs externos pendentes |
| Login/logout existentes preservados | atendido | unitários/HTTP/Chrome/Keycloak real; Origin nativa corrigida |
| Testes negativos de ataques previstos | atendido | origin/cookies/CSRF/state/replay/redirect/CORS/CSP/payload/cache/429/storage/provider |
| Documentação atualizada | atendido | http-security, ADR 0033, links de identidade/baseline/README |
| Relatório independente produzido | atendido | Este arquivo, data/HEAD/estado/comandos/falhas/riscos |
| Working tree local sem commit | atendido | main/HEAD idênticos, staging vazio, inspeção abaixo |

## Arquivos alterados/criados

Criados:

- apps/api/src/libris/api/security.py: CORS restrito a endpoints e headers externos ASGI.
- tests/api/test_http_security.py: 45 casos de configuração/CORS/cache/headers/erros.
- apps/web/src/proxy.ts e src/server/http-security.ts: nonce/CSP/cache/referrer/HSTS.
- apps/web/src/server/auth/quotas.ts: decisão atômica compartilhada PostgreSQL.
- apps/web/migrations/0002_auth_quotas.up.sql e .down.sql: migração incremental isolada.
- apps/web/tests/http-security.test.ts: 29 casos adicionais de segurança/configuração/limites/falhas.
- apps/web/tests/browser.ts: sonda Chrome opt-in, perfil temporário e CDP sanitizado.
- docs/architecture/http-security.md, este relatório e docs/decisions/0033-http-auth-quotas.md.

Modificados:

- apps/api/src/libris/core/config.py e main.py: validar origens/issuer e compor middleware externo.
- tests/api/identity/test_identity.py: fixture com allowlist explícita.
- apps/web/next.config.ts e src/app/layout.tsx: headers de base e SSR dinâmico.
- apps/web/src/server/auth/config.ts: origem canônica, URL e quotas privadas validadas.
- apps/web/src/server/auth/handlers.ts, security.ts e service.ts: entrada limitada, admission,
  cookies ambíguos e Fetch Metadata, preservando CSRF e consumo único.
- apps/web/src/server/auth/request.ts: cookie bruto/duplicatas no reconhecimento SSR.
- apps/web/src/server/auth/store.ts: quotas compartilhadas e timeouts PG.
- apps/web/src/server/auth/oidc.ts: backoff local de discovery, sem replay de grants.
- apps/web/scripts/migrate.ts: seleção explícita 0001/0002 e erro sem detalhes sensíveis.
- apps/web/tests/helpers.ts, store.integration.ts, http.e2e.ts, admin-api.e2e.ts e
  keycloak.real.ts: fixtures, quotas PG, migração incremental, referrer, nonce/assets/browser.
- .env.example e docker-compose.yml: parâmetros HTTP privados, sem segredos.
- README.md e docs/architecture/identity.md, identity-web.md, security-baseline.md,
  security-m04-exit-criteria.md: links/estado atual, mantendo tabelas históricas.

Nenhuma dependência/lock ou arquivo excluído; next-env.d.ts gerado foi restaurado.
Nenhum relatório histórico de verificação foi alterado.

## Limpeza e inspeção Git final

Os dois containers exclusivos foram encerrados por docker stop com seus nomes
exatos; --rm/tmpfs removeu somente seus recursos efêmeros. Credenciais/realm derivado/
runner privados e perfis Chrome da execução removidos. Logs sanitizados permanecem
em /tmp. Inventário final confirmou os cinco serviços de trabalho ativos: libris-api-1,
libris-web-1, libris-postgres-1, libris-keycloak-1 e libris-elasticsearch-1. Sem prune,
down -v, remoção de volumes ou mutação administrativa de realm/banco de trabalho.

Branch main; HEAD final igual ao inicial:
`20b8bd6145390422c93a6a07f2eae26358668ba6`.
Nenhuma branch criada/trocada, staging, commit, push, PR, merge/rebase/reset/clean/
stash/pull ou publicação remota. Todas as alterações permanecem localmente na main.
Git diff --stat contém somente 25 arquivos já rastreados; os 12 novos constam no
status, totalizando 37 arquivos locais. git diff --check passou; nenhuma alteração staged.


```text
$ git status --short
 M .env.example
 M README.md
 M apps/api/src/libris/core/config.py
 M apps/api/src/libris/main.py
 M apps/web/next.config.ts
 M apps/web/scripts/migrate.ts
 M apps/web/src/app/layout.tsx
 M apps/web/src/server/auth/config.ts
 M apps/web/src/server/auth/handlers.ts
 M apps/web/src/server/auth/oidc.ts
 M apps/web/src/server/auth/request.ts
 M apps/web/src/server/auth/security.ts
 M apps/web/src/server/auth/service.ts
 M apps/web/src/server/auth/store.ts
 M apps/web/tests/admin-api.e2e.ts
 M apps/web/tests/helpers.ts
 M apps/web/tests/http.e2e.ts
 M apps/web/tests/keycloak.real.ts
 M apps/web/tests/store.integration.ts
 M docker-compose.yml
 M docs/architecture/identity-web.md
 M docs/architecture/identity.md
 M docs/architecture/security-baseline.md
 M docs/architecture/security-m04-exit-criteria.md
 M tests/api/identity/test_identity.py
?? apps/api/src/libris/api/security.py
?? apps/web/migrations/0002_auth_quotas.down.sql
?? apps/web/migrations/0002_auth_quotas.up.sql
?? apps/web/src/proxy.ts
?? apps/web/src/server/auth/quotas.ts
?? apps/web/src/server/http-security.ts
?? apps/web/tests/browser.ts
?? apps/web/tests/http-security.test.ts
?? docs/architecture/http-security-m04-07-verification.md
?? docs/architecture/http-security.md
?? docs/decisions/0033-http-auth-quotas.md
?? tests/api/test_http_security.py
```

```text
$ git diff --stat
 .env.example                                    | 10 +++++
 README.md                                       | 13 ++++++
 apps/api/src/libris/core/config.py              | 53 +++++++++++++++++++++---
 apps/api/src/libris/main.py                     | 31 +++++++++-----
 apps/web/next.config.ts                         |  9 +++--
 apps/web/scripts/migrate.ts                     |  7 +++-
 apps/web/src/app/layout.tsx                     |  2 +
 apps/web/src/server/auth/config.ts              | 19 ++++++++-
 apps/web/src/server/auth/handlers.ts            | 54 +++++++++++++++++++------
 apps/web/src/server/auth/oidc.ts                | 11 ++++-
 apps/web/src/server/auth/request.ts             |  6 +--
 apps/web/src/server/auth/security.ts            | 20 ++++++++-
 apps/web/src/server/auth/service.ts             |  3 +-
 apps/web/src/server/auth/store.ts               |  7 +++-
 apps/web/tests/admin-api.e2e.ts                 |  5 ++-
 apps/web/tests/helpers.ts                       | 13 ++++++
 apps/web/tests/http.e2e.ts                      | 49 ++++++++++++++++++++--
 apps/web/tests/keycloak.real.ts                 |  1 +
 apps/web/tests/store.integration.ts             | 25 ++++++++++++
 docker-compose.yml                              |  5 +++
 docs/architecture/identity-web.md               | 13 ++++++
 docs/architecture/identity.md                   | 13 ++++++
 docs/architecture/security-baseline.md          | 13 ++++++
 docs/architecture/security-m04-exit-criteria.md | 13 ++++++
 tests/api/identity/test_identity.py             |  3 +-
 25 files changed, 349 insertions(+), 49 deletions(-)
```
