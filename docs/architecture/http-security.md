# Segurança HTTP — M04.07 / #40

Contrato local e diferenças de implantação. Evidências da execução em
[http-security-m04-07-verification.md](http-security-m04-07-verification.md).
Decisão de quotas: [ADR 0033](../decisions/0033-http-auth-quotas.md).
Mantidos Resource Server (ADR 0016), BFF/sessões (ADR 0030), RBAC (ADR 0031) e
fronteira humana (ADR 0032). Nenhum contrato bibliográfico ou API CRUD foi alterado.

## Fronteiras e CORS

Browser → Next.js usa cookie opaco; Next.js → FastAPI usa Bearer server-side e não
precisa de CORS. API não autentica por cookies. CORS_ORIGINS é uma lista JSON:
default vazio, nega todas as origens de browser; [] é recomendado quando só há BFF.
O exemplo local mantém http://localhost:3000 para chamadas diretas explicitamente
permitidas. HTTP somente para localhost, 127.0.0.1, ::1 e *.localhost fora de
production. Produção aceita somente HTTPS. Rejeitados wildcard (inclusive sem
credenciais), null, userinfo, path/barra final, query/fragment, portas inválidas,
whitespace/controles, backslash, hostname inválido e duplicatas.

GET somente; headers Authorization/X-Request-ID mais os safelisted do padrão CORS
(Accept, Accept-Language, Content-Language, Content-Type). Expostos X-Request-ID e
WWW-Authenticate. Sem allow_credentials/cookies. Preflight somente em /health e
/api/v1/identity/me; métodos/headers/origens indevidos são recusados. Erros 401/403/500
seguem a mesma política externa à cadeia ASGI de erros. CORS não autoriza operações
nem impede clientes fora de um browser. Nenhum método futuro é antecipado.

## CSRF, cookies e callback

Reutilizados Origin/Host exatos nos POST login/logout; Fetch Metadata presente
aceita somente same-origin ou none, com Origin/Host ainda obrigatórios. Ausência
não dispensa Origin/Host. Logout exige CSRF aleatório da sessão, comparado em tempo
constante. API Bearer não usa sessão/cookies; não acrescentar CSRF ao Resource Server.

Binding separado por aba/tentativa, state/verifier/nonce imprevisíveis, PKCE S256,
ID token validado por biblioteca, DELETE RETURNING atômico antes da troca, replay
recusado. GET callback não exige Origin nem token CSRF convencional. Duplicatas
state/code continuam recusadas após consumo confiável; entradas excessivas são
recusadas antes de operações de banco/provedor. Cookies relevantes duplicados
no header bruto não são aceitos: a API de cookies do framework colapsa duplicatas.
A mesma regra aplica-se ao reconhecimento de sessão em SSR.

Cookies host-only, HttpOnly, SameSite=Lax; Secure e __Host-/Path=/ em HTTPS.
HTTP local mantém binding em /oidc/callback. IDs opacos; tokens cifrados no servidor;
expiração absoluta/refresh/rotação/revogação existentes preservados. Retornos aceitam
somente /pt, /en, /pt/admin e /en/admin canônicos, com queries normais; rejeitados
URLs externas, protocol-relative, controles, backslashes, dot segments, separadores
codificados e codificação dupla. Origem pública/redirect_uri nunca vem de Forwarded.

## CSP, headers e cache

Next.js 16.4: Proxy gera 32 bytes aleatórios por requisição, substitui CSP/x-nonce
vindos do cliente e passa o mesmo nonce ao SSR e à resposta. Root layout dinâmico;
scripts do framework/hidratação recebem nonce automaticamente. Produção e build
local: script-src self + nonce + strict-dynamic, sem unsafe-inline/unsafe-eval;
style-src self + nonce. CSS público self; img self/data, fontes self; connect self;
object/base none; frame-ancestors none. form-action permite self e somente a origem
do issuer configurado, pois browsers podem verificar destinos de redirects de
formulários POST para login/logout OIDC. Não libera todos os hosts do provedor.

next dev permite unsafe-eval para depuração React, estilos inline para HMR e ws/wss;
essas exceções não estão no build de produção, inclusive quando WEB_AUTH_ENV=local.
upgrade-insecure-requests somente com WEB_AUTH_ENV=production. Nonce público não é
credencial, não é persistido. Sem PPR/ISR para documentos com nonce. Assets
/_next/static e /_next/image são excluídos do Proxy e mantêm cache próprio; headers
nosniff/referrer/permissions/frame também são definidos em next.config para assets.

API JSON: default-src none, frame-ancestors/base none. Docs interativas desabilitadas
em APP_ENV=production; em desenvolvimento a UI padrão FastAPI recebe exceção CDN
jsdelivr/scripts e estilos inline, restrita a /docs e /redoc. Nenhuma exceção dessa
UI alcança a API JSON ou o frontend.

Nosniff, Referrer-Policy=same-origin nos documentos web (no-referrer em rotas OIDC/API), Permissions-Policy sem câmera/microfone/localização,
X-Frame-Options=DENY. Next desativa poweredByHeader; API remove Server na fronteira
ASGI, mas Uvicorn/proxy podem inserir novamente: configurar --no-server-header/proxy.

Referrer-Policy=same-origin nos documentos web conserva Origin real em POST de
formulários nativos e suprime Referer externo. no-referrer no documento tornava
Origin=null nesses POST no Chrome, recusados pelo CSRF; identificado no ensaio real
e corrigido sem aceitar null Origin. Rotas OIDC e API mantêm no-referrer; redirects
OIDC não carregam Referer com código/state para fora. Ver [Fetch Standard](https://fetch.spec.whatwg.org/#append-a-request-origin-header)
e [suporte CSP Next.js](https://nextjs.org/docs/app/guides/content-security-policy).

Next documentos/rotas/erros/redirects: no-store/private + Pragma=no-cache, inclusive
páginas de login públicas que podem conter identidade/CSRF. API /api/*, respostas
com entrada Authorization/Cookie e erros: mesma política, sem alterar Problem Details.
/health público não recebe no-store global; assets imutáveis não perdem cache.

## HTTPS confiável e configuração

API APP_ENV=production exige issuer HTTPS mesmo com OIDC desativado; CORS HTTPS.
HSTS max-age=31536000 somente com produção e scheme ASGI=https. X-Forwarded-Proto
não é interpretado pelo middleware. Servidor ASGI pode tratar proxy headers apenas
se a origem do proxy for explicitamente confiável e ele sanitizar esses headers.

Web WEB_AUTH_ENV obrigatório local/production e WEB_ORIGIN exatamente canônica.
Production exige WEB_ORIGIN/issuer/API_INTERNAL_URL HTTPS e WEB_HTTPS_TERMINATED=1.
Este último é uma afirmação operacional explícita: proxy TLS é o único ingresso
público e preserva Host; rede impede acesso público ao servidor HTTP interno.
HSTS só é emitido com essa configuração e Host público exato; não usa URL/forwarded
arbitrários para inferir TLS. Não inclui includeSubDomains/preload. Não anunciar
produção segura só por definir a variável; validar proxy/TLS/rede separadamente.
Ausência/incompatibilidade da configuração HTTP resulta 503 vazio e não armazenável.
Segredos continuam em ambiente/keyring privados, nunca NEXT_PUBLIC ou build público.
Compose permanece local e preserva credenciais/realm/volumes.

## Limites e quotas

Formulário URL-encoded: 4096 bytes efetivamente lidos, até oito pares, duplicatas
recusadas; somente returnTo no login e csrf/returnTo no logout. Leitura tem prazo de
cinco segundos. Content-Length não é a fonte da garantia. Callback: query codificada
até 8192 bytes, até oito pares, nomes até 64 e valores até 4096 caracteres; 413 vazio
para excedentes. Limites de JWT/JWKS/documentos e timeout HTTP cinco segundos
existentes preservados. Sem retry de code/refresh; falhas ambíguas de refresh revogam.

Quotas por rota compartilhadas em PostgreSQL: 120 login, 240 callback, 240 logout por
60 segundos. 429 + Retry-After; falha de storage → 503 antes de operação custosa.
Configuração WEB_AUTH_RATE_WINDOW_SECONDS/WEB_AUTH_LOGIN_LIMIT/WEB_AUTH_CALLBACK_LIMIT/
WEB_AUTH_LOGOUT_LIMIT, mesmos valores em todas as réplicas. Nenhum X-Forwarded-For
nem endereço de NAT é interpretado. São quotas globais, não individuais; atacante
pode esgotá-las. Algoritmo, concorrência e riscos no ADR 0033. Backoff de discovery
adicional de dez segundos por processo; refresh e JWKS mantêm seus controles próprios.

Instalar explicitamente em banco de destino já com migração 0001:

```bash
cd apps/web
npm run session:migrate -- 0002_auth_quotas
```

Em instalação nova, executar 0001 (comando padrão) e depois 0002. Runtime precisa
SELECT/INSERT/UPDATE/DELETE na tabela, sem DDL. Nunca aplicar downgrade em banco de
trabalho. A migração 0002.down remove somente quotas; testes isolados comprovam
preservação de sessão/transação/legado. Três linhas no máximo, sem necessidade de prune.

## Operação e homologação

Proxy confiável deve limitar conexões/header/URI/body, prazos de leitura lenta,
volume total e egress; não logar Authorization, Cookie, códigos ou queries OIDC.
Aplicação não adiciona logging sensível; scripts de migração só reportam classe
do erro. 401 Bearer/403 Problem Details existentes preservados; erros web são
vazios ou feedback genérico. TLS PostgreSQL, secret manager/key rotation, política
Keycloak, logs externos, carga/disponibilidade e auditoria #41 requerem implantação.
Não é pentest nem homologação de produção/M04 completa.

Testes padrão: pytest + npm test; integração: npm run test:integration; Next/API:
npm run test:http. Exigem bancos isolados inicialmente vazios, como descrito em
identity-web.md. TEST_WEB_BROWSER_ENABLED=1 no harness HTTP ativa Chrome headless
já instalado (TEST_WEB_CHROME_PATH opcional), perfil temporário, sem nova dependência.
Verifica hidratação/navigation Link, CSP sem violações legítimas, bloqueio de script
sem nonce e login/logout com provedor simulado assinado. Não prova Keycloak real,
TLS público, todos os browsers ou acessibilidade manual. Relatório distingue execuções.
