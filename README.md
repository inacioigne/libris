# Libris

Base inicial de um sistema integrado de gestão de bibliotecas com BIBFRAME 2.0,
RDF e Linked Data. Monólito modular FastAPI, frontend Next.js App Router,
PostgreSQL transacional e Elasticsearch para descoberta futura. A base visual usa
Tailwind e uma primitiva acessível Radix UI; a adoção de shadcn/ui para controles
complexos está registrada no ADR 0005.

**Implementado:** `/health`, página inicial `/pt` e `/en`, configuração validada,
engine/sessões SQLAlchemy assíncronas, Docker Compose e núcleo semântico experimental
BIBFRAME/RDF. A Etapa 2 inclui JSON-LD/Turtle, perfil monográfico, SHACL, UUID/URI,
snapshots JSONB, revisões e concorrência otimista. Há uma migração Alembic
experimental; ela não executa no startup. Editor, APIs de catalogação, circulação,
autoridades, pesquisa e autenticação ainda não estão implementados.

Consulte a [fundação semântica](docs/architecture/semantic-foundation.md) para
exemplos, serviços internos, limites e testes de integração PostgreSQL.

## Estrutura

```text
apps/
  api/
    src/libris/{api,core,infrastructure,modules}/
    migrations/versions/
    pyproject.toml, uv.lock, alembic.ini
  web/
    src/app/[locale]/
    src/i18n/
    package.json, package-lock.json
packages/shared/
infrastructure/docker/
docs/architecture/
docs/decisions/
scripts/check.sh
tests/api/
docker-compose.yml
.env.example
AGENTS.md
```

Leia [visão arquitetural](docs/architecture/overview.md),
[domínios](docs/architecture/domains.md),
[modelo bibliográfico](docs/architecture/bibliographic-model.md) e
[ADRs](docs/decisions/) antes de implementar módulos.

## Executar com Docker

Requisitos: Docker Engine com Compose, acesso ao daemon e conexão para baixar
imagens/dependências. Reserve inicialmente cerca de 4 GB de RAM disponíveis para
o conjunto; ajuste conforme o ambiente.

```bash
cp .env.example .env
# Edite .env: escolha uma senha local e atualize DATABASE_URL com a mesma senha.
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs -f api web
```

Acesse:

- Frontend: http://localhost:3000 (redireciona para `/pt`; inglês em `/en`).
- API: http://localhost:8000/health
- OpenAPI: http://localhost:8000/docs
- Elasticsearch: http://localhost:9200
- PostgreSQL: localhost:5432

As portas podem ser alteradas no `.env`. Ajuste `CORS_ORIGINS` se mudar a porta
do frontend. Dentro do Compose use hosts `postgres`, `elasticsearch` e `api`,
independentemente das portas publicadas. `API_INTERNAL_URL` está reservado para
futuras chamadas no servidor Next.js; a página atual não consulta a API.

A senha do exemplo é descartável e pública. O Compose é exclusivamente local,
publica portas em `127.0.0.1` e desativa segurança do Elasticsearch. Não usar essa
configuração como implantação de produção. Configurar credenciais, TLS, backups e
rede apropriados antes de implantação real. `POSTGRES_PASSWORD` só inicializa um
volume novo; alterá-la no `.env` não troca a senha de um banco já existente.

Se Elasticsearch registrar erro de `vm.max_map_count`, consulte o requisito do
host em [documentação Elastic](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-docker-prod).
Não altere configurações do kernel sem considerar o ambiente hospedeiro.

```bash
docker compose stop        # preserva volumes
docker compose down        # remove containers/rede, preserva dados
# docker compose down -v   # DESTRUTIVO: apaga dados locais; execute só se desejado
```

## Desenvolvimento com ferramentas locais

Instale [uv](https://docs.astral.sh/uv/getting-started/installation/) e Node.js 24 LTS
(com npm). Python de referência é 3.13; uv pode obtê-lo automaticamente. Mantenha os locks
sob controle de versão; não inclua a pasta `.venv` nem `node_modules`.

```bash
cp .env.example .env
# Para aplicações fora do Docker, altere no .env:
# DATABASE_URL=postgresql+asyncpg://libris:SUA_SENHA@localhost:5432/libris
# ELASTICSEARCH_URL=http://localhost:9200
# API_INTERNAL_URL=http://localhost:8000
docker compose up -d postgres elasticsearch
cd apps/api
uv sync --locked
uv run fastapi dev --host 0.0.0.0
```

Em outro terminal:

```bash
cd apps/web
npm ci
npm run dev
```

O backend lê `.env` da raiz quando executado em `apps/api`; variáveis do processo
prevalecem. A saúde pode funcionar sem PostgreSQL/Elasticsearch, pois não abre
conexão no startup; isso é intencional e não comprova readiness dos serviços.

## Testes e verificações

```bash
cd apps/api
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
uv run alembic heads
uv run alembic upgrade head --sql
```

Existe a revisão experimental `0001_semantic`. `alembic current` exige banco
acessível; `heads` e geração offline inspecionam o ambiente sem modificar o banco.
Execute `uv run alembic upgrade head` explicitamente quando desejar instalar as
tabelas experimentais. O downgrade descarta seus dados.

```bash
cd apps/web
npm run build
npm run typecheck
```

Na raiz, `bash scripts/check.sh` reúne os testes, análise de tipos, build e
validação do Compose. Para testar dentro da imagem API, que não contém dependências
de desenvolvimento por padrão:

```bash
docker compose run --rm --user root -v "$PWD/tests:/tests:ro" api \
  sh -c 'uv sync --locked --group dev && uv run pytest /tests/api'
```

Esse comando instala ferramentas somente no container descartável e precisa de
rede. A suíte padrão cobre lifespan/saúde sem serviços externos, contrato OpenAPI,
CORS, configuração, RDF e SHACL. A suíte separada de integração verifica snapshots,
histórico e concorrência em PostgreSQL real; não há integração com índices. Evidências desta sessão estão em
[verification.md](docs/architecture/verification.md).

## Próxima etapa

Validar o perfil com catalogadores, definir limites dos agregados Work/Instance/Item,
política de resolução das URIs e autenticação/autorização antes de criar APIs de
escrita e editor mínimo. As tabelas permanecem experimentais; não há esquema
bibliográfico definitivo. Ver [ADR 0007](docs/decisions/0007-semantic-core.md) e
[ADR 0008](docs/decisions/0008-experimental-rdf-persistence.md).

A licença do Libris ainda precisa ser escolhida pelos mantenedores; não foi
adicionada uma licença arbitrária. Avaliar também os termos das distribuições
Elasticsearch antes de redistribuição. Para orientação FastAPI atualizada opcional,
`uvx library-skills` instala skills interativamente a partir das dependências;
escolha o agente usado no projeto quando solicitado.
