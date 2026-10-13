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
autoridades e pesquisa ainda não estão implementados. A Entrega A do Incremento 2
implementa [autenticação/autorização OIDC](docs/architecture/identity.md),
`/api/v1/identity/me` e ator opcional nas revisões, sem login no frontend.

Consulte a [fundação semântica](docs/architecture/semantic-foundation.md) para
exemplos, serviços internos, limites e testes de integração PostgreSQL.

A Etapa 3, Incremento 1 consolida o [contrato catalográfico](docs/architecture/catalogographic-contract.md):
release candidata monograph-v1.1, perfil complementar de autoridades, snapshots
proprietários e revisões independentes, preservando o perfil experimental legado.
Ver [diagnóstico](docs/architecture/catalogographic-contract-diagnosis.md),
[ADRs 0009–0015](docs/decisions/) e
[relatório de verificação](docs/architecture/catalogographic-contract-verification.md).
A homologação institucional permanece pendente; não há novos endpoints ou editor.
A M03.01.02 acrescenta [contratos públicos Pydantic v2](docs/architecture/catalogographic-schemas.md)
para Work, Instance, Item, Agent e Subject, com Create/Read/Update e testes OpenAPI
isolados; as APIs de catalogação continuam pendentes.
A M03.01.03 acrescenta o [contrato de relacionamentos](docs/architecture/relationships.md):
referências locais, externas e não reconciliadas, matriz semântica, operações
explícitas de vínculos e validação de integridade com resolvedor desacoplado.
Ver [evidências e critérios](docs/architecture/relationships-verification.md).
A M03.01.04 consolida a [estratégia de identificadores persistentes](docs/architecture/persistent-identifiers.md):
UUIDv4 e URI armazenada, referências compatíveis, ciclo de vida, importação e
resolução HTTP futura. Ver [ADR 0019](docs/decisions/0019-persistent-identifiers.md)
e [verificação](docs/architecture/persistent-identifiers-verification.md).

A M03.01.05 implementa a [representação semântica v1](docs/architecture/semantic-serialization.md):
mapeamento dos cinco Read para Graph, JSON-LD com contexto local versionado, Turtle,
exportação integral de snapshots e negociação Accept desacoplada. Ver
[ADR 0020](docs/decisions/0020-jsonld-rdf-serialization.md),
[exemplos pareados](docs/examples/serialization/) e
[verificação](docs/architecture/semantic-serialization-verification.md).
Não há novos endpoints ou homologação institucional.


A M03.02.01 acrescenta o [contrato de perfis declarativos 2.0](docs/architecture/catalog-profiles.md):
configurações Pydantic/JSON, herança por release, seleção determinística, registro
semântico local e associação SHACL versionada, preservando todos os perfis históricos.
Ver [ADR 0021](docs/decisions/0021-declarative-catalog-profiles.md),
[exemplos](docs/examples/profiles/) e [verificação](docs/architecture/catalog-profiles-verification.md).
O contrato prepara formulários futuros; não acrescenta CRUD, editor ou tabelas.

A M03.02.02 consolida a [validação SHACL](docs/architecture/shacl-validation.md):
registro local por release/contexto, diagnóstico RDF completo, distinção de falhas e
políticas suplementares para perfis 2.0, preservando as fontes históricas.
Ver [inventário](docs/architecture/shacl-inventory.md),
[ADR 0022](docs/decisions/0022-shacl-profile-policies.md) e
[evidências](docs/architecture/shacl-validation-verification.md).

A M03.02.03 implementa [diagnósticos e erros catalográficos 1.0](docs/architecture/catalogographic-errors.md):
contratos Pydantic, códigos estáveis, adaptação SHACL/perfis, correlação por request ID
e Problem Details na aplicação FastAPI. Rejeições persistentes carregam diagnósticos,
preservando transações e perfis históricos. Ver [ADR 0023](docs/decisions/0023-catalogographic-diagnostics.md)
e [verificação](docs/architecture/catalogographic-errors-verification.md).
Pré-validação HTTP, ETags de edição e editor continuam futuros.

A M03.03.01 acrescenta o [contrato de valores controlados e vocabulários](docs/architecture/controlled-vocabularies.md):
valores discriminados 1.0, conceitos locais/externos, evidência de pertença, estados,
provedores desacoplados e política de cache, com exemplos RDF/JSON-LD verificáveis.
Ver [ADR 0024](docs/decisions/0024-controlled-vocabularies.md) e
[verificação](docs/architecture/controlled-vocabularies-verification.md).
Não há conectores remotos, cache persistente ou adoção automática nos DTOs históricos.

A M03.03.02 implementa [extensibilidade semântica governada](docs/architecture/semantic-extensions.md):
registro semântico 2.0 fixado por release, autorização de classes/propriedades e
perfil candidato BIBFRAME + Dublin Core Terms, com exemplos RDF/JSON-LD sem perdas.
Ver [ADR 0025](docs/decisions/0025-semantic-extensions.md) e
[verificação](docs/architecture/semantic-extensions-verification.md).
Os registros/perfis históricos e os DTOs permanecem preservados; não há novas rotas.

A M03.04.01 implementa o [contrato de estados editoriais](docs/architecture/editorial-lifecycle.md):
matriz fechada, permissões explícitas, publicação validada, revisão candidata separada
da publicação anterior e ciclo independente da identidade. Ver
[ADR 0026](docs/decisions/0026-editorial-lifecycle.md).
A coordenação exige adaptador transacional futuro; não há persistência editorial,
integração à escrita semântica ou auditoria durável nesta entrega.


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

Existem as revisões experimentais `0001_semantic` e `0002_revision_actor`. `alembic current` exige banco
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

Homologar os perfis candidatos com catalogadores e implementar a API de catalogação
no Incremento 2, conforme o contrato consolidado de entidades, URIs, referências
e concorrência. Autenticação/autorização OIDC está implementada na Entrega A; auditoria humana
completa e entregas B–E continuam pendentes.
As tabelas permanecem experimentais; não há esquema bibliográfico definitivo.
Ver [contrato](docs/architecture/catalogographic-contract.md) e ADRs 0009–0015.

A licença do Libris ainda precisa ser escolhida pelos mantenedores; não foi
adicionada uma licença arbitrária. Avaliar também os termos das distribuições
Elasticsearch antes de redistribuição. Para orientação FastAPI atualizada opcional,
`uvx library-skills` instala skills interativamente a partir das dependências;
escolha o agente usado no projeto quando solicitado.
