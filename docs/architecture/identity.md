# Identidade e autorização — OIDC e M04.05

A API atua como OAuth 2.0 Resource Server: aceita access tokens do provedor externo,
valida JWT e converte papéis em permissões. Não emite tokens, recebe senhas ou executa
refresh. O [BFF Next.js M04.03](identity-web.md) implementa o cliente de login,
sessão compartilhada, refresh e logout; a API mantém seu contrato. Decisão: [ADR 0016](../decisions/0016-oidc-resource-server.md).

## Configuração

Pydantic Settings lê ambiente e `.env` conforme o restante da API. Nenhuma variável
OIDC é NEXT_PUBLIC. O Compose Docker já propaga a configuração para a API.

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
| OIDC_HUMAN_CLIENT_ID | libris-web | Cliente interativo permitido em azp assinado; outros clientes são recusados |
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
| libris-cataloger | bibliographic:read/create/update, authority:read, metadata_revision:read/create, editorial:submit |
| libris-authority-manager | bibliographic:read, authority:read/manage |
| libris-reviewer | bibliographic:read, authority:read, metadata_revision:read, metadata_audit:read, editorial:approve/return |
| libris-publisher | bibliographic:read, authority:read, metadata_revision:read, metadata_audit:read, editorial:publish/withdraw/republish/archive |
| libris-admin | Todas: as anteriores, bibliographic:delete e system:admin |

As operações editoriais e seus limites estão no [contrato #27](editorial-lifecycle.md).
O realm demonstrativo provisiona os seis papéis do mapa centralizado. Instâncias
persistidas precisam receber reviewer/publisher explicitamente; a importação de
startup não sobrescreve um realm existente.

Múltiplos papéis somam permissões. Papel desconhecido ou ausente não concede nada.
SYSTEM_ADMIN não é um bypass implícito: libris-admin recebe as 17 concessões
explicitamente enumeradas; ampliar o enum não amplia esse papel automaticamente. Extrair resource_access[OIDC_ROLE_CLIENT].roles por padrão;
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

BibliographicService.create/revise/read exigem `context=` confiável; `actor=actor`
permanece adaptador para humano OIDC autenticado. Sem contexto/ator a operação é
negada. O chamador HTTP futuro obtém HumanContext exclusivamente de
get_execution_context e o propaga ao serviço. Não construir actor a partir de JSON do cliente.
O domínio bibliográfico não importa FastAPI; identity não acessa tabelas bibliográficas.

Revision.actor_id e SemanticRevision.actor_id são opcionais. Origem, processo,
instante, perfil e RDF permanecem preservados. Aplicar `uv run alembic upgrade head`
explicitamente antes de usar os serviços atualizados sobre um banco existente.
Migração 0002_revision_actor é aditiva, sem backfill/UPDATE das revisões imutáveis.
O downgrade remove somente a coluna e perde as associações de ator; não executar
em dados de trabalho sem decisão explícita. Histórico com NULL não recebe ator fictício.
A #28 acrescenta auditoria observada, atores técnicos controlados e leitura interna
por metadata_audit:read; ver [contrato e limites](provenance-audit-versioning.md).

## Keycloak opcional local

A configuração importa realm libris sem usuários/senhas e dois clients:

- libris-api: bearer-only, sem login ou emissão própria; contém os seis client roles.
- libris-web: público, Authorization Code com PKCE S256, sem implicit flow,
  password grant ou service accounts. Redirect registrado:
  http://localhost:3000/oidc/callback. O [BFF M04.03](identity-web.md) implementa callback/login; validação web real
  segue procedimento e evidências próprios.

O scope padrão `basic` em libris-web mantém a claim obrigatória `sub` em Keycloak
25+. Mapper de audiência inclui libris-api somente no access token. Mapper de client roles
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
docker compose -f docker-compose.yml config --quiet
docker compose -f docker-compose.yml up --build -d
```

Browser/host precisam resolver keycloak.localhost em 127.0.0.1; se o sistema não
resolver nomes .localhost, adicionar `127.0.0.1 keycloak.localhost` ao /etc/hosts.
Docker usa alias de rede keycloak.localhost e mesma porta interna/externa 8081.
KC_HOSTNAME fixa a URL pública; o Compose define exatamente o mesmo emissor na API.
Fora do Docker, definir OIDC_ENABLED=true e esse OIDC_ISSUER_URL no ambiente/.env.
Não substituir o emissor por localhost/keycloak nem desabilitar a comparação de iss.

Admin console: http://keycloak.localhost:8081/admin. Criar usuário local no realm
libris, definir senha no provedor e atribuir client roles de libris-api. O volume
Keycloak preserva o realm; import não sobrescreve realm existente, portanto mudanças
no JSON exigem atualização pelo administrador. Produção precisa configuração própria.

Para validar Code + PKCE sem implementar sessão Next.js, use o
[harness e roteiro isolado M04.02](identity-keycloak-local.md). O harness mantém
verifier, state, códigos e tokens em memória; verifica state antes da troca,
rejeições PKCE/redirect, API real e rotação de chave. Não imprime credenciais nem
precisa de callback web. A sessão de produto da #36 está descrita em [identidade web](identity-web.md);
o harness M04.02 não a homologa.

## Verificações

A execução M04.02 / #35 está no [relatório separado](identity-m04-02-verification.md),
com resultados Keycloak reais, testes offline e limitações de navegador/Next.js.
O [roteiro local](identity-keycloak-local.md) inclui setup isolado, DNS IPv4/IPv6,
provisionamento, suíte opcional e desligamento que preserva volumes.

A [baseline M04.01](security-baseline.md), a
[matriz de acesso](security-access-matrix.md), o
[modelo de ameaças](security-threat-model.md) e os
[critérios de saída M04](security-m04-exit-criteria.md) consolidam os controles
atuais e as dependências futuras. Resultados da execução de 2026-10-13 estão na
[verificação M04.01](security-m04-01-verification.md); o relatório da Entrega A
abaixo permanece evidência histórica.

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

## Enforcement vigente M04.05 / #38

[Contrato de autorização por operação](operation-authorization.md),
[ADR 0031](../decisions/0031-operation-authorization.md) e
[verificação própria](identity-m04-05-verification.md) sucedem as descrições de
confiança interna/ator opcional desta Entrega A. O Resource Server e /me permanecem.

BibliographicService.create/revise/read agora exigem contexto confiável explícito.
`actor=` autenticado continua como adaptador M03 para HumanContext; `actor=None`
sem contexto é negado. ExecutionActor isolado classifica auditoria, sem conceder
acesso. TechnicalContext é configuração do composition root, com identidade/origem,
permissões e operações limitadas, sem decisões humanas ou SYSTEM_ADMIN.
HistoryService e EditorialService usam o mesmo guard injetável, sem acesso a tabelas
de identidade ou duplicação de auditoria. Falhas tipadas de autorização retornam 403
pelo Problem Details v1 existente. /health público e falhas OIDC 401 são preservados.

Leitura editorial genérica requer read + metadata_revision:read; reader não ganha
acesso a rascunhos sem contrato institucional. Público usa somente read_public e
revisão efetivamente publicada. Autoria histórica NULL permanece inalterada;
novas operações técnicas registram sua identidade explícita, sem backfill.
Os contextos Python não são prova criptográfica; não deserializar payload/header.
M2M operacional e homologação #42 permanecem separados. A governança #39 está
definida no [contrato M04.06](identity-governance.md), com
[evidências próprias](identity-m04-06-verification.md). IdentityService exige
azp assinado igual a OIDC_HUMAN_CLIENT_ID após validação JWT; serviços externos
não são promovidos a humanos por receberem roles. Configurar o cliente interativo
sem service accounts ou token exchange para impersonação. /me conserva seu DTO.


## Atualização M04.07 — 2026-10-14

A [política HTTP M04.07](http-security.md) acrescenta validação CORS por
ambiente, CSP com nonce no SSR Next.js, headers/cache, limites de entrada e quotas
compartilhadas PostgreSQL. Reutiliza PKCE, state/binding/consumo único, sessão cifrada,
CSRF e autorização existentes. Instalação exige `alembic upgrade head` explicitamente; a revisão **0005_web_auth**
cria/adota as tabelas em `libris_web`, inclusive quotas (ADR 0034). Nenhuma migração executa no startup. Em produção web,
WEB_HTTPS_TERMINATED=1 exige proxy TLS/rede confiáveis; Compose continua local.
Resultados, falhas corrigidas e limites no [relatório próprio](http-security-m04-07-verification.md).
As evidências/tabelas históricas acima não foram reclassificadas como homologação
atual; carga, TLS público, operação institucional e pentest continuam pendentes.


## Atualização M04.08 — 2026-10-14

A [auditoria de segurança #41](security-audit.md) emite envelopes JSON fechados
para autenticação, decisões de autorização, sessões BFF, quotas e negação administrativa.
Correlação por requisição propaga BFF → API; ator só vem do boundary confiável.
[ADR 0035](../decisions/0035-security-audit-emission.md) define emissão best effort,
sem tabela/migração ou alteração semântica da auditoria M03. Retenção/acesso e coleta
durável dependem do destino operacional; não há expurgo automático nem homologação
de produção. Resultados desta execução no [relatório separado](security-audit-m04-08-verification.md);
as tabelas e verificações históricas anteriores permanecem evidências datadas.
