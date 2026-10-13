# ADR 0030 — BFF OIDC e sessões web compartilhadas

Data: 2026-10-13. Estado: aceito para implementação M04.03 / #36;
homologação operacional/produção separada.

## Contexto

O FastAPI é Resource Server (ADR 0016), não cliente de login. O Next.js 16
precisa executar Code + PKCE sem entregar tokens ao navegador, sobreviver a
reinícios e coordenar refresh token rotation entre réplicas. PostgreSQL já é
infraestrutura do monólito; as tabelas bibliográficas experimentais não são
armazenamento de identidade.

## Decisão

Route Handlers Node.js constituem um BFF pequeno. `openid-client` 6.8.8
implementa PKCE S256, processamento OIDC e validação de claims. Habilitar
`enableNonRepudiationChecks` explicitamente: o padrão de Code Flow da biblioteca
confia na comunicação TLS com o token endpoint e não verifica a assinatura
por JWKS sozinho. Esta entrega exige assinatura RS256, issuer/client audience,
expiração e nonce. Audience da API permanece `libris-api`, não `libris-web`.

`pg` acessa somente o schema `libris_web`. Migrações SQL próprias do frontend são
executadas explicitamente por operador, separadas da cadeia Alembic experimental
0001–0004. Não há acesso BFF às tabelas de domínio nem alteração de metadata
SQLAlchemy. Migração inicial não se repete automaticamente; falha se o schema já
existe. Downgrade é explícito e destrói somente as sessões/transações web.

Sessão e transação são cifradas com AES-256-GCM via Node Crypto, IV aleatório de
96 bits e AAD contendo tipo/hash do registro. IDs, state e binding de navegador
são aleatórios de 256 bits; o banco guarda hashes SHA-256 como chaves. Cada
tentativa tem binding/cookie próprio, expira em cinco minutos e é consumida
por DELETE RETURNING antes da troca. A sessão tem limite absoluto, padrão oito
horas, sem extensão por renovação. Não se conserva ID token após validação.

Locks FOR UPDATE serializam consulta, refresh, chamada API e revogação. Tokens
rotacionados são persistidos antes da chamada API, na mesma transação local.
Timeout/rede no refresh tem resultado externo incerto: invalidar, exigir login.
Resposta definitiva 429/5xx permite backoff compartilhado de dez segundos, sem
usar access token vencido. Não há atomicidade distribuída com o provedor: se o
processo morrer depois de rotacionar e antes do commit, o próximo refresh pode
falhar e encerrar a sessão; a prioridade é segurança, não continuidade garantida.

Cookies host-only, HttpOnly, SameSite=Lax, Secure quando a origem é HTTPS.
Em HTTPS usar prefixo __Host- inclusive nos cookies temporários, Path=/ para
impedir cookie tossing por subdomínios; em HTTP local, o binding é restrito a
/oidc/callback. Logout exige POST, Origin e Host exatos mais token CSRF da sessão.
Login exige POST/Origin/Host; callback exige state/binding/nonce/PKCE.
Destinos limitados a caminhos canônicos /pt e /en; rejeitar URLs externas,
backslashes, controles, separadores codificados e codificação dupla.

Logout revoga primeiro, apaga cookie e pode redirecionar ao end_session_endpoint
com client_id e post_logout_redirect_uri registrado. Não enviar id_token_hint
porque colocaria um token na URL do navegador; Keycloak pode pedir confirmação.
Não se promete revogação global dos JWTs emitidos.

## Alternativas e consequências

Cookie contendo JWT/ciphertext de tokens viola o requisito de ID opaco.
Memória de processo perde sessões e não coordena workers. Redis adicionaria
infraestrutura desnecessária. Implementar JOSE manualmente aumenta risco;
Auth.js oferece recursos amplos, mas adaptar armazenamento/cookies aos requisitos
seria maior que os handlers e o cliente OIDC usados aqui.

Pool é local, estado é compartilhado: todas as réplicas usam banco e keyring
iguais. Locks ocupam conexão durante HTTP limitado a cinco segundos; avaliar carga
e quotas antes de produção. Runtime deve ter acesso somente ao schema web
(SELECT/INSERT/UPDATE/DELETE), sem DDL; migração usa papel separado.
Produção requer HTTPS, TLS PostgreSQL configurado/verificado na URL pg, secret
manager, rotação, backups e proxy que preserve Host público. Não há framework
genérico de identidade, cadastro de usuários ou auditoria de segurança #41.

Referências primárias: [openid-client](https://github.com/panva/openid-client),
[verificação de assinatura](https://github.com/panva/openid-client/blob/main/docs/functions/enableNonRepudiationChecks.md),
[OAuth BCP](https://www.rfc-editor.org/rfc/rfc9700.html),
[RP-Initiated Logout](https://openid.net/specs/openid-connect-rpinitiated-1_0.html).
