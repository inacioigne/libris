# Identidade web — M04.03 / issue #36

Implementação local do BFF Next.js 16, React 19, Node 24, TypeScript strict.
Decisão: [ADR 0030](../decisions/0030-web-oidc-sessions.md).
Evidências e limites: [verificação própria](identity-web-verification.md).
FastAPI continua Resource Server e único responsável pela autorização real;
nenhum contrato M03 ou endpoint da API foi alterado.

## Login, callback e chamada à API

A página /pt ou /en renderiza formulário nativo POST /oidc/login.
O servidor valida Origin/Host e destino, gera state/verifier/nonce/binding de
256 bits, cifra a transação no PostgreSQL e cria cookie de binding de cinco
minutos. Cada tentativa usa cookie próprio, permitindo abas independentes.
Descoberta confirma issuer exato, S256 e endpoints na mesma origem do issuer;
HTTP só é permitido com WEB_AUTH_ENV=local e host localhost/127.0.0.1/*.localhost.
Configuração é privada, validada sob demanda e fail closed; /pt permanece pública
com feedback genérico mesmo sem configuração válida.

`openid-client` monta Code + PKCE S256. /oidc/callback usa somente a origem e URI
configuradas; não confia em forwarded headers. Confere state, binding, duplicatas,
issuer de resposta se presente, código/erro e parâmetros permitidos. Consome a
transação atomicamente antes da troca; falha, cancelamento e replay não criam
sessão. A biblioteca valida ID token RS256 por JWKS, issuer, audience libris-web,
expiração e nonce. Somente o access token é encaminhado à API.

```mermaid
sequenceDiagram
    participant B as Navegador
    participant W as Next.js BFF
    participant P as PostgreSQL libris_web
    participant O as Provedor OIDC
    participant A as FastAPI
    B->>W: POST /oidc/login (Origin/Host, retorno /pt ou /en)
    W->>O: Descoberta confiável
    W->>P: Transação cifrada com expiração
    W-->>B: Cookie de binding HttpOnly + redirect Code/S256/state/nonce
    B->>O: Autenticação no provedor
    O-->>B: Redirect /oidc/callback?code&state
    B->>W: Callback e cookie
    W->>P: DELETE RETURNING (uso único/browser correto)
    W->>O: Troca code + verifier + redirect_uri fixo
    O-->>W: Access/ID/refresh tokens
    W->>O: JWKS e verificação de assinatura ID
    W->>P: Nova sessão cifrada; revogar ID antigo
    W-->>B: ID opaco HttpOnly + destino interno validado
    B->>W: GET /pt ou /en com ID opaco
    W->>P: FOR UPDATE da sessão
    opt Access expira em até 30 segundos
        W->>O: Refresh server-side
        O-->>W: Access/refresh rotacionados
        W->>P: Persistir tokens cifrados
    end
    W->>A: GET /api/v1/identity/me + Bearer
    A-->>W: actor_id, roles, permissions / 401 / 403
    W->>P: Commit e liberar lock
    W-->>B: HTML sem tokens (identidade retornada pela API)
```

UI apresenta somente actor_id, roles e permissions do contrato existente,
escapados pelo React. Não faz concessão de permissões nem interpreta ID token
como autorização. 401 encerra sessão; 403 mostra insuficiência mantendo logout;
falhas operacionais mostram indisponibilidade. Textos pt/en, role=status, labels,
formulários/botões nativos e foco visível preservados. Não implementa shell #37.

## Configuração e instalação explícita

| Variável privada | Uso |
| --- | --- |
| WEB_AUTH_ENV | local ou production obrigatórios; independente do NODE_ENV do build Docker |
| WEB_ORIGIN | Origem pública exata, sem caminho/query; callback derivado /oidc/callback |
| WEB_OIDC_ISSUER | Emissor exato; demo http://keycloak.localhost:8081/realms/libris |
| WEB_OIDC_CLIENT_ID | libris-web, cliente público; sem client secret |
| WEB_OIDC_SCOPES | padrão openid profile; openid obrigatório |
| WEB_SESSION_DATABASE_URL | URL pg postgresql://, distinta da sintaxe asyncpg da API |
| WEB_SESSION_KEYS | JSON de id → chave de 32 bytes em base64 |
| WEB_SESSION_ACTIVE_KEY | ID existente no keyring para novas cifras |
| WEB_SESSION_SECONDS | 60–86400, padrão 28800; expiração absoluta |
| API_INTERNAL_URL | Origem interna da API; HTTP em local, HTTPS em production |

Nenhuma variável NEXT_PUBLIC. Next local não lê automaticamente o .env da raiz:
exportar ambiente privado ou configurar apps/web/.env.local ignorado pelo Git.
Compose propaga as variáveis da raiz; URL pg deve usar host postgres na rede.
Senhas com caracteres reservados exigem codificação na URL.

Gerar chave diretamente em arquivo privado ou secret manager, sem imprimir
segredos em terminal compartilhado. Exemplo local sem chave fixa:

```bash
cd apps/web
umask 077
node -e 'require("node:fs").writeFileSync("/tmp/libris-web-keys.json",JSON.stringify({k1:require("node:crypto").randomBytes(32).toString("base64")}))'
# Exportar privadamente conexão e variáveis de origem/issuer/API conforme tabela.
export WEB_SESSION_KEYS="$(cat /tmp/libris-web-keys.json)"
export WEB_SESSION_ACTIVE_KEY=k1
npm ci
npm run session:migrate
npm run dev
```

A migração `apps/web/migrations/0001_oidc_sessions.up.sql` cria somente schema web,
duas tabelas e índices de expiração. Aplicar uma única vez por banco antes de
ativar login, com papel administrativo. A aplicação nunca migra no startup.
Arquivo down é destrutivo para sessões e transações: somente ensaiar em banco
descartável. Não executar downgrade Alembic ou modificar volume de trabalho.
Não há criação automática de usuários/papéis PostgreSQL; DBA concede acesso
mínimo ao schema a um usuário de runtime separado.

Execute `npm run session:prune` em agendamento administrativo; remove até 1000
transações e 1000 sessões expiradas por execução, sem identificadores no output.
A aplicação rejeita expiração mesmo antes da limpeza. Scripts usam ferramentas
de desenvolvimento instaladas por npm ci; execute via checkout administrativo,
não pressuponha disponibilidade de tsx na imagem standalone de runtime.

## Cookies, CSRF e retorno

Sessão: ID aleatório de 256 bits, host-only (sem Domain), HttpOnly, SameSite=Lax,
Path=/, Secure sempre em HTTPS, prefixo __Host- em HTTPS. Cookie não contém JWT
nem sessão serializada/cifrada. Reautenticação revoga sessão antiga e cria novo ID.
Em HTTPS, bindings temporários também usam __Host-/Path=/; em HTTP local,
Path=/oidc/callback. Exclusão usa os mesmos atributos e Max-Age=0.

POST login valida Origin/Host públicos exatos e rejeita Sec-Fetch-Site cross-site.
Logout exige esses checks e CSRF aleatório vinculado à sessão; SameSite sozinho
não é a defesa. Futuros handlers mutáveis devem reutilizar ambos.
Proxy deve preservar Host público e encaminhar Origin do navegador; não substituir
Host por origem interna nem confiar em X-Forwarded-* arbitrários.
Callback é GET limitado por state/binding/nonce/PKCE e uso único.

Retorno aceita somente caminhos canônicos /pt e /en, incluindo query normal.
Rejeita destino absoluto/protocol-relative, backslashes, whitespace/controles,
fragmentos, dot segments, separadores codificados e dupla codificação.
Erro/cancelamento após consumo válido mantém destino/idioma confiáveis;
sem transação confiável usa /pt com erro genérico.
Cabeçalhos de autenticação: Cache-Control=no-store, private, Pragma=no-cache,
Referrer-Policy=no-referrer. Páginas autenticadas são dinâmicas sem cache público.
Não configurar proxy para registrar query/cookies/Bearer em /oidc/*: códigos,
state e nonce fazem parte do protocolo, mas não devem entrar em logs/telemetria.

## Expiração, refresh e concorrência

Access token tem prazo de expires_in da resposta validada; renovar ao faltar
30 segundos. Refresh usa refresh_expires_in quando disponibilizado pelo Keycloak,
sem decodificar refresh token; expiração/invalid_grant encerram a sessão.
Ausência de refresh exige login quando o access deixa de servir. Prazo absoluto
da aplicação não é renovado. Refresh token rotation substitui o token armazenado.
ID token de refresh, se emitido, tem validação da biblioteca e subject deve continuar
o mesmo; ID token não é armazenado nem enviado ao browser.

FOR UPDATE permanece durante refresh e chamada API (HTTP até cinco segundos).
Workers/réplicas compartilham banco e keyring, não memória de sessão.
429/5xx definitivos mantêm sessão com backoff de dez segundos, sem chamar API
com access vencido. Erro de rede/timeout ambíguo no refresh revoga para não repetir
token possivelmente consumido. Falha do banco bloqueia autenticação/mutação.
Commit perdido após rotação pode exigir novo login; não há transação distribuída
com o provedor. Pool máximo cinco conexões/worker, timeouts de lock/SQL/pool
limitados; dimensionar banco e quotas na implantação.

## Chaves e proteção em repouso

Tokens access/refresh, subject, CSRF, verifier, nonce e retorno ficam dentro de
ciphertext AES-256-GCM. AAD liga ciphertext ao tipo/hash da linha; troca de linhas
ou adulteração falha. IV aleatório por cifra. Banco guarda hash do state/binding/ID.
ID token é descartado após validação, evitando retenção desnecessária.

Rotação: distribuir keyring contendo chave antiga e nova a todas as réplicas,
depois mudar active key em todas. Escritas/refresh usam a ativa, leituras aceitam
as antigas. Manter antigas pelo prazo máximo das sessões/transações existentes
e conforme política de backups; não há re-encryption automática de sessões frias.
Se remover/perder uma chave, as sessões correspondentes são rejeitadas/removidas
quando lidas e exigem login; backups correspondentes ficam ilegíveis. Comprometimento
exige invalidar sessões/revisar tokens no provedor, não apenas mudar active key.
Secret manager, TLS PostgreSQL e backups protegidos são responsabilidades da
implantação; cifra de coluna não protege um host BFF comprometido.

## Logout

POST /oidc/logout valida CSRF, toma lock e DELETE da sessão no banco. Commit
precede consulta ao provedor/redirecionamento. Cookie é apagado.
Se descoberta/end_session falhar, retornar ao destino local sem reativar sessão.
RP-Initiated Logout usa client_id e post_logout_redirect_uri; nunca ID token na URL.
Keycloak pode pedir confirmação para encerrar a sessão SSO. A revogação local é
imediata após requests já em andamento liberarem seu lock; não cancela operações
iniciadas antes do logout. JWTs previamente emitidos continuam válidos na API
até expiração/revogação segundo política do provedor; logout local não os revoga.

## Roteiro Keycloak real e validação manual

Reutilizar [Compose e roteiro isolado M04.02](identity-keycloak-local.md).
Não reaproveitar contas/volumes/bancos de trabalho para testes.
Prepare projeto Compose novo e arquivo .env privado, credenciais aleatórias e
portas livres; issuer registrado precisa ser idêntico em browser, web e API.
Se mudar porta pública do web, alterar WEB_ORIGIN e redirects do client de teste;
não mudar issuer para resolver DNS. Resolver keycloak.localhost em IPv4 conforme
política do host; a M04.02 documenta a diferença ::1/publicação 127.0.0.1.

1. Inicializar Keycloak 26.8.0, confirmar import de realm libris e discovery/JWKS.
   Client público libris-web: Code, PKCE S256, basic/roles/profile, sem implicit
   ou password grant. Client libris-api é audiência do access token, não ID token.
2. Registrar callback exato http://localhost:3000/oidc/callback e post-logout exatos
   http://localhost:3000/pt e /en. JSON novo já traz post.logout.redirect.uris;
   realm persistido exige atualização administrativa, import não sobrescreve.
3. Criar somente no provedor isolado usuário temporário e senha aleatória;
   atribuir client roles libris-api explicitamente; nenhum usuário/senha no Git.
4. Configurar variáveis BFF/keyring/pg privados, aplicar migration explicitamente
   no banco isolado, iniciar web. Conferir /health público e /me sem Bearer 401.
5. Visitar /en?view=original; navegar por Tab/Enter até Sign in. Efetuar login no
   Keycloak e conferir retorno/idioma, actor_id/roles/permissions da API.
   Confirmar no navegador que cookies são HttpOnly e não contêm JWTs, storage
   não recebe tokens e HTML não inclui access/refresh/ID token.
6. Reabrir callback salvo: falha genérica. Cancelar login: feedback no idioma
   original. Repetir com usuário sem papéis: nenhuma permissão inventada.
7. Reduzir lifespan de access token apenas no realm descartável e observar
   renovação server-side/rotation; expirar/revogar refresh e conferir novo login.
   Parar apenas o Keycloak de teste: falha segura e logout local continua possível
   quando a sessão é resolvível; nunca liberar acesso anônimo.
8. Sair por POST: sessão local não reutilizável. Confirmar logout no provedor se
   solicitar confirmação; visitar novamente fluxo de login para verificar SSO.
9. Registrar data/versões/resultados; remover somente usuário temporário e parar
   projeto isolado preservando volumes, conforme roteiro M04.02.

Esse roteiro por si só não comprova execução. O [relatório](identity-web-verification.md)
registra ensaio real automatizado em origem/portas isoladas e distingue as
validações restantes do navegador e do Compose canônico.

## Testes reproduzíveis

```bash
cd apps/web
npm test
npm run typecheck
npm run build
# Bancos PostgreSQL exclusivos inicialmente vazios, sem URLs/credenciais reais:
TEST_WEB_ISOLATED=1 TEST_WEB_DATABASE_URL="$DISPOSABLE_PG_URL" npm run test:integration
# Banco diferente e vazio; build prévio obrigatório. Next inicia em porta efêmera.
TEST_WEB_ISOLATED=1 TEST_WEB_HTTP_DATABASE_URL="$DISPOSABLE_HTTP_PG_URL" npm run test:http
cd ../..
bash scripts/check.sh
```

Suíte padrão: RSA efêmero + HTTP simulado e MemoryStore apenas de teste.
Persistência: PostgreSQL real, migração upgrade/downgrade/re-upgrade, legado
preservado, ciphertext, consumo concorrente, refresh/logout entre stores e rollback.
HTTP: servidor Next construído, provedor simulado com JWT assinados e API simulada,
HTML real/headers/rotas/cookies/CSRF/replay/403/logout; não é Keycloak real.
Ausência de variáveis causa skip explícito, nunca aprovação de integração.
Acessibilidade estática e formulários nativos não substituem auditoria manual
com leitor de tela/navegador. Não há garantia de produção, carga, CSP/pentest ou
homologação M04 completa.

### Harness real opcional da M04.03

`npm run test:keycloak` exige build prévio, Python/API instalados em
apps/api/.venv, realm e PostgreSQL descartáveis inicialmente vazios, e ambiente
privado. Não apontar para realm institucional/de trabalho. O harness altera
explicitamente **somente o realm descartável**: lifespan access=40 s,
revokeRefreshToken=true e max reuse=0; cria usuário sintético aleatório, atribui
reader, usa formulário Code/PKCE e remove o usuário no finally. Não é password
grant do cliente libris-web; o grant administrativo admin-cli serve exclusivamente
ao provisionamento do teste, nunca ao produto.

```bash
# Todas as variáveis de credenciais abaixo devem vir de arquivo/secret privado.
export TEST_WEB_ISOLATED=1 TEST_KEYCLOAK_WEB_ENABLED=1
export TEST_KEYCLOAK_WEB_ISSUER=http://127.0.0.1:55464/realms/libris
export TEST_KEYCLOAK_WEB_ORIGIN=http://127.0.0.1:55465
# TEST_KEYCLOAK_WEB_DATABASE_URL: banco vazio exclusivo, URL pg nativa.
# TEST_KEYCLOAK_ADMIN_USERNAME/PASSWORD: bootstrap privado da instância de teste.
cd apps/web
npm run build
npm run test:keycloak
```

Para esse exemplo, iniciar container Keycloak novo sem volumes persistentes, data
em tmpfs, porta publicada 127.0.0.1:55464 → 8081 e KC_HOSTNAME com a origem acima.
Derivar realm de `infrastructure/keycloak/libris-realm.json` em arquivo temporário
sem usuários: registrar callback http://127.0.0.1:55465/oidc/callback,
webOrigins=http://127.0.0.1:55465 e post.logout.redirect.uris com /pt##/en.
Credenciais bootstrap aleatórias via --env-file privado (modo 0600).
O harness inicia/encerra Next e FastAPI em processos próprios; API usa porta
efêmera e issuer idêntico ao BFF/provedor. Cookies do provedor ficam somente em
memória do cliente HTTP de teste; essa simulação não altera cookies do produto
e não comprova comportamento de browser real.
Startup inicial Keycloak pode demorar mais de um minuto; aguardar descoberta antes
de executar. Toda repetição exige **novo banco vazio**, sem reset de base existente.
Após testes, parar somente os containers efêmeros criados; não usar down -v/prune.
A origem de teste alternativa não substitui a configuração canônica do Compose.
