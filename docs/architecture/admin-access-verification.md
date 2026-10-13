# Verificação — M04.04 / issue #37

Data: **2026-10-13**, America/Manaus. Implementação e verificações locais.
Branch inicial/final: **main**.
HEAD inicial/final: **ad6dbec9d91a54f1fdec64e7a1aa8215a9be2570**.
Working tree inicial limpo, sem staging. Relatórios anteriores preservados.

## A. Diagnóstico inicial

Leitura de AGENTS.md, README, overview/domains, contrato catalográfico, identidade,
identidade web e seu relatório, baseline/matriz/ameaças/critérios M04 e ADRs
0016/0030, seguida de inspeção dos componentes e testes efetivos.
GitHub consultado somente para leitura: [#37](https://github.com/inacioigne/libris/issues/37)
aberta e [#36](https://github.com/inacioigne/libris/issues/36) fechada, ambas milestone
4/M04. Nenhuma alteração remota. O estado fechado da #36 não foi usado como
prova: AuthService, handlers, storage, provider, painel e harnesses foram examinados.

A M04.03 já fornecia Code/PKCE, state/binding/nonce, PostgreSQL cifrado, cookie opaco,
refresh/rotação, logout com CSRF e /identity/me server-side. IdentityResult distinguia
anonymous/expired/forbidden/unavailable. O backend tinha 17 permissões e seis papéis;
reader recebia apenas bibliographic:read/authority:read, admin recebia enum completo
por concessão explícita. Não havia shell ou guarda administrativa.

O painel já usava cookies server-side; a resolução foi extraída para request.ts
sem mudar sessão/contrato. Os doubles MemoryStore/transport e HTTP construído
permitiam extensão dos testes sem substituição da infraestrutura de autenticação.
O returnPath real aceitava caminhos arbitrários sob pt/en, embora a documentação
descrevesse somente páginas públicas. Logging ativo no login imprimia destino,
transação com dados OIDC e erros; havia também debug comentado de configuração/sessão.
Ambos os problemas foram corrigidos nos caminhos diretamente relacionados.

## B. Implementação

Shell Server Component em `/pt/admin` e `/en/admin`: marca/cabeçalho, idiomas,
main/skip link, contexto mínimo actor_id, logout nativo, navegação determinística
e seções informativas de capacidades futuras. Página pública fornece link de entrada.
Nenhum CRUD, editor, endpoint, tabela, migração, biblioteca ou lock modificado.

Guarda tipada reutilizável resolve identidade antes de invocar a função de conteúdo
protegido. Quatro estados traduzidos; 403 da API distinto de identidade autenticada
com permissões insuficientes. A última mantém identidade e sessão, sem revogação.
Exceções/indisponibilidade bloqueiam o conteúdo.

Entrada exige qualquer uma das 15 capacidades administrativas explicitadas no
[documento arquitetural](admin-access.md); leitura geral isolada é recusada.
Requisitos all/any explícitos, conjuntos vazios falham e desconhecidas não concedem
direitos. system:admin não satisfaz requisitos de outras seções. Navegação para
âncoras existentes, todas identificadas como interfaces operacionais futuras.

## C. Segurança

Nenhuma permissão inferida de roles/browser. AuthService/Resource Server existentes
continuam autoridades de sessão/identidade/permissões. O guard web controla a
renderização e não substitui autorização por operação/recurso da API futura.
Página protege seu próprio trabalho; não depende de ordem de execução de layout.

Retorno aceita somente quatro caminhos canônicos públicos/admin pt/en; negativos
de redirect/controle/codificação preservados e ampliados. Callback usa transação
OIDC existente; POST login/logout e CSRF existentes preservados. Logout retorna
à página pública para manter o pós-logout OIDC registrado.

Rotas administrativas dinâmicas; headers no-store/private, no-cache e no-referrer
verificados em HTTP real, incluindo estado bloqueado, RSC e filho inexistente.
Handlers OIDC mantêm headers em redirects/rejeições. Cookies/headers/query de
autorização forjados não afetam a identidade consultada no servidor. Tokens,
subject, verifier, nonce e state não entram no shell. CSRF é somente o necessário
ao formulário existente. Logging sensível removido; logs operacionais backend intactos.

## D. Testes e resultados executados

Node **24.16.0** da instalação NVM existente incluído no PATH. Next **16.4.0**,
Python **3.13.15**, PostgreSQL **17-bookworm**. Ferramentas/dependências existentes.
Sandbox bloqueou descritores do runner Node e socket Docker; comandos necessários
foram executados com escalonamento aprovado automaticamente. Nenhuma rejeição
da revisão automática. Nenhuma dependência nova/download de framework.

| Comando / execução | Resultado |
| --- | --- |
| git branch --show-current; git status --short; git rev-parse HEAD; git diff --check iniciais | main, HEAD acima, working tree limpo, sem erro |
| npm test no sandbox | runner bloqueado por descritores; **não contado como aprovação** |
| npm test fora do sandbox, primeira suite ampliada | **88 aprovados, 0 falhos, 0 ignorados** |
| npm run typecheck inicial | falhou por estreitamento de união em access.reason; corrigido com checagem discriminada explícita |
| npm run typecheck após correção | passou |
| npm run build após correção | passou; /[locale]/admin dinâmica |
| npm run test:integration, banco web_store exclusivo | **1 aprovado, 0 falhos, 0 ignorados**; migração/cifra/locks/refresh/logout M04.03 |
| node --conditions=react-server --import tsx --test tests/http.e2e.ts, banco web_http exclusivo | **1 aprovado, 0 falhos, 0 ignorados**; Next real, OIDC/API simulados |
| node --conditions=react-server --import tsx --test tests/admin-api.e2e.ts, banco web_api exclusivo | **1 aprovado, 0 falhos, 0 ignorados**; Next/FastAPI/PG reais, emissor/JWKS simulados |
| bash scripts/check.sh, execução final | **exit 0**; todos os comandos abaixo executados |
| uv run pytest, dentro do gate | **1260 aprovados, 0 falhos, 0 ignorados**, 465 warnings, 120,80 s |
| uv run ruff check . ../../tests, dentro do gate | passou: All checks passed |
| uv run mypy src, dentro do gate | passou: 76 arquivos |
| npm test, dentro do gate final | **91 aprovados, 0 falhos, 0 ignorados** |
| npm run build, dentro do gate final | passou, shell dinâmico e handlers OIDC preservados |
| npm run typecheck, dentro do gate final | passou |
| docker compose --env-file .env.example config --quiet, dentro do gate | passou; bootstrap efêmero do próprio script, sem iniciar serviços |
| npm run test:http final, bancos novos web_http_final/web_api_final | **2 aprovados, 0 falhos, 0 ignorados**, 3,91 s; nenhum banco reaproveitado |
| npm run typecheck após reposição do arquivo gerado | passou |
| git diff --check e git diff --cached --name-only finais | sem erros; staging vazio |

Os 91 unitários são os 53 existentes mais 38 novos. Os warnings Python são os
avisos preexistentes de Starlette/httpx e RDFLib, não falhas. O build atualiza
automaticamente next-env.d.ts entre dev/build; o conteúdo original foi reposto,
sem deixar esse arquivo gerado como alteração da entrega.

Cobertura específica: conjuntos empty/reader/cataloger/authority-manager/reviewer/
publisher/admin/combinados/desconhecidos; all/any e ausência de bypass; API enum;
guarda não chama conteúdo protegido em negativas; sessão mantida quando insuficiente;
login/retorno e callback adulterado pt/en; destinos externos/controles/dot segments/
separadores/dupla codificação recusados; logs sem dumps de auth.

HTTP final: anônimo/cookie inexistente/inválido/reader desconhecido/403/401/503/banco
indisponível; forja por cookie/query/header; rotas inválidas; HTML por capacidade;
contraste base calculado, foco CSS, main/skip/h1/h2/h3/idioma/navegação ativa;
ausência de tokens em HTML/logs; HTML/RSC sem cache público; request anônimo após
autorizado não recebe conteúdo protegido. Provedor/API simulados usam códigos e
contratos existentes; 403/5xx exercitam falhas conservadoras sem inventar endpoint.

Ensaio adicional real: sessões cifradas semeadas pelo harness, JWTs assinados por
RSA efêmero, discovery/JWKS locais simulados, FastAPI real calcula RBAC para seis
papéis/papel desconhecido; Next renderiza conforme permissões efetivas. JWT inválido
produz expiração/revogação e FastAPI parado produz indisponibilidade. O harness
não realiza login; o outro ensaio verifica login/callback/retorno. **Nenhum dos dois
é homologação real do Keycloak.** Harness Keycloak da M04.03 não foi reexecutado.
Integrações bibliográficas M03 PostgreSQL não foram reexecutadas; código API/M03 intacto.

### Isolamento e limpeza

Container exclusivo `libris-m0404-pg-20261013`, --rm, dados em tmpfs,
porta dinâmica somente em 127.0.0.1. Cinco bancos novos inicialmente vazios:
web_store, web_http, web_api, web_http_final, web_api_final. Nenhuma base, volume,
realm, usuário ou serviço de trabalho modificado. Migração up/down da suite de
storage ocorreu somente no banco exclusivo. Sem down -v, prune ou limpeza Git.
Next/FastAPI iniciados pelos harnesses e encerrados nos blocos finally.
Credenciais aleatórias em arquivos /tmp modo 0600; removidas ao final.
Container efêmero encerrado exclusivamente por docker stop do seu nome.
Logs sanitizados de comandos mantidos em /tmp/libris-m0404-*.log, fora do Git.

## E. Arquivos alterados

Criados:

- UI: apps/web/src/app/[locale]/admin/page.tsx;
  apps/web/src/server/admin/shell.tsx.
- Guardas/capacidades: apps/web/src/server/admin/access.ts e navigation.ts;
  apps/web/src/server/auth/request.ts.
- Testes: apps/web/tests/admin.test.ts e admin-api.e2e.ts.
- Documentação: docs/architecture/admin-access.md e este relatório.

Modificados:

- UI/idiomas/headers: apps/web/src/app/[locale]/page.tsx;
  apps/web/src/i18n/messages.ts; apps/web/next.config.ts.
- Reuso/segurança auth: apps/web/src/server/auth/panel.tsx, security.ts,
  handlers.ts, runtime.ts e config.ts.
- Testes HTTP: apps/web/tests/http.e2e.ts.
- Referências: README.md; docs/architecture/identity-web.md e overview.md.

## F. Critérios de aceite

| Critério | Estado | Evidência |
| --- | --- | --- |
| Shell pt/en sem CRUD/editor | Atendido | admin/page.tsx, shell.tsx; build/HTTP nos dois idiomas |
| Sessão protegida e /identity/me server-side | Atendido | request.ts, AuthService preservado, PostgreSQL + FastAPI reais |
| Anônimo/expirado sem conteúdo protegido | Atendido | guardAdminContent unitário; HTML/RSC e 401 reais |
| Autorização efetiva sem roles do browser | Atendido | access/navigation, forjas negativas HTTP, RBAC real seis papéis/desconhecido |
| Leitura pública não concede entrada; admin sem bypass | Atendido | admin.test.ts; reader bloqueado, system isolado só seção system |
| Permissão insuficiente preserva identidade/sessão | Atendido | teste serviço/guarda e HTTP; session row mantida |
| Indisponibilidade não autoriza | Atendido | resolver/API/banco simulados e FastAPI real parado |
| Navegação por permissões reutilizável | Atendido | navigation.ts, AdminNavigation; dez conjuntos unitários e HTML por capacidades |
| Login/retorno admin pt/en, redirects/CSRF | Atendido | unitários callbacks/adulteração e dois fluxos HTTP completos; suite M04.03 preservada |
| Headers privados e ausência de tokens | Atendido | HTTP HTML/RSC/erros/redirects, teste logs/source, produção server-only |
| Estados acessíveis (estrutura/i18n automática) | Atendido | landmarks/títulos/status/formulários, foco, idiomas e contraste base testados |
| Estados acessíveis (auditoria completa navegador/AT) | Pendente | roteiro manual em admin-access.md, não executado |
| Regressão padrão M03/M04 | Atendido | gate exit 0, 1260 API + 91 web, Ruff/mypy/build/typecheck/Compose |
| Integração web PostgreSQL/Next/API | Atendido | 1 storage + 2 HTTP finais, zero skips; emissor simulado explicitado |
| Keycloak/browser/produção desta entrega | Pendente | ensaio M04.03 histórico preservado; nenhuma nova homologação declarada |
| Documentação/Git/remoto preservados | Atendido | docs próprios; main/HEAD/staging abaixo; apenas consultas GitHub |

## G. Riscos e pendências

Nenhuma falha conhecida de implementação/regressão restante nas verificações
executadas. Validações operacionais futuras: navegador interativo, leitor de tela,
foco nas transições, contraste integral e responsividade/zoom; Keycloak real na
rota admin; HTTPS/proxy/cookies e segurança da implantação; carga/locks/pool.
Estas etapas não são comprovadas por testes Node/HTTP ou presença de ARIA.
Produção/M04 completa não homologada. As limitações de JWT/logout/rotação M04.03
persistem. Autorização contextual #38/#39, auditoria #41, editor/CRUD continuam fora
do escopo. Não houve alteração de configuração Keycloak para facilitar testes.

## H. Estado final do Git

Branch: **main**. HEAD inicial = HEAD final:
`ad6dbec9d91a54f1fdec64e7a1aa8215a9be2570`.
Novas branches: nenhuma. Commits criados: nenhum. Staging: vazio.
Push: nenhum. Pull Requests: nenhum. Nenhuma modificação de issue/PR/tag/ref remota.
Alterações exclusivamente no working tree local. Nenhum git add, checkout,
pull, merge, rebase, cherry-pick, reset, stash ou clean executado.
Verificações finais: branch/rev-parse/status/diff --check/diff --cached --name-only.
