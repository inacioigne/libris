# Verificação — M04.03 / issue #36

Data: **2026-10-13**, America/Manaus. Branch inicial/final: **main**.
HEAD inicial/final: **61d014d65293219b28936dd4a6d76cdfb1fa6216**.
Working tree inicial limpo. Alterações somente locais, sem staging/commit.
Fontes GitHub consultadas somente para leitura: #36 aberta, #35 fechada, milestone
4/M04. A dependência #35 foi verificada pelo módulo, realm, harness e evidência
histórica efetivamente presentes; não foi presumida pelo estado da issue.

## Resultado e delimitação

BFF Code + PKCE S256, callback com state/binding/nonce e assinatura ID token,
sessão PostgreSQL cifrada, cookies opacos, refresh/rotation/expiração, cliente API,
logout local/RP, CSRF e interface pt/en implementados.

**Ensaio real aprovado:** Keycloak 26.8.0 → Next.js construído → PostgreSQL 17
→ FastAPI real /api/v1/identity/me. Refresh token rotation real com reuse=0,
callback replay rejeitado, CSRF logout rejeitado, sessão local revogada e não
reutilizável; end_session do provedor alcançado sem token na URL.
É um cliente HTTP automatizado, não navegador interativo. O RP logout pode exigir
confirmação; o harness alcançou a página/resposta do provedor, sem afirmar que
clicou na confirmação SSO. Nenhuma homologação institucional/produção declarada.

## Implementação e decisões

[Fluxo e operação](identity-web.md), [ADR 0030](../decisions/0030-web-oidc-sessions.md).
openid-client **6.8.8**, pg **8.23.1**, server-only; tsx **4.23.15** nos testes.
Node **24.16.0**, Next **16.4.0**, Python **3.13.15**, PostgreSQL **17**,
Keycloak **26.8.0**. Locks/dependências atualizados conjuntamente.

Schema libris_web independente, sem tabelas/contratos M03 alterados.
Migração web SQL explícita e teste upgrade/down/re-up em banco descartável,
não integrada ao Alembic bibliográfico. Tokens/verifier/nonce/subject/CSRF cifrados
AES-256-GCM; ID token validado e descartado. Pool/metadata públicos são process-local,
sessões/transações são compartilhadas. JWT/autorizações permanecem na API.
FOR UPDATE coordena refresh e logout; rotação externa não é transação distribuída.
Origin/Host + CSRF no logout; login POST com origem exata; callback de uso único.
__Host-/Secure em HTTPS; HTTP só explicitamente local.

## Comandos e resultados efetivamente executados

Node 24 foi incluído no PATH a partir da instalação NVM existente.
npm, Docker, pytest/uv e testes HTTP necessitaram execução fora do sandbox.
Não houve rejeição da revisão automática de aprovação.

| Comando / verificação | Resultado observado |
| --- | --- |
| git branch/status/rev-parse iniciais | main, HEAD acima, status vazio |
| npm install openid-client pg server-only; npm install -D @types/pg tsx | passaram; lock atualizado, audit sem vulnerabilidades reportadas nessa instalação |
| npm test, primeira execução no sandbox | somente arquivo reportado, não casos; **não contado como aprovação** |
| npm test fora do sandbox, suite inicial | **50 passed**, zero skips |
| npm test fora do sandbox, suite ampliada | **53 passed**, zero skips |
| npm run test:integration com TEST_WEB_ISOLATED e banco exclusivo | **1 passed**, zero skips; múltiplas verificações de migração/locks/ciphertext |
| npm run test:http com segundo banco vazio e build Next | **1 passed**, zero skips; servidor Next real, OIDC/API simulados |
| npm run test:keycloak, primeira tentativa | **falhou**: discovery não pronta no prazo de 30 s; Keycloak ainda inicializava |
| npm run test:keycloak, nova base vazia após startup | **1 passed**, zero skips; provider/API/BFF reais |
| npm run test:keycloak, nova base vazia com rotation/reuse=0 e comparação privada dos tokens | **1 passed**, zero skips; 19,27 s; refresh/access efetivamente substituídos |
| uv run pytest | **1260 passed**, 465 warnings, 137,33 s |
| uv run ruff check . ../../tests | passou |
| uv run mypy src | passou: 76 arquivos |
| npm run typecheck | passou após correções de tipos de fixtures |
| npm run build | passou; /[locale] e /oidc/* dinâmicos |
| bash scripts/check.sh, primeira execução completa | **exit 0**: 1260 API (173,49 s), Ruff/mypy, 50 web, build/typecheck, Compose |
| bash scripts/check.sh, execução final | **exit 0**: **1260 API** (182,81 s), Ruff/mypy, **53 web**, build/typecheck, Compose |
| docker compose --env-file .env.example config --quiet | passou |
| config do overlay sem bootstrap env | falhou corretamente: username/password obrigatórios ausentes |
| config do overlay com bootstrap temporário privado via ambiente | passou, sem imprimir valores |
| git diff --check | passou nas revisões |
| Busca de tokens/storage/logs no código de produto | nenhuma chamada localStorage/sessionStorage/Math.random/console; único Bearer server-side |

Avisos API: deprecações preexistentes de Starlette/httpx e RDFLib ConjunctiveGraph.
Tentativas intermediárias de typecheck detectaram incompatibilidade do corpo
CustomFetch com RequestInit e tipos das fixtures; corrigidas, execuções finais
passaram. Duas invocações npm acidentais na raiz falharam ENOENT (sem package.json);
as verificações efetivas foram reexecutadas em apps/web. gh não estava instalado;
issues foram lidas pelo conector GitHub, sem escrita. curl externo falhou DNS no
sandbox; Node 24 já instalado foi localizado e usado. Nenhum erro/skip foi
convertido em evidência positiva.

## Isolamento e recursos

Serviços de trabalho libris-web/api/postgres/keycloak/elasticsearch estavam
ativos e foram preservados. Nenhuma migração, alteração de realm, usuário,
downgrade ou limpeza foi executada sobre eles.

Containers exclusivos desta execução, ambos --rm e dados em tmpfs, sem volume
persistente novo:

- libris-m0403-pg-20261013: localhost **55463**, PostgreSQL 17;
- libris-m0403-kc-20261013: localhost **55464**, Keycloak 26.8.0.

Bancos de teste inicialmente vazios e distintos: libris_web_test,
libris_web_http_test, libris_web_keycloak_test (tentativa de startup),
libris_web_keycloak_test2 e libris_web_keycloak_rotation.
Credenciais aleatórias em arquivos /tmp privados modo 0600, não no Git.
Realm temporário derivado do JSON versionado, sem usuários predefinidos;
callback/post-logout alterados somente na cópia para porta de teste.
Usuários sintéticos com senha aleatória criados no provedor e removidos no finally.
Next usa localhost **55465** no ensaio real; FastAPI usa porta efêmera.
Sem dados pessoais reais, contas/credenciais fixas ou JWTs versionados.

Issuer real do ensaio: **http://127.0.0.1:55464/realms/libris**, exato em
descoberta, Next e FastAPI. **Não** afirmar que essa execução homologou o DNS/browser
da origem canônica **http://keycloak.localhost:8081/realms/libris**.
Overlay/realm/configuração versionados preservam essa origem canônica.
O teste de persistência cria sentinela de legado, aplica up/down/re-up e comprova
preservação; não usa SQLite nem banco de trabalho. Os testes M03 PostgreSQL
existentes não foram reexecutados nesta entrega; nenhuma tabela M03 foi modificada.

## Cobertura e matriz de aceite

| Entrega/requisito #36 e pedido | Estado | Evidência e limite |
| --- | --- | --- |
| A configuração server-only, URLs, issuer, discovery, local/HTTPS | atendido | config/oidc; negativos de discovery/config e integração real; TLS prod não homologado |
| B login Code/PKCE S256, state/nonce/verifier seguros | atendido | auth tests + Keycloak real; challenge consistente e biblioteca OIDC |
| B transação curta, browser correto, concorrência e uso único | atendido | binding por cookie, DELETE RETURNING, testes errados/expirados/replay e PG concorrente |
| C callback, ausências/duplicatas/adulteração/error/cancelamento | atendido | casos negativos; transação consumida antes da troca |
| C assinatura ID, issuer/audience/exp/nonce; code inválido | atendido | RSA assinado/mocks e assinatura real por biblioteca com non-repudiation |
| D sessão servidor, cookie ID opaco HttpOnly, Secure/SameSite | atendido | cookie tests HTTP/HTTPS, HTML HTTP real, PG cifrado; comportamento de browser HTTPS não ensaiado |
| D compartilhamento, cifra/keyring/rotação/migração explícita | atendido | PostgreSQL real, ciphertext/AAD/keys, up/down/re-up; operação de secret manager futura |
| E refresh/rotation/expiração/falhas/concorrência | atendido | casos determinísticos, PG entre stores, rotation real no Keycloak; crash entre provider/commit pode exigir login |
| F API_INTERNAL_URL e Bearer server-side /me | atendido | mock HTTP e FastAPI real; sem cookies/roles/tokens vindos do browser |
| F 401/403/falhas operacionais distintas | atendido | API/service tests, 403 HTTP Next, /me sem Bearer 401 real |
| G logout local, invalidação/cookie/CSRF/replay | atendido | DELETE commit, POST Origin/Host/CSRF, PG/HTTP/Keycloak real; JWT já emitido não revogado globalmente |
| G RP-Initiated Logout | atendido na integração; confirmação SSO não verificada | URL client_id/post_logout sem ID token; provedor real retornou resposta de logout; confirmação depende do usuário |
| H interface mínima pt/en, feedback/retorno/idioma | atendido | catálogo, nativos, callbacks confiáveis e retorno /en?view=original real |
| H acessibilidade por teclado/leitor de tela | parcial | HTML semântico/form/button/foco/role=status e inspeção estática; navegador/AT manual pendentes |
| I CSRF/open redirect/replay/fail closed/no-store/sem tokens | atendido | casos negativos, limites HTTP, HTML/logs reais sem tokens; proxy/pentest prod separados |
| J testes positivos/negativos e persistência real isolada | atendido | 53 unitários + PG + HTTP + Keycloak opcionais; sem skip nas execuções ativadas |
| /health e contratos API/M03 preservados | atendido na regressão padrão | 1260 API, /health real, código API/M03 intacto; integração M03 PG não reexecutada |
| K procedimento/Keycloak real | parcial operacionalmente | harness real aprovado em origem alternativa, roteiro canônico; navegador/DNS/HTTPS canônicos pendentes |
| L documentação técnica/ADR/relatório histórico preservado | atendido | identity-web/ADR 0030/este relatório, adendos de segurança; relatórios anteriores intactos |
| Git main/sem branch/commit/push/PR/remoto | atendido | HEAD/status final; nenhuma operação Git de escrita utilizada |

## Riscos residuais e validação restante

Navegador interativo, leitor de tela, HTTPS/proxy/cookies na implantação específica,
DNS keycloak.localhost do host, confirmação SSO no Keycloak, carga/pool/locks,
quotas globais, secret manager/TLS PG/backups, CSP/pentest e segurança M04 abrangente
não são comprovados pelo build/harness. Logout local não cancela requests já em
andamento nem revoga JWTs globalmente. Provedor/banco indisponíveis bloqueiam
operações autenticadas; chave perdida exige login. Não há auditoria de segurança
#41 nem shell #37. A infraestrutura Compose segue exclusivamente local.

## Arquivos alterados

Modificados: .env.example; README.md; apps/web/package.json e package-lock.json;
apps/web/src/app/[locale]/page.tsx; apps/web/src/i18n/messages.ts;
docker-compose.yml e docker-compose.oidc.yml; infrastructure/keycloak/libris-realm.json;
scripts/check.sh; docs/architecture/identity.md, overview.md, security-baseline.md,
security-threat-model.md, security-access-matrix.md e security-m04-exit-criteria.md.

Criados:

- apps/web/src/server/auth/config.ts, security.ts, crypto.ts: configuração,
  cookies/CSRF/retorno e cifra;
- apps/web/src/server/auth/store.ts, oidc.ts, service.ts, runtime.ts, handlers.ts:
  PostgreSQL, OIDC, casos de uso, pool e adaptadores HTTP;
- apps/web/src/server/auth/panel.tsx: interface server-side mínima;
- apps/web/src/app/oidc/login/route.ts, callback/route.ts, logout/route.ts;
- apps/web/migrations/0001_oidc_sessions.up.sql e .down.sql;
- apps/web/scripts/migrate.ts e prune.ts: comandos administrativos explícitos;
- apps/web/tests/helpers.ts, auth.test.ts, store.integration.ts, http.e2e.ts,
  keycloak.real.ts;
- docs/architecture/identity-web.md e identity-web-verification.md;
- docs/decisions/0030-web-oidc-sessions.md.

Nenhum arquivo excluído. Nenhuma dependência API, lock Python, perfil, shape,
snapshot, revisão, ator histórico, contrato catalográfico ou migração M03 alterado.

## Estado final do Git e limpeza

Main e HEAD inicial preservados. Nenhuma branch criada/trocada, staging,
commit, push, PR, tag, stash, merge/rebase/cherry-pick/reset ou alteração remota.
Os arquivos permanecem modificados/não rastreados para revisão local.
Containers exclusivos de M04.03 encerrados com docker stop; --rm/tmpfs eliminou
somente seus recursos efêmeros. Inventário posterior confirmou os cinco serviços
libris de trabalho ainda ativos. Nenhuma remoção de volume, down -v ou prune.
Arquivos privados temporários de credenciais/realm de M04.03 foram removidos;
logs sanitizados do gate mantidos em /tmp, fora do Git.

git diff --check passou. Diff rastreado: 16 arquivos, 889 inserções e 14 remoções;
git diff --stat não inclui os 24 arquivos novos. Total: 40 arquivos locais.
git diff --cached --name-only vazio, sem staging.

Resultado final de git status --short:

```text
 M .env.example
 M README.md
 M apps/web/package-lock.json
 M apps/web/package.json
 M apps/web/src/app/[locale]/page.tsx
 M apps/web/src/i18n/messages.ts
 M docker-compose.oidc.yml
 M docker-compose.yml
 M docs/architecture/identity.md
 M docs/architecture/overview.md
 M docs/architecture/security-access-matrix.md
 M docs/architecture/security-baseline.md
 M docs/architecture/security-m04-exit-criteria.md
 M docs/architecture/security-threat-model.md
 M infrastructure/keycloak/libris-realm.json
 M scripts/check.sh
?? apps/web/migrations/
?? apps/web/scripts/
?? apps/web/src/app/oidc/
?? apps/web/src/server/
?? apps/web/tests/
?? docs/architecture/identity-web-verification.md
?? docs/architecture/identity-web.md
?? docs/decisions/0030-web-oidc-sessions.md
```

