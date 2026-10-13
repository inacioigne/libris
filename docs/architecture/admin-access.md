# Acesso administrativo — M04.04 / #37

Implementação local de `/pt/admin` e `/en/admin`, sem editor, CRUD ou novos
endpoints. [Verificação datada](admin-access-verification.md).
Reutiliza [sessões M04.03](identity-web.md) e os ADRs
[0016](../decisions/0016-oidc-resource-server.md) e
[0030](../decisions/0030-web-oidc-sessions.md); não altera arquitetura, armazenamento
ou contratos da API. Nenhuma nova dependência, migração ou concessão foi criada.

## Sessão, identidade e guarda

`server/auth/request.ts` centraliza a leitura server-side do cookie opaco usando
`sessionCookie(service.config)` e `AuthService.identity`. Também é usado pelo painel
público existente. Configuração/banco indisponíveis produzem `unavailable`.
AuthService mantém resolução PostgreSQL cifrada, lock, refresh, expiração e
GET `/api/v1/identity/me` com Bearer server-side. Não encaminha cookies ou headers
do navegador à API. A identidade retornada contém apenas actor_id, roles e permissions.

`server/admin/access.ts` adapta o resultado em união discriminada `AdminAccess`.
`guardAdminContent` aguarda a resolução e verifica a política antes de chamar a
função que produz conteúdo protegido. Erros de resolução bloqueiam o acesso.
`admin/page.tsx` valida locale e usa essa guarda antes de criar `AdminShell`.
O frame público contém marca, idiomas e landmarks, nunca navegação por capacidades.

Não há layout como única barreira: páginas/layouts do App Router podem executar
em paralelo. Toda futura página protegida deve chamar a guarda com sua própria
exigência **antes** de consultar/renderizar seus dados. Estar no shell ou aparecer
na navegação não autoriza uma operação. O backend continua responsável pela
autorização definitiva por operação/recurso; #38/#39 e M05 permanecem separados.

## Política de entrada

A [matriz normativa](security-access-matrix.md) distingue as duas capacidades de
leitura do reader das capacidades administrativas. O shell exige **pelo menos uma**
das 15 permissões atuais abaixo, explicitadas em `administrativePermissions`:

- bibliographic:create, bibliographic:update, bibliographic:delete;
- authority:manage;
- metadata_revision:read, metadata_revision:create, metadata_audit:read;
- editorial:submit, editorial:approve, editorial:return, editorial:publish,
  editorial:withdraw, editorial:republish, editorial:archive;
- system:admin.

Leitura de revisões/auditoria é capacidade administrativa de histórico restrito
na matriz, embora não seja escrita. bibliographic:read e authority:read, sozinhas
ou combinadas, não autorizam o shell. Permissões desconhecidas não concedem nada.
O teste compara essa lista ao enum backend, excluindo as duas leituras gerais;
uma futura extensão precisa de revisão explícita, sem inclusão automática na UI.

Os papéis nunca entram na avaliação web. Não há mapa role → permission, parsing
JWT, estado de browser nem bypass por system:admin. Esta permissão sozinha habilita
somente a informação de administração do sistema. Identidade com permissão
insuficiente continua autenticada e mantém sessão/CSRF; não ocorre revogação.

## Navegação por capacidades

`navigation.ts` define requisitos tipados com `mode: all | any`. Uma exigência
vazia falha nos dois modos. `adminNavigation` filtra no servidor as permissões
efetivas já resolvidas pela API, em ordem fixa:

| Seção | Requisito (qualquer uma) |
| --- | --- |
| Catalogação | bibliographic:create/update/delete, metadata_revision:create |
| Autoridades | authority:manage |
| Revisões e auditoria | metadata_revision:read, metadata_audit:read |
| Fluxo editorial | qualquer uma das sete permissões editorial existentes |
| Administração do sistema | system:admin |

`AdminNavigationItem` descreve id, label traduzido, href e requisito. Os links
apontam para âncoras informativas existentes na própria página. Cada seção informa
expressamente que a interface operacional ainda não está disponível; não há links
para CRUD fictício. Os descritores apresentam capacidades e não concedem direitos.
`AdminNavigation` e `AdminShell` são Server Components; não recebem tokens/sessão
completa nem enviam objetos de autenticação a componentes client-side.

## Estados de acesso

| Resultado de identidade | Estado da guarda | Comportamento |
| --- | --- | --- |
| anonymous | login_required | formulário POST do login existente, retorno ao admin no mesmo locale |
| expired | session_expired | nova autenticação; sem chamada API com token expirado |
| authenticated sem requisito | access_denied / insufficient_permissions | contexto mínimo actor_id, retorno público e logout; sessão preservada |
| forbidden (API 403) | access_denied / api_forbidden | mensagem distinta, sem fabricar identidade; logout se CSRF resolvido |
| unavailable ou exceção | service_unavailable | tentativa por novo GET na rota canônica; sem fallback para login/anônimo ou acesso |
| authenticated com requisito | authorized | shell, contexto mínimo e navegação filtrada |

Todos os estados usam o catálogo `i18n/messages.ts` em pt/en, um h1, região main,
mensagem textual role=status, links/botões nativos e foco visível. Há skip link,
idiomas preservando `/admin`, `aria-current` na visão geral e idioma ativo,
seções com títulos hierárquicos e layout de uma/duas colunas conforme largura.
Feedback `auth=error/cancelled` só seleciona mensagens fixas; não altera acesso.

## Retorno, privacidade e cache

`returnPath` aceita exatamente `/pt`, `/en`, `/pt/admin`, `/en/admin`, com query
normal compatível. Rejeita qualquer outro caminho, barras finais, destinos externos,
protocol-relative, backslashes, controles literais/codificados, fragmentos,
dot segments, separadores codificados e dupla codificação. O retorno é validado
no login e cifrado na transação OIDC existente; o callback usa essa transação
consumida, nunca query de destino do browser. Logout administrativo retorna à
página pública no mesmo idioma, preservando URIs de pós-logout registradas.

POST login mantém Origin/Host; logout mantém Origin/Host e CSRF vinculado à sessão.
Nenhuma operação mutável nova. O CSRF necessário ao formulário permanece o do
mecanismo existente; access/refresh/ID token, subject, state, nonce e verifier
não são renderizados no shell/estados. Logging ativo de destino/transação/erro
no login foi removido; trechos de debug comentados também. Logs operacionais
seguros do Resource Server foram preservados.

`force-dynamic` impede prerender/cache de conteúdo administrativo.
`next.config.ts` aplica Cache-Control: no-store, private; Pragma: no-cache;
Referrer-Policy: no-referrer aos caminhos administrativos, incluindo filhos
inexistentes. Next pode acrescentar diretivas privadas no Cache-Control;
os testes verificam a semântica no-store/private em respostas HTML/RSC reais.
Handlers OIDC preservam os mesmos controles em redirects/rejeições.
Proxies devem respeitar esses headers e excluir credenciais/queries OIDC dos logs.

## Testes e validação manual

`admin.test.ts`: políticas, conjuntos de permissões, all/any, desconhecidas,
ausência de bypass, enum backend, estados, função protegida não invocada,
AuthService com doubles de transporte/storage, sessão preservada, callback/retorno
pt/en, negativos de redirect e ausência de logging. Inclui contraste calculado
para texto/foco base; não é auditoria visual completa de todos os elementos.

`http.e2e.ts`: Next construído, PostgreSQL real exclusivo, OIDC/API simulados;
HTML, rotas, cookies falsos, query/header forjados, negação/expiração/403/503/banco,
navegação pt/en, login admin/retorno, logout/CSRF, cache/headers, landmarks/títulos
e ausência de tokens em HTML/logs. `admin-api.e2e.ts`: Next e FastAPI reais,
sessões cifradas PostgreSQL semeadas pelo harness, access tokens RS256/JWKS efêmeros
e emissor simulado; prova de permissões calculadas pelo backend para seis papéis
e papel desconhecido. Não simula login nem homologa Keycloak real; o primeiro
harness testa o fluxo de login. `store.integration.ts` preserva regressão M04.03.

```bash
cd apps/web
npm test
npm run typecheck
npm run build
# URLs privadas de três bancos exclusivos inicialmente vazios:
TEST_WEB_ISOLATED=1 TEST_WEB_DATABASE_URL="$DISPOSABLE_STORE_URL" npm run test:integration
TEST_WEB_ISOLATED=1 TEST_WEB_HTTP_DATABASE_URL="$DISPOSABLE_HTTP_URL" \
  TEST_ADMIN_API_DATABASE_URL="$DISPOSABLE_API_URL" npm run test:http
cd ../..
bash scripts/check.sh
```

Sem URLs opcionais, os testes pulam explicitamente. Não apontar para bancos de
trabalho; migrações são explícitas somente nos bancos do harness. O ensaio com
FastAPI exige Python/uvicorn instalados em `apps/api/.venv`.

Roteiro manual pendente: acessar ambos os idiomas nos quatro estados e autorizado;
Tab/Shift+Tab, Enter/Space em formulários; skip link e foco no main/âncoras;
landmarks/títulos/nomes com leitor de tela; foco após login/logout/retry;
zoom 200%/400%, 320 px e tela larga, sem rolagem horizontal; contraste de todos os
textos/controles e mensagens. Repetir em navegador com Keycloak isolado, HTTPS e
proxy de implantação. Presença de ARIA/testes HTTP não comprova essas etapas.

Sem homologação de navegador, produção, auditoria de segurança #41, autorização
contextual #38/#39 ou editor M07. Relatórios M04.01–M04.03 permanecem históricos.
