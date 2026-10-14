# Homologação reproduzível M04.09

Este roteiro usa o checkout local, sem commits, PRs ou alterações remotas.
[Resultados datados](identity-m04-09-verification.md) são evidências separadas;
executar um comando e receber skip não homologa integração.

## Preparação

1. Registrar branch, status, HEAD e diff check; trabalhar somente em main, sem
   descartar arquivos do mantenedor. Registrar também versões e horário.
2. Ler AGENTS, ADRs 0016/0030–0035 e os contratos de identidade, HTTP, auditoria,
   autorização e saída M04. Conferir escopo/dependências #35–#42 no GitHub somente
   em leitura. Não acrescentar endpoints M05.
3. Usar Python 3.13 e Node 24. Instalar locks com `uv sync --locked` em apps/api
   e `npm ci` em apps/web somente quando as dependências não estiverem disponíveis.
   Docker/Compose e imagens PostgreSQL `17-bookworm`, Keycloak `26.8.0` são
   necessários para integração. Chrome é necessário para `--browser`.
4. Inspecionar `docker ps -a`, `docker volume ls` e portas livres. Não parar serviços
   existentes. Reservar aproximadamente 4 GiB livres para ensaio local (estimativa,
   não medição de capacidade); bancos em tmpfs consomem memória. As portas de teste
   são efêmeras, no loopback. Sem Elasticsearch, pois não participa desses fluxos.
5. Dependências desta execução: Python 3.13.15, Node 24.16.0, npm 11.15.0,
   uv 0.12.21, FastAPI 0.143.0, Next 16.4.0, Keycloak 26.8.0 e PostgreSQL 17.
   Conferir patches efetivamente executados no relatório, não inferir por tag Docker.

```bash
git branch --show-current
git status --short
git rev-parse HEAD
git diff --check
python --version
node --version
npm --version
docker --version
docker compose version
google-chrome --version
```

Neste host, Node existe em `/home/inacio/.nvm/versions/node/v24.16.0/bin`;
carregar NVM ou adicionar esse diretório ao PATH. Não modificar variáveis HOME.

## Gate offline

```bash
bash scripts/check.sh
git diff --check
```

O gate executa pytest API, Ruff (incluindo script de integração), mypy strict,
`npm test`, build, typecheck e Compose **estático**. `set -euo pipefail` propaga
falhas. Não inicializa infraestrutura, migra ou aplica DDL. A API padrão usa
testpaths `tests/api`; Node usa somente `*.test.ts`, RSA efêmero/MemoryStore e
transportes simulados. Um teste de limites HTTP abre servidor somente no loopback.
Compose exige Docker CLI instalado; a validação estática não precisa de daemon.
Credenciais efêmeras geradas pelo gate apenas satisfazem validação de configuração.

Comandos individuais, nos diretórios indicados:

```bash
cd apps/api
uv run pytest
uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py
uv run mypy src
cd ../web
npm test
npm run build
npm run typecheck
```

## Integrações opt-in em recursos novos

Após build, na raiz:

```bash
# PostgreSQL, migrações, sessões/quotas concorrentes, M03 e HTTP com OIDC simulado:
apps/api/.venv/bin/python scripts/verify-m04-integration.py --isolated
# Acrescenta provedor e tokens reais, concessão/revogação e BFF real:
apps/api/.venv/bin/python scripts/verify-m04-integration.py --isolated --keycloak
# Acrescenta Chrome real: CSP/hidratação com mock e login/admin/logout com Keycloak:
apps/api/.venv/bin/python scripts/verify-m04-integration.py --isolated --keycloak --browser
```

O script não recebe URLs de bases existentes. Cria nomes/labels aleatórios,
PostgreSQL novo com dados em tmpfs, oito bancos vazios separados e, quando ativado,
Keycloak novo com data em tmpfs. Segredos são aleatórios e privados no ambiente de
subprocessos; não usar shell `set -x`. Descarta configuração de aplicação/teste e
proxies herdados. Não imprime comandos/URLs de banco/erros externos. Logs completos
ficam em diretório `/tmp/libris-m0409-*` modo 0700, arquivos 0600: revisar localmente,
não publicar logs brutos de falhas nem anexar sem sanitização.

Cria/adapta **cópia temporária** do realm versionado, sem usuários, com issuer
exato `http://127.0.0.1:<porta>/realms/libris`, callbacks exatos para o harness
Python e a origem Next efêmera. API, BFF e browser usam o mesmo issuer; não
contorna comparação por issuer alternativo. Essa origem isolada não valida DNS
`keycloak.localhost` nem a implantação Compose de trabalho.

Executa Alembic explicitamente no banco semantic e harnesses web migram seus
próprios bancos vazios. Migrações com downgrade usam bancos exclusivos criados
pelo script. Nenhum schema é criado no startup. API/Uvicorn e Next são processos
do ensaio, com access log API desabilitado. Keycloak usa `start-dev`/H2 somente
no ensaio. Teste web real muda TTL/refresh exclusivamente nesse realm descartável.

Variáveis geradas internamente, sem valores secretos:

| Ensaio | Ativação/configuração |
| --- | --- |
| M03 | TEST_DATABASE_URL (asyncpg), DATABASE_URL administrativo |
| Migrações isoladas | TEST_MIGRATION_DATABASE_URL, TEST_EDITORIAL_MIGRATION_DATABASE_URL, TEST_WEB_MIGRATION_DATABASE_URL |
| Sessões | TEST_WEB_ISOLATED=1, TEST_WEB_DATABASE_URL (pg nativo) |
| HTTP/SSR | TEST_WEB_HTTP_DATABASE_URL, TEST_ADMIN_API_DATABASE_URL; bancos distintos |
| Keycloak API | TEST_KEYCLOAK_ENABLED/ISOLATED/GOVERNANCE=1, TEST_KEYCLOAK_ISSUER/API_URL, KEYCLOAK_ADMIN_USERNAME/PASSWORD |
| Keycloak BFF | TEST_KEYCLOAK_WEB_ENABLED=1, TEST_KEYCLOAK_WEB_ISSUER/ORIGIN/DATABASE_URL, TEST_KEYCLOAK_ADMIN_USERNAME/PASSWORD |
| Browser | TEST_WEB_BROWSER_ENABLED=1; TEST_WEB_CHROME_PATH opcional para harness manual |

O runner fornece também TEST_KEYCLOAK_CONTAINER. O caso de indisponibilidade no
Chrome verifica nome e label de propriedade antes de `docker pause`, força a
necessidade de refresh exclusivamente na sessão cifrada do banco de teste e
retoma o provedor no finally. Resultado incerto do refresh deve revogar a sessão,
mostrar novo login e impedir conteúdo protegido. Um harness manual sem essa
variável não executa a pausa; registrar essa limitação explicitamente.

Os comandos existentes continuam disponíveis em apps/web: `npm run
test:integration`, `npm run test:http`, `npm run test:keycloak`. Sem configuração
eles fazem skip; não executar isoladamente contra .env de trabalho. Para montar
manualmente ambiente equivalente, seguir [identidade web](identity-web.md) e
[Keycloak isolado](identity-keycloak-local.md), fornecendo variáveis acima e bancos
novos exclusivos. `pytest -c pyproject.toml ../../tests/integration` é o conjunto
API opcional; ausência de URLs ou flags produz skips explicitamente registrados.

## Checklist e resultados esperados

| Área | Aprovação | Reprovação / ação |
| --- | --- | --- |
| JWT/JWKS | válido aceito; assinatura/iss/aud/exp/nbf/iat/alg/kid/discriminador/azp inválidos → 401 Bearer genérico; cache/rotação/backoff limitados | qualquer acesso indevido, chave expirada usada ou vazamento bloqueia aceite |
| RBAC | seis papéis/combinações/17 permissões e operações por recurso; 403 autenticado sem permissão; admin sem bypass; contextos técnicos limitados | expansão de permissão por header/body/actor ou tipo de recurso incorreto bloqueia |
| OIDC | Code + S256/state/nonce/browser binding; ID token verificado; callback único, URI fixa; resposta incompleta/falha sem retry | sessão em callback rejeitado ou troca repetida bloqueia |
| Sessão/cookie | ID opaco rotacionado, cifra/AAD/keyring, HttpOnly/Lax/Path; Secure/__Host- HTTPS offline; expiração absoluta/refresh concorrente/logout/API 401 | tokens em browser/HTML/storage/URLs/logs, replay após revogação ou sessão anterior ativa bloqueia |
| CSRF/CORS | Origin/Host/CSRF; duplicatas/abuso recusados sem mutação; allowlist/métodos/headers/preflight inclusive erros | wildcard/credenciais indevidas ou logout cross-site bloqueia |
| CSP/HTTP | nonce distinto/SSR/Next hidratado, scripts sem nonce bloqueados, framing/nosniff/referrer/permissions/no-store; HSTS nas condições do contrato | enfraquecimento ou conteúdo protegido sem sessão bloqueia |
| Quotas/disponibilidade | PostgreSQL global entre pools, 429/Retry-After/recuperação; storage fail closed 503; refresh incerto revoga | fallback local/bypass/retry de code incerto bloqueia |
| Auditoria | envelope fechado UTC/UUID/ator confiável ou NULL/correlação; sentinelas ausentes; sink falho não concede privilégios | credenciais/PII em envelope, ator fabricado ou alteração M03 bloqueia |
| Persistência/M03 | migrações explícitas/adoção/rollback, CAS/revisões/NULL/proveniência/transações/publicada exata/draft isolado | mudança semântica, dado legado perdido ou base de trabalho usada bloqueia |
| Browser real | acesso direto anônimo negado; reader negado, cataloger autorizado pt/en; logout impede acesso; CSP intacta | teste HTTP sem browser não substitui essa linha |

Falha de provedor, sessão expirada e callback adulterado têm testes offline/HTTP
adicionais e percursos reais em browser.ts/keycloak.real.ts. O caso de expiração
altera o prazo absoluto cifrado e a coluna auxiliar no banco exclusivo; não é
medição de oito horas reais nem mudança do contrato. Leitor de tela,
TLS ingress real, carga/pentest e logs de proxy/collector requerem ensaios próprios.
Registrar como não executados até haver evidência; aprovação institucional exige
política de retenção, pessoas autorizadas, segredos, backups/TLS e riscos aceitos.

## Encerramento

O finally encerra somente API, Chrome/perfis e containers de nomes gerados pelo
ensaio. `docker stop` aciona `--rm`; dados em tmpfs são descartados. Não há volume
de trabalho a apagar. Cleanup falho retorna erro e exige inspeção dos nomes exatos
impressos pelo script. Não usar down -v, prune, remoção ampla ou reset de Git.

Em interrupção abrupta, identificar **somente os nomes/label desta execução** com
`docker ps -a --filter label=libris.verification=<nome-da-execução>` e parar seus
containers individualmente. Não parar containers de outro ensaio/mantenedor.
Manter os logs privados para diagnóstico ou remover somente o diretório /tmp
registrado após revisão. Perfis browser temporários são removidos no finally.

Comparar nomes/IDs dos containers e volumes preexistentes antes/depois. Finalizar
com status, HEAD, diff check/stat e diff staged vazio. Build pode atualizar
next-env.d.ts; preservar apenas conteúdo gerado necessário ou repor as linhas
iniciais registradas, sem descartar alterações do usuário. Separar aceite técnico
#42, homologação integrada local e aprovação institucional/produção.
