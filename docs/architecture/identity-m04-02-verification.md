# Verificação — M04.02 / issue #35

Data: **2026-10-13**, America/Manaus. Branch inicial/final: **main**.
HEAD inicial/final: **f7615b34bae49a2224934a757efd5d565088c641**.
Working tree inicial limpo. Mudanças finais exclusivamente locais, sem commit.
Nenhuma branch, troca de branch, commit, push, PR, alteração de issue, atualização
remota, merge/rebase/cherry-pick, stash ou descarte de trabalho foi realizado.

## Resultado delimitado

**Integração técnica real executada e aprovada pelo harness:** Keycloak 26.8.0 →
Authorization Code + PKCE S256 → access token → API FastAPI implantada → `/me` 200.
ID token, Bearer ausente e JWT malformado receberam 401 com challenge Bearer.
Reader recebeu 403 em dependência de permissão explícita no TestClient, cataloger
recebeu 200, e reviewer/publisher somaram permissões sem conceder admin.
Rotação RSA no provedor real também passou, com relógio monotônico do cache injetado.

**Homologação de navegador neste host permanece parcial:** a descoberta/JWKS
públicos responderam usando IPv4 explícito, mas o resolver retornou `::1` e o
Compose publica em `127.0.0.1`. Não foi alterado `/etc/hosts` nem executado navegador
interativo. O harness usa a rede Docker e não depende desse resolver. Corrigir a
resolução IPv4 e verificar o navegador são passos restantes da operação local.
Sessão/login Next.js e homologação E2E de M04 continuam nas #36/#42.

## Fontes, diagnóstico e decisões

Lidos AGENTS.md, README, overview, domains, contrato catalográfico, identity e
verificação histórica, baseline/matriz/ameaças/critérios/relatório M04.01 e ADR 0016.
Inspecionados módulo identity, Settings, create_app, frontend, Compose, realm,
testes de identidade e integração. GitHub consultado apenas para leitura:
#34 fechada, #35/#36/#42 abertas, milestone 4. Estado de issue não foi usado como
prova operacional. Relatórios históricos permanecem intactos.

| Diagnóstico inicial | Estado inicial | Ação/evidência desta execução |
| --- | --- | --- |
| JWT/JWKS, issuer/audience/typ, RBAC, cache, /me, 401/403 | implementado e comprovado offline | reutilizados; cobertura das lacunas ampliada |
| Realm/overlay, PKCE e token real na API | implementado, sem validação Keycloak real | implantação isolada e harness real executados |
| Scope basic e sub no token | incorreto no realm existente | token real sem sub foi rejeitado; basic acrescentado, sem enfraquecer API |
| Reviewer/publisher no realm | ausentes; mapa interno já tinha seis papéis | provisionados explicitamente, alinhados ao mapa centralizado |
| Fluxo reproduzível sem expor credenciais | procedimento manual incompleto | harness com segredos em memória, state verificado e negações reais |
| Callback/login/sessão Next.js | ausentes, fora de #35 | preservados como responsabilidade #36 |

O problema funcional observado foi a ausência de `sub`: o JSON limitava os scopes
padrão a roles/profile. Desde Keycloak 25, o mapper de subject está no scope `basic`.
A API rejeitou corretamente esse token; não houve mudança de assinatura, issuer,
audience, tipagem de token ou autorização para fazê-lo passar.
[Referência oficial](https://www.keycloak.org/docs/26.5.7/server_admin/index.html).

Outro problema era específico do harness: Keycloak 26.8 considera `.localhost`
seguro e emite cookie Secure, enquanto o CookieJar padrão não o retorna em HTTP.
O provedor retornou HTTP 400/cookie_not_found. A compatibilidade ficou restrita aos
cookies em memória desse hostname/caminho no probe HTTP de desenvolvimento.
[Implementação oficial](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/utils/SecureContextResolver.java).
Não foi desativada segurança no Keycloak, JWT ou configuração de produto.

Nenhum ADR novo: são correções e verificação do contrato já aceito no ADR 0016.
Nenhum contrato M03, tabela, migration, transação, revisão, shape/perfil ou ator
histórico foi alterado. Não foi criado cadastro local, serviço de login, RBAC
paralelo ou rota artificial na aplicação implantada. Nenhuma dependência nova;
lockfiles mantidos. O marcador pytest não altera dependências do projeto.

## Ambiente e isolamento

Host Linux; Python local **3.13.15**, Node **24.16.0** por NVM, Docker Engine
**29.8.2**, Compose **v5.6.0**. Container API/probe usou Python **3.13.16**.
Keycloak **26.8.0**, PostgreSQL **17**, Elasticsearch **9.5.5**.
Docker/uv/build necessitaram execução fora do sandbox; autorizações foram aceitas.
Não houve rejeição da revisão automática de aprovação.

Antes do startup: main limpa, nenhum container existente; portas do overlay livres.
Volumes `libris_*` e volumes anônimos já existiam e foram preservados.
Projeto novo: **libris-m0402-20261013**, com volumes próprios:

- `libris-m0402-20261013_postgres_data`;
- `libris-m0402-20261013_elasticsearch_data`;
- `libris-m0402-20261013_keycloak_data`.

Arquivo privado gerado em `/tmp/libris-m0402-private.env`, modo **0600**, com
credenciais aleatórias; não está no Git e seus valores não constam neste relatório.
O arquivo foi mantido privado para permitir reinício do projeto persistido.
Um script auxiliar sem segredos em `/tmp/libris-m0402-sync-roles.py` atualizou
explicitamente apenas o realm isolado: adicionou reviewer/publisher e atribuiu basic
como scope Default ao client web. O roteiro versionado descreve a mesma atualização
pelo administrador. A primeira importação aconteceu antes da correção final do JSON;
a validação real usou a configuração corrigida por operações administrativas
explícitas. Não se afirma reimportação automática de realm persistido.

## Evidências executadas

Nos comandos abaixo, `C` abrevia exclusivamente o prefixo realmente usado:

```text
docker compose --env-file /tmp/libris-m0402-private.env -p libris-m0402-20261013 -f docker-compose.yml -f docker-compose.oidc.yml
```

API executada em `apps/api`; frontend em `apps/web`; demais comandos na raiz.
Node 24 foi acrescentado ao PATH nas execuções npm/check.sh. O
[roteiro reproduzível](identity-keycloak-local.md) contém comandos completos,
variáveis, provisionamento, diagnóstico e desligamento seguro, sem segredos.

### Infraestrutura e verificações de rede

| Comando/verificação executada | Esperado | Observado | Status |
| --- | --- | --- | --- |
| git branch/status/rev-parse iniciais | main limpa | main, SHA acima, status vazio | aprovado |
| docker info/ps/volume ls; ss -ltn no sandbox | inspecionar daemon/portas | acesso negado ao socket/netlink | bloqueado no sandbox |
| Mesma inspeção com permissão adequada | conhecer recursos sem modificá-los | Engine/Compose disponíveis, sem containers, volumes de trabalho presentes, portas livres | aprovado |
| `C config --quiet` antes de subir e ao encerrar | configuração válida | exit 0, sem saída | aprovado |
| `C up --build -d` | iniciar apenas projeto novo | cinco serviços iniciados; postgres/ES/API/web saudáveis | aprovado |
| `C logs --tail 25 keycloak` e inspeção posterior | startup/import | Keycloak 26.8.0 iniciou; realm libris importado, estratégia IGNORE_EXISTING | aprovado |
| `getent hosts keycloak.localhost` fora do sandbox | resolver compatível com bind | retornou ::1; publicação IPv4 somente | parcial |
| curl sem resolve + inspeção dos serviços | acesso padrão do host | conexão não validada pelo resolver IPv6; serviços ativos | parcial |
| `curl --noproxy '*' --resolve keycloak.localhost:8081:127.0.0.1 --fail --silent .../.well-known/openid-configuration` | discovery público com issuer canônico | issuer, authorization/token/JWKS URLs canônicos | aprovado com IPv4 explícito |
| Mesmo curl para `/protocol/openid-connect/certs` | JWKS público | exit 0 | aprovado |
| `C exec -T api python -c ...` com urllib/socket, sem tokens | descoberta/JWKS dentro da rede | issuer canônico, alias resolveu 172.18.0.2, JWKS HTTP 200 | aprovado |
| `curl --fail --silent http://localhost:3000/pt -o /dev/null` | frontend implantado acessível | exit 0 | aprovado |
| Navegador interativo + resolução automática | login acessível no navegador | não executado; depende de ajuste IPv4 | parcial |
| `C down` sem -v; docker ps -a; docker volume ls | desligar só teste, preservar dados | containers/rede removidos, ps vazio; volumes anteriores e três novos preservados | aprovado |

Não foram executadas migrações, downgrade, prune ou remoções de volume/banco.
A API iniciou sem fazer descoberta ou migração automática.

### Testes unitários offline

| Comando/cobertura | Esperado | Observado | Status |
| --- | --- | --- | --- |
| `uv sync --locked` | ambiente coerente com lock | exit 0; 83 pacotes resolvidos/82 instalados verificados | aprovado |
| `uv run pytest ../../tests/api/identity` | casos JWT/JWKS/RBAC/HTTP | **76 passed**, 1 warning; 25 casos adicionais à baseline | aprovado |
| `uv run pytest` via check.sh, primeira execução | regressão API sem serviços necessários | **1260 passed**, 465 warnings, 153,51 s | aprovado para testes; gate falhou depois em imports |
| `uv run pytest -c pyproject.toml ../../tests/integration/test_keycloak_oidc.py` sem ativação | PKCE/state puros e skip real explícito | **7 passed, 1 skipped**, 1 warning, 2,13 s | aprovado offline; skip não comprova provedor |
| JWT negativo também via HTTP | 401 + WWW-Authenticate Bearer sem JWT na resposta | aud ausente/incorreta, issuer, expiração, ID/typ ausente, assinatura, algoritmo e malformed rejeitados | aprovado offline |
| Papéis ausentes/desconhecidos, outros clients/realm, headers falsos | /me 200 sem permissões; rota de permissão 403 | resultados esperados, actor_id não vem de header | aprovado offline |
| Discovery/JWKS inválidos e limites | falhar sem loops/redirects | JSON inválido, formato inválido, URI ausente, >100 chaves, >1 MiB, redirect rejeitados com <=2 chamadas | aprovado offline |
| Timeout/cache expirado/falha e recuperação | sem fallback expirado e refresh contido | backoff mantido, chave nova recuperada após intervalo e antiga removida rejeitada | aprovado offline |
| key_ops incompatível e logs | rejeitar chave só sign; não registrar token/sub/email | asserções passaram | aprovado offline |
| Realm importável compatível com contrato | seis papéis do mapa, basic, PKCE/redirect exato, audience access-only, nenhum usuário | asserções passaram | aprovado offline |

Os avisos são depreciações existentes de Starlette/httpx e RDFLib/ConjunctiveGraph.
Não foram atualizadas dependências para suprimi-los. Fault injection usa RSA local,
HTTPX MockTransport e relógio injetado; não representa indisponibilidade real do
container Keycloak. Rotação simulada e real estão discriminadas abaixo.

### Integração opcional e Keycloak real

Execução real: `C run --rm --no-deps -T --user root`, com credenciais passadas pelo
ambiente privado, `TEST_KEYCLOAK_ENABLED=1`, `TEST_KEYCLOAK_ISOLATED=1`,
`TEST_KEYCLOAK_API_URL=http://api:8000`, bind mounts somente leitura de tests e
pyproject, seguida de `uv sync --locked --group dev && uv run pytest -c
/config/pyproject.toml -p no:cacheprovider -s /tests/integration/test_keycloak_oidc.py`.
**Resultado: 8 passed, 1 warning, 16,70 s**, incluindo o teste real.
O CLI direto também foi executado e passou após as correções.

| Cenário real | Esperado | Observado | Status |
| --- | --- | --- | --- |
| Descoberta/JWKS e verificação local de JWT real | assinatura RS256, iss exato, aud libris-api, exp/sub, typ Bearer | OIDCValidator real validou token | aprovado |
| Code + PKCE S256, client público web | verifier seguro/challenge SHA256/state conferido/troca bem-sucedida | token real obtido sem password grant web | aprovado |
| Verifier errado | invalid_grant/400 | HTTP 400 | aprovado |
| Authorization code reutilizado | 400 | HTTP 400 | aprovado |
| Redirect arbitrário | rejeição sem redirecionar | HTTP 400, sem Location | aprovado |
| API implantada com access token real | /me 200 | HTTP 200, roles/permissions do mapa | aprovado |
| API implantada com ID token real | 401 + Bearer | HTTP 401 + Bearer | aprovado |
| Sem token/JWT malformado | 401 + Bearer | HTTP 401 + Bearer | aprovado |
| /health sem token | 200 | HTTP 200 | aprovado |
| Reader e operação com bibliographic:create | 403, mantendo /me autorizado | 403 no TestClient com validação OIDC real; /me 200 implantado | aprovado, rota só no teste |
| Cataloger/reviewer/publisher | união de permissões, sem system:admin | 200 na permissão e união correta na API implantada | aprovado |
| Rotação RSA original → novo kid | conter refresh e recuperar nova chave | componente rsa-generated temporário; novo kid inicialmente recusado, aceito com uma atualização de JWKS após avanço de 10 s do relógio monotônico injetado | aprovado real, tempo controlado |
| Limpeza de recursos próprios | remover só usuário/componente criados | duas mensagens PASS de remoção; nenhum recurso preexistente removido | aprovado |

A rotação usou chaves/tokens/JWKS reais, mas não mediu dez segundos de espera real:
o relógio do cache foi injetado; datas JWT continuaram reais. Não comprova latência,
rotação instantânea, caches de múltiplos workers ou sessão Next.js.
401 por issuer/audience/exp/assinatura/typ adulterados, desconhecidos e falhas do
provedor têm evidência offline; não foram todos reproduzidos com tokens emitidos
pelo Keycloak. Não foi preciso guardar ou editar tokens reais para esses cenários.

Primeiras execuções reais **reprovaram**: callback HTTP 400/cookie_not_found e,
após adaptar CookieJar, AuthenticationError pela ausência de sub. O finally
removeu os usuários de cada tentativa. A correção foi seguida de execução real
aprovada; os erros não foram tratados como sucesso nem ocultados como skips.

Integração PostgreSQL foi apenas coletada sem URLs de teste, com variáveis de banco
removidas. Não foram usados os bancos recém-criados nem bases de trabalho para
validar contratos M03. Resultado: **55 skipped, 8 deselected**, 1 warning, 2,11 s; nenhuma prova de integração PostgreSQL.

### Build e verificações estáticas

| Comando executado | Esperado | Observado | Status |
| --- | --- | --- | --- |
| `npm ci` com Node 24 | instalar lock sem mudanças | 51 pacotes adicionados; exit 0 | aprovado |
| `npm run build` | compilar páginas atuais | exit 0, /pt e /en geradas | aprovado |
| `npm run typecheck` | tipos TypeScript | exit 0 | aprovado |
| `uv run ruff check . ../../tests` após corrigir imports | nenhuma infração | All checks passed, exit 0 | aprovado |
| `uv run mypy src` e adicional com harness | tipagem strict | 77 arquivos sem erros incluindo harness | aprovado |
| Primeira execução `bash scripts/check.sh` | gate completo | 1260 testes passaram; gate interrompido em dois imports I001 | reprovado, corrigido |
| Segunda execução `PATH=.../node/v24.16.0/bin:$PATH bash scripts/check.sh` | gate completo | **exit 0**: 1260 testes (160,72 s), Ruff, mypy (76 arquivos), build/typecheck e Compose passaram | aprovado |
| `git diff --check` | sem erro de whitespace | passou nas inspeções | aprovado |

## Critérios de aceite e limites

| Requisito do pedido | Situação | Evidência/limite |
| --- | --- | --- |
| Main e HEAD preservados; sem branches/commits/PRs | atendido | Git inicial/final |
| Resource Server e RBAC existentes preservados | atendido | nenhuma mudança no código de produto; ADR 0016 |
| Keycloak real inicializa e realm funciona | atendido | Compose real, import e login |
| Usuário temporário e papéis explícitos | atendido | criado no provedor; reader depois cataloger/reviewer/publisher; removido |
| Authorization Code + PKCE S256 e access token real | atendido | harness CLI/pytest reais |
| Access token real autentica /me | atendido | API implantada 200 |
| Issuer único no token/discovery/API/URL pública | atendido | mesmo valor canônico em todas as verificações |
| Conectividade automática de navegador neste host | parcial | ::1 vs bind IPv4; curl resolve funcionou; navegador não executado |
| Audience libris-api e typ Bearer assinados | atendido | OIDCValidator real e testes |
| ID token rejeitado | atendido | ID token real 401; discriminator independente offline |
| Inválidos e ausência de audience rejeitados | atendido | matriz JWT/HTTP offline; malformed real |
| Papéis insuficientes sem privilégios e 401/403 corretos | atendido | reader real 403 em teste local; /me 200; fontes não confiáveis offline |
| Rotação JWKS evidenciada | atendido com limite documentado | RSA no Keycloak, relógio de cache controlado |
| Indisponibilidade/fail closed isolados | atendido | MockTransport, TTL/backoff/recovery; sem fallback expirado |
| Suíte padrão independente do Keycloak | atendido | testpaths só API; gate padrão e skip opcional |
| Credenciais não versionadas | atendido | ambiente privado/memória, relatório sanitizado |
| Procedimentos reproduzíveis | atendido | roteiro local e comandos de suite |
| Testes/estáticas executados e falhas registradas | atendido | tabela de resultados |
| Contratos M03 preservados | atendido | diff sem código de domínio/persistência/migration |
| Volumes/bancos de trabalho preservados | atendido | inventários antes/depois, down sem -v |
| Login/sessão/logout Next.js completo | fora de #35 | #36, sem implementação parcial |
| Homologação E2E abrangente/produção | fora de #35 | #42/implantação própria; não declaradas |

Passos pendentes da operação de navegador: resolver `keycloak.localhost` para
127.0.0.1 conforme política do host, repetir descoberta sem `--resolve` e visitar
o provedor no navegador. Para sessão de produto, executar a #36. Para E2E de toda
M04, cumprir as dependências da #42. O harness HTTP não substitui esses aceites.
O ambiente de teste foi desligado; o roteiro permite subir novamente o projeto
privado ou criar projeto novo. Produção exige TLS, cookies seguros, segredos,
rede, persistência/backup e observabilidade próprios.

## Inventário final do working tree

Modificados:

- `infrastructure/keycloak/libris-realm.json`: basic e papéis reviewer/publisher;
- `apps/api/pyproject.toml`: marcador pytest keycloak opcional;
- `tests/api/identity/test_identity.py`: 25 casos adicionais de segurança/configuração;
- `docs/architecture/identity.md`: estado atual, links e troca do procedimento que imprimia verifier por harness privado;
- `README.md`: links de operação/evidências.

Novos, não rastreados:

- `tests/integration/keycloak_harness.py`: Code/PKCE, OIDC/API/RBAC/rotação reais e limpeza;
- `tests/integration/test_keycloak_oidc.py`: sete casos puros e caso real opt-in em subprocesso;
- `docs/architecture/identity-keycloak-local.md`: setup/troubleshooting/desligamento;
- `docs/architecture/identity-m04-02-verification.md`: esta evidência datada.

Auditoria final: main e HEAD preservados; `git diff --check` passou; diff completo
revisado, nove arquivos inventariados, links locais conferidos e varredura de
segredos sem ocorrências. Stat rastreado: cinco arquivos, 230 inserções e 31 remoções. O stat de arquivos rastreados não inclui os
quatro novos. Sem segredos reais, tokens, cookies, authorization codes, verifiers
ou dados pessoais de usuários no relatório. Nenhum arquivo privado adicionado ao Git.
