# Identidade e autorização — Entrega A

A API atua como OAuth 2.0 Resource Server: aceita access tokens do provedor externo,
valida JWT e converte papéis em permissões. Não emite tokens, recebe senhas, executa
refresh ou implementa login no Next.js. Decisão: [ADR 0016](../decisions/0016-oidc-resource-server.md).

## Configuração

Pydantic Settings lê ambiente e `.env` conforme o restante da API. Nenhuma variável
OIDC é NEXT_PUBLIC. O overlay Docker já propaga a configuração para a API.

| Variável | Default | Significado |
| --- | --- | --- |
| OIDC_ENABLED | false | Habilita validação; false mantém endpoints protegidos bloqueados |
| OIDC_ISSUER_URL | http://localhost:8081/realms/libris | Valor exato de iss e issuer da descoberta, incluindo eventual barra final |
| OIDC_AUDIENCE | libris-api | Audiência da API; distinta do client frontend |
| OIDC_ALGORITHMS | RS256 | Allowlist separada por vírgula; RS256/384/512, ES256/384/512 ou EdDSA |
| OIDC_JWKS_CACHE_TTL | 300 | Validade das chaves em segundos, positiva |
| OIDC_JWKS_REFRESH_INTERVAL | 10 | Intervalo mínimo positivo entre tentativas de refresh, inclusive falhas |
| OIDC_CLOCK_SKEW_SECONDS | 30 | Tolerância de relógio, 0–300 segundos |
| OIDC_HTTP_TIMEOUT_SECONDS | 5 | Timeout HTTP por operação, >0 e <=60 segundos |
| OIDC_ROLE_SOURCE | client | client ou realm; realm exige escolha explícita |
| OIDC_ROLE_CLIENT | libris-api | Client confiável para extração de papéis |
| OIDC_ACCESS_TOKEN_CLAIM | typ | Claim assinada no payload que distingue access token |
| OIDC_ACCESS_TOKEN_VALUE | Bearer | Valor esperado; Keycloak emite ID para ID tokens |

Produção habilitada exige HTTPS. Em outros provedores, configurar claim equivalente
(por exemplo token_use=access) e uma audiência específica. Tokens sem o discriminador
configurado são rejeitados, mesmo se a assinatura e a audiência forem válidas.
O campo typ do header JOSE sozinho não basta para esse contrato.

## Fluxo e falhas

Descoberta: `{issuer sem barra final}/.well-known/openid-configuration`.
O issuer publicado deve ser igual à configuração. Somente seu jwks_uri é consultado;
JWT não escolhe host/chaves. HTTPX não segue redirects nem usa proxies do ambiente.
Documentos até 1 MiB, até 100 chaves, tokens até 16 KiB. Exigir chave assimétrica
única compatível com kid, alg, use e key_ops. PyJWT verifica assinatura e claims;
exp/nbf/iat devem ser números finitos, exp é obrigatório, sub não pode ser vazio.

Cache por aplicação/worker, protegido por lock. TTL expirado ou kid desconhecido
solicita refresh, limitado pelo intervalo configurado. Falhas também ativam o
intervalo; não há loop de retries nem consultas ilimitadas por tokens aleatórios.
Dentro desse intervalo uma chave recém-rotacionada ainda desconhecida pode gerar
401; nova tentativa após o intervalo permite recuperá-la. Chaves expiradas não
são fallback. Descoberta não acontece no startup, preservando liveness isolada;
sua URI fica em memória até reiniciar o processo.

Ausência/erro de Bearer, falha do provedor, token inválido e OIDC desabilitado:
401 com WWW-Authenticate: Bearer e detalhe genérico. Identidade válida sem todas
as permissões solicitadas: 403. Eventos operacionais usam logging Python warning;
rejeições JWT usam debug, sem token ou dados pessoais. Configurar níveis/handlers
na implantação; não foi criado um sistema paralelo de logging.

## Papéis e permissões

| Papel externo | Permissões internas |
| --- | --- |
| libris-reader | bibliographic:read, authority:read |
| libris-cataloger | bibliographic:read/create/update, authority:read, metadata_revision:read/create |
| libris-authority-manager | bibliographic:read, authority:read/manage |
| libris-admin | Todas: as anteriores, bibliographic:delete e system:admin |

Múltiplos papéis somam permissões. Papel desconhecido ou ausente não concede nada.
SYSTEM_ADMIN não é um bypass implícito: libris-admin recebe todas as permissões
definidas no enum. Extrair resource_access[OIDC_ROLE_CLIENT].roles por padrão;
realm_access.roles só com OIDC_ROLE_SOURCE=realm. Não ler headers/body para papéis.
A identidade expõe os papéis externos da origem escolhida, inclusive desconhecidos,
mas o mapa concede permissões somente aos papéis conhecidos.

## Dependências FastAPI

```python
from typing import Annotated
from fastapi import Depends
from libris.modules.identity.api.dependencies import get_current_actor, require_permissions
from libris.modules.identity.domain.models import AuthenticatedActor
from libris.modules.identity.domain.permissions import Permission

# Assinaturas ilustrativas para rotas futuras:
async def inspect(actor: Annotated[AuthenticatedActor, Depends(get_current_actor)]) -> str:
    return actor.actor_id

async def write(actor: Annotated[AuthenticatedActor, Depends(
    require_permissions(Permission.BIBLIOGRAPHIC_CREATE)
)]) -> str:
    return actor.actor_id
```

GET `/api/v1/identity/me` retorna somente actor_id, roles e permissions ordenados.
Não retorna JWT, sub, emissor, e-mail ou configuração. `/health` continua público.
CORS mantém origens explícitas e permite Authorization para GET. As permissões
para endpoints catalográficos serão aplicadas na Entrega B.

Nos testes, substituir `get_current_actor` via `app.dependency_overrides` ou
`get_identity_service` por um serviço com TokenValidator simulado. A instância real
fica em app.state durante o lifespan; não há singleton global de serviço/cache.

## Revisões e proveniência

BibliographicService.create/revise aceitam `actor=actor` como argumento nomeado
opcional. O chamador HTTP futuro deve obter esse objeto exclusivamente da dependência
autenticada e passá-lo ao serviço. Não construir actor a partir de JSON do cliente.
O domínio bibliográfico não importa FastAPI; identity não acessa tabelas bibliográficas.

Revision.actor_id e SemanticRevision.actor_id são opcionais. Origem, processo,
instante, perfil e RDF permanecem preservados. Aplicar `uv run alembic upgrade head`
explicitamente antes de usar os serviços atualizados sobre um banco existente.
Migração 0002_revision_actor é aditiva, sem backfill/UPDATE das revisões imutáveis.
O downgrade remove somente a coluna e perde as associações de ator; não executar
em dados de trabalho sem decisão explícita. Histórico com NULL não recebe ator fictício.
Não há auditoria completa ou taxonomia implementada para atores de serviço.

## Keycloak opcional local

A configuração importa realm libris sem usuários/senhas e dois clients:

- libris-api: bearer-only, sem login ou emissão própria; contém os quatro client roles.
- libris-web: público, Authorization Code com PKCE S256, sem implicit flow,
  password grant ou service accounts. Redirect registrado:
  http://localhost:3000/oidc/callback. É contrato demonstrativo; não há página de callback/login.

Mapper de audiência inclui libris-api somente no access token. Mapper de client roles
publica resource_access.libris-api.roles somente no access token. JWT esperado:
iss=http://keycloak.localhost:8081/realms/libris, aud contendo libris-api,
sub não vazio, exp e typ=Bearer; JOSE alg=RS256 e kid correspondente ao JWKS.
Não colocar a audiência da API em ID tokens. Administrador do realm deve atribuir
client roles explicitamente aos usuários locais; não existe concessão automática.

Na raiz, após copiar `.env.example` para `.env`, definir credenciais administrativas
locais sem versioná-las:

```bash
export KEYCLOAK_ADMIN_USERNAME='seu-admin-local'
read -rsp 'Senha administrativa local: ' KEYCLOAK_ADMIN_PASSWORD
export KEYCLOAK_ADMIN_PASSWORD
# Não imprimir a variável.
docker compose -f docker-compose.yml -f docker-compose.oidc.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.oidc.yml up --build -d
```

Browser/host precisam resolver keycloak.localhost em 127.0.0.1; se o sistema não
resolver nomes .localhost, adicionar `127.0.0.1 keycloak.localhost` ao /etc/hosts.
Docker usa alias de rede keycloak.localhost e mesma porta interna/externa 8081.
KC_HOSTNAME fixa a URL pública; o overlay define exatamente o mesmo emissor na API.
Fora do Docker, definir OIDC_ENABLED=true e esse OIDC_ISSUER_URL no ambiente/.env.
Não substituir o emissor por localhost/keycloak nem desabilitar a comparação de iss.

Admin console: http://keycloak.localhost:8081/admin. Criar usuário local no realm
libris, definir senha no provedor e atribuir client roles de libris-api. O volume
opcional preserva o realm; import não sobrescreve realm existente, portanto mudanças
no JSON exigem atualização pelo administrador. Produção precisa configuração própria.

Para obter token manualmente sem implementar login, usar cliente OIDC com PKCE,
ou gerar um verifier e challenge em um terminal local (não guardar em logs):

```bash
python3 - <<'PY'
import base64, hashlib, secrets
verifier = secrets.token_urlsafe(48)
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
print('verifier:', verifier)
print('challenge:', challenge)
print('state:', secrets.token_urlsafe(24))
PY
```

Abrir no browser o authorization_endpoint publicado na descoberta, com
client_id=libris-web, response_type=code, scope=openid,
redirect_uri=http://localhost:3000/oidc/callback, state gerado,
code_challenge=challenge e code_challenge_method=S256. Após autenticar, o redirect
vai à URL de callback ainda não implementada: copiar code da barra de endereço,
conferir state e trocar imediatamente no token_endpoint da descoberta via POST
application/x-www-form-urlencoded: grant_type=authorization_code,
client_id=libris-web, code, redirect_uri idêntico e code_verifier original.
Usar somente access_token como Bearer em `/api/v1/identity/me`. Não colocar tokens
em comandos compartilhados, arquivos versionados ou documentação. Esse procedimento
manual não adiciona callback ou fluxo de refresh à aplicação.

## Verificações

```bash
cd apps/api
uv sync --locked
uv run pytest
uv run pytest ../../tests/api/identity
uv run ruff check . ../../tests
uv run mypy src
uv run alembic heads
uv run alembic upgrade head --sql
# PostgreSQL dedicado previamente migrado, como em semantic-foundation.md:
TEST_DATABASE_URL="$DATABASE_URL" uv run pytest ../../tests/integration -m integration
# Na raiz:
bash scripts/check.sh
```

A suíte padrão usa RSA local e HTTPX MockTransport, sem PostgreSQL/Keycloak/Elasticsearch.
Inclui assinatura/claims, allowlist, ID tokens, descoberta/JWKS, TTL/rotação/limite de
refresh, concorrência de cache, papéis, identidade estável, 401/403, CORS e overrides.
Integração PostgreSQL testa persistência do ator e histórico sem ator. Esses testes
não comprovam uma integração real com Keycloak. Ver [relatório](identity-verification.md).
