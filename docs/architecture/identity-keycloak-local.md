# Keycloak local isolado — M04.02 / #35

Este roteiro valida o Resource Server do [ADR 0016](../decisions/0016-oidc-resource-server.md)
e Authorization Code + PKCE S256 com o client público `libris-web`.
O [relatório desta execução](identity-m04-02-verification.md) distingue provas reais,
simulações e limites. Login, callback, logout e sessão Next.js pertencem à #36.
O harness não publica rotas, não administra catálogo e não guarda tokens em arquivos.

## Preparação e isolamento

Requisitos: Docker Engine/Compose acessível, imagens/dependências disponíveis,
Python 3.13 e dependências instaladas por `cd apps/api && uv sync --locked`.
Para verificações web, Node 24/npm; NVM pode precisar ser carregado no terminal.
O conjunto usa PostgreSQL 17, Elasticsearch 9.5.5, Keycloak 26.8.0, API e web.
Reserve memória para os cinco serviços e as portas TCP 5432, 9200, 8081, 8000 e 3000.
Antes de iniciar, execute na raiz:

```bash
docker info --format '{{.ServerVersion}}'
docker compose version
docker ps -a --format '{{.Names}} {{.Status}} {{.Ports}}'
docker volume ls
ss -ltn
```

Se houver conflito, não pare containers/processos de terceiros. As portas de
PostgreSQL/API/web/Elasticsearch podem ser ajustadas nas variáveis documentadas
no README. A porta Keycloak 8081 e o issuer canônico precisam continuar consistentes.
Nunca reutilize um projeto Compose de trabalho para esta verificação. Um nome
novo gera volumes próprios; volumes antigos `libris_*` não precisam ser apagados.

Crie um arquivo privado **fora do repositório**, com segredos aleatórios, sem
ativar `set -x` ou imprimir seu conteúdo:

```bash
export OIDC_TEST_PROJECT="libris-oidc-test-$(date +%Y%m%d-%H%M%S)"
export OIDC_TEST_ENV="$(mktemp /tmp/libris-oidc.XXXXXX)"
apps/api/.venv/bin/python - <<'PY'
import os
import secrets
from pathlib import Path
path = Path(os.environ['OIDC_TEST_ENV'])
path.chmod(0o600)
password = secrets.token_urlsafe(32)
path.write_text(
    f'POSTGRES_PASSWORD={password}\n'
    f'DATABASE_URL=postgresql+asyncpg://libris:{password}@postgres:5432/libris\n'
    'KEYCLOAK_ADMIN_USERNAME=oidc-test-admin\n'
    f'KEYCLOAK_ADMIN_PASSWORD={secrets.token_urlsafe(32)}\n'
)
PY
docker compose --env-file "$OIDC_TEST_ENV" -p "$OIDC_TEST_PROJECT" \
  -f docker-compose.yml -f docker-compose.oidc.yml config --quiet
docker compose --env-file "$OIDC_TEST_ENV" -p "$OIDC_TEST_PROJECT" \
  -f docker-compose.yml -f docker-compose.oidc.yml up --build -d
```

`--env-file` seleciona a configuração privada; variáveis já exportadas no terminal
prevalecem. Revise configurações locais preexistentes sem divulgar seus valores.
Não executar migrações no startup nem migrar banco bibliográfico para testar OIDC.
As credenciais de bootstrap só inicializam um volume Keycloak novo; trocar o arquivo
não redefine senhas de uma instância persistida.

## Hostname, descoberta e inicialização

O issuer único é `http://keycloak.localhost:8081/realms/libris`, audience `libris-api`.
Docker resolve `keycloak.localhost` pelo alias de rede para Keycloak, na porta 8081.
No host, o overlay publica **somente IPv4 127.0.0.1**. Verifique:

```bash
getent hosts keycloak.localhost
curl --noproxy '*' --resolve keycloak.localhost:8081:127.0.0.1 --fail --silent \
  http://keycloak.localhost:8081/realms/libris/.well-known/openid-configuration
curl --noproxy '*' --resolve keycloak.localhost:8081:127.0.0.1 --fail --silent \
  http://keycloak.localhost:8081/realms/libris/protocol/openid-connect/certs
curl --fail --silent http://localhost:8000/health
```

Os dois documentos OIDC contêm metadados/chaves públicas, não tokens de sessão.
Confira `issuer`, `authorization_endpoint`, `token_endpoint` e `jwks_uri`;
eles devem usar o hostname canônico. Se a resolução local der somente `::1`,
configure, conforme a política do host, `127.0.0.1 keycloak.localhost` em `/etc/hosts`
e repita a consulta. `curl --resolve` verifica o caminho IPv4 mantendo Host/URL;
isso não prova a resolução automática do navegador. Não trocar issuer por `api`,
`keycloak` ou `localhost` e não relaxar a comparação de `iss`.

Verifique `ps` e logs de inicialização **do projeto de teste**. Elasticsearch pode
levar mais tempo para ficar saudável; a API aguarda PostgreSQL/Elasticsearch,
mas não espera descoberta OIDC no startup. Keycloak importa o realm durante sua
inicialização; a primeira execução pode demorar. `/health` continua liveness público,
sem prometer readiness dos serviços.

O JSON importa `libris`, os clients API/web e seis papéis de API iguais às chaves
em `ROLE_PERMISSIONS`. Não há usuários predefinidos. `libris-web` tem PKCE S256,
redirect exato `http://localhost:3000/oidc/callback`, mapper de audience somente
no access token e o scope padrão **basic**, necessário para emitir `sub` em Keycloak
25+. Consulte o [guia do Keycloak](https://www.keycloak.org/docs/26.5.7/server_admin/index.html).

A [importação de startup](https://www.keycloak.org/server/importExport) ignora realms
já existentes. Em instância de teste persistida, adicionar explicitamente
`libris-reviewer`/`libris-publisher` em Clients → libris-api → Roles e atribuir
`basic` como Default em Clients → libris-web → Client scopes. Não apagar volumes
para forçar importação. A alternativa preferida é um projeto de teste novo.
Papéis são atribuídos em Users → Role mapping → client roles de libris-api;
nenhum usuário recebe `libris-admin` automaticamente.

## Harness real e suíte opcional

O harness usa o formulário de login real por HTTP e troca o código no token endpoint;
não usa password grant para `libris-web`. Somente o administrador de bootstrap
usa `admin-cli` no master para criar/remover recursos de teste. Isso não adiciona
login/password grant ao Resource Server. A ativação requer consentimento explícito
na configuração de teste: `TEST_KEYCLOAK_ISOLATED=1`; nunca usar credenciais
institucionais ou um realm compartilhado.

Execução reproduzível na rede Docker, sem depender do resolver do host:

```bash
# Arquivo privado gerado acima contém exclusivamente atribuições shell aleatórias.
set -a
source "$OIDC_TEST_ENV"
set +a
docker compose --env-file "$OIDC_TEST_ENV" -p "$OIDC_TEST_PROJECT" \
  -f docker-compose.yml -f docker-compose.oidc.yml run --rm --no-deps -T \
  -e KEYCLOAK_ADMIN_USERNAME -e KEYCLOAK_ADMIN_PASSWORD \
  -e TEST_KEYCLOAK_ISOLATED=1 -e TEST_KEYCLOAK_API_URL=http://api:8000 \
  -v "$PWD/tests:/tests:ro" api python /tests/integration/keycloak_harness.py
```

Para executar também os testes de PKCE/state e o gate pytest opcional:

```bash
docker compose --env-file "$OIDC_TEST_ENV" -p "$OIDC_TEST_PROJECT" \
  -f docker-compose.yml -f docker-compose.oidc.yml run --rm --no-deps -T --user root \
  -e KEYCLOAK_ADMIN_USERNAME -e KEYCLOAK_ADMIN_PASSWORD \
  -e TEST_KEYCLOAK_ENABLED=1 -e TEST_KEYCLOAK_ISOLATED=1 \
  -e TEST_KEYCLOAK_API_URL=http://api:8000 \
  -v "$PWD/tests:/tests:ro" \
  -v "$PWD/apps/api/pyproject.toml:/config/pyproject.toml:ro" api \
  sh -c 'uv sync --locked --group dev && uv run pytest -c /config/pyproject.toml -p no:cacheprovider -s /tests/integration/test_keycloak_oidc.py'
```

O usuário root instala ferramentas apenas no container descartável. O pytest usa
subprocesso e saída sanitizada: não imprime stderr, locals, URLs de callback,
tokens, códigos, senhas ou cookies. Evite instrumentação de requests/tracebacks
adicional. Fora do Docker, use `TEST_KEYCLOAK_API_URL=http://localhost:8000` e a
mesma configuração privada, depois de corrigir DNS; o issuer permanece o mesmo.

Sem ativação, a suíte opcional executa os casos puros de PKCE/state e registra
**skip** do caso real. Ela não está nos testpaths da suíte API padrão:

```bash
cd apps/api
uv run pytest
uv run pytest -c pyproject.toml ../../tests/integration/test_keycloak_oidc.py
```

O harness cria somente um usuário sintético com senha aleatória em memória,
atribui reader, verifica 403 em rota de teste local, adiciona cataloger/reviewer/
publisher e verifica a união centralizada sem admin. Obtém access/ID tokens reais,
confere 200/401 na API implantada e valida state, verifier errado, reutilização e
redirect arbitrário. A rota de permissão existe apenas no TestClient, sem rota
administrativa artificial na implantação.

A rotação cria **um provedor RSA temporário** de maior prioridade no realm isolado,
obtém um token com novo kid e consulta JWKS real. O relógio monotônico do cache é
injetado para testar o intervalo mínimo sem sleeps; datas JWT usam o relógio real.
Isso comprova rotação real com passagem de tempo do cache controlada, não uma
medição de latência nem propagação instantânea em todos os workers. O `finally`
remove só o provedor de chave e usuário que o harness criou. Encerramento abrupto
ou falha de comunicação na limpeza exige verificar os recursos com prefixo
`m0402-probe-` no **realm de teste**; não apagar usuários/chaves preexistentes.

Keycloak 26.8 marca `.localhost` como contexto seguro
([implementação oficial](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/utils/SecureContextResolver.java)).
O CookieJar padrão não aplica essa exceção em HTTP. O harness adapta exclusivamente
seus cookies locais de `keycloak.localhost`, caminho `/realms/libris/`, em memória.
Não é uma política de cookies para a aplicação e não homologa navegador/Next.js.

## Falhas frequentes e limites

| Sintoma | Diagnóstico e ação |
| --- | --- |
| Conexão recusada no host | conferir IPv4/IPv6, porta 8081, daemon, `ps` e inicialização; manter issuer |
| API não alcança descoberta | conferir rede do projeto/alias `keycloak.localhost`, porta interna e jwks_uri publicado; não apontar para loopback do container |
| Realm antigo após editar JSON | import ignora realm persistido; atualizar explicitamente na instância isolada ou usar projeto novo |
| Token tem aud/typ mas /me dá 401 | verificar `basic` como scope Default e claim `sub`, RS256, issuer exato, clocks e JWKS; não publicar token para diagnosticar |
| Audience ausente/incorreta | verificar mapper `libris-api-audience` no client web e se foi aplicado ao realm persistido |
| invalid_grant | código expirado/reutilizado, verifier incorreto, redirect diferente ou outro client; iniciar fluxo novo sem reutilizar código |
| Redirect recusado | usar somente URI exata registrada; callback de produto ainda pertence à #36 |
| cookie_not_found em HTTP harness | CookieJar não reconhece secure context .localhost; adaptação restrita está no harness; não desligar segurança no provedor |
| 401 | ausência/token inválido, ID token, OIDC desabilitado ou chave indisponível; WWW-Authenticate Bearer, resposta genérica |
| 403 | identidade válida sem permissão requerida; /me só exige autenticação e não retorna 403 apenas por falta de papel |
| Novo kid recebe 401 temporário | aguardar intervalo mínimo de refresh; não diminuir/desabilitar validação para contornar cache |
| Provedor indisponível | cache válido de chave conhecida pode funcionar; expirado não tem fallback; testes de falha usam MockTransport |
| Elasticsearch não saudável | conferir recursos e requisito de vm.max_map_count no README; não alterar kernel sem avaliar host |

HTTP, H2 local do Keycloak e `start-dev` servem exclusivamente ao desenvolvimento.
Produção exige arquitetura própria para TLS, secrets, cookies seguros, rede,
observabilidade, persistência/backup e governança. O Compose não é produção;
esta entrega não homologa #36–#42 nem as futuras APIs M05.

## Desligamento seguro

Mantenha as mesmas variáveis de projeto/arquivo privado e desligue exclusivamente
o projeto criado para a verificação:

```bash
docker compose --env-file "$OIDC_TEST_ENV" -p "$OIDC_TEST_PROJECT" \
  -f docker-compose.yml -f docker-compose.oidc.yml stop
# Opcional: remover só containers/rede do projeto, preservando seus volumes:
docker compose --env-file "$OIDC_TEST_ENV" -p "$OIDC_TEST_PROJECT" \
  -f docker-compose.yml -f docker-compose.oidc.yml down
unset KEYCLOAK_ADMIN_PASSWORD KEYCLOAK_ADMIN_USERNAME POSTGRES_PASSWORD DATABASE_URL
```

Não usar `down -v`, prune ou remoção de volumes. Guarde o arquivo privado com modo
0600 se precisar reiniciar esse projeto: ele contém as credenciais de sua instância
persistida. Remova apenas esse arquivo privado quando decidir abandonar a instância,
sem supor que isso apague dados ou credenciais armazenados no volume. Um novo projeto
usa credenciais novas. Nunca versionar arquivo privado ou volume/export de usuários.
