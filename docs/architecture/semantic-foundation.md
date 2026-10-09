# Fundação semântica — Etapa 2

Implementado em `apps/api/src/libris/modules/bibliographic/`:

- `domain/models.py`: UUID/URI estáveis, revisão, proveniência e conflito de revisão.
- `infrastructure/rdf.py`: Graph RDFLib, namespaces extensíveis, parsing limitado,
  exportação com teste de isomorfismo e relações inversas BIBFRAME.
- `infrastructure/validation.py`: SHACL local e relatório estruturado.
- `infrastructure/persistence.py`: SQLAlchemy async, snapshots JSONB e CAS de revisão.
- `application/service.py`: criação, nova revisão e recuperação; transações próprias.
- `resources/monograph-v1.{json,ttl}`: perfil de formulário e shapes independentes.
- `__main__.py`: diagnóstico/exportação local sem gravação em banco.

O núcleo utiliza Graph nativamente: chamar `graph.add((subject, predicate, object))`
para novas propriedades/ontologias. URIRef, BNode e Literal são termos distintos.
`new_graph` vincula bf, dcterms, skos e prov, sem whitelist de ontologias. Título
é um bf:Title com bf:mainTitle, publicação é bf:Publication, ISBN é bf:Isbn com
rdf:value; ISBN não substitui UUID/URI. O Item descrito é bibliográfico, sem estado
administrativo, empréstimos ou dados de leitores. Fixtures usam apenas dados sintéticos.

O formato declarativo lista classes de formulário, propriedades, rótulos em
português, repetibilidade, tipos de campo, classes de destino e vocabulários externos.
`requiredInForm` orienta futuros formulários e não executa validação. As shapes são
a autoridade para conformidade institucional e continuam abertas a extensões.
O perfil pode exigir relações descritas no mesmo grafo; URIs externas em assunto,
agentes e outras propriedades são preservadas sem consulta à rede.

`validate_monograph` distingue `conforms`, SHACL Warning, Info e Violation e conserva
o relatório RDF. Warning/Info não bloqueiam; Violation bloqueia o serviço. Um grafo
RDF válido pode não cumprir o perfil. SHACL usa targets: um grafo vazio tem conformidade
vazia; o serviço de persistência exige também uma raiz com classe BIBFRAME suportada.
Não há inferência nem validação de todo o vocabulário BIBFRAME, ISBN ou vocabulários
controlados externos. Não carregar shapes ou regras enviadas junto dos dados.

## Identidade e persistência

Configure `RESOURCE_BASE_URI` antes de criar recursos. O default localhost é
provisório e não fornece endpoint resolvível. Use
`ResourceIdentity.create(str(Settings().resource_base_uri))`. Guarde a URI retornada
na criação. Uma mudança de ambiente não altera URIs de registros existentes.
Identificadores externos mantêm as URIs originais.

`BibliographicService.create(identity, graph, Provenance(source, process))` gera
revisão 1; `revise(id, expected_revision, graph, provenance)` cria revisão seguinte;
`read(id)` retorna atual e `read(id, number)` retorna revisão histórica e Graph.
O chamador fornece a identidade antes de construir o grafo com a URI raiz.
Cada snapshot contém o grafo completo; neste ensaio a raiz Work agrega as três
entidades. Não salvar separadamente grafos sobrepostos esperando merge automático.
Revisões registram instante UTC, origem, processo e perfil versionado. As tabelas
não contêm identidade humana nem representação PROV-O completa.

```python
from libris.core.config import Settings
from libris.infrastructure.database import Database
from libris.modules.bibliographic.application.service import BibliographicService
from libris.modules.bibliographic.domain.models import Provenance, ResourceIdentity

settings = Settings()
identity = ResourceIdentity.create(str(settings.resource_base_uri))
# Construa graph com identity.uri como raiz tipada e título compatível com o perfil.
database = Database(settings)
service = BibliographicService(database.sessions)
# Em uma função async:
# revision = await service.create(identity, graph, Provenance("fixture:local", "manual:test"))
# revision, recovered_graph = await service.read(identity.internal_id)
# await database.close()
```

Veja [ADR 0007](../decisions/0007-semantic-core.md) e
[ADR 0008](../decisions/0008-experimental-rdf-persistence.md) para escolhas e alternativas.

## Exemplos reais e comandos

A fixture `tests/fixtures/bibliographic/book.ttl` contém 49 triplas: Work, Instance,
Item, contribuição fictícia, título pt/en, dois assuntos, idioma, publicação,
identificador, datatype gYear, blank nodes e exemplos DCTERMS/SKOS. Exportações
produzidas pela ferramenta estão em [Turtle](../examples/book.ttl) e
[JSON-LD expandido](../examples/book.jsonld). O teste compara por isomorfismo,
não texto ou nomes de blank nodes.

Da raiz:

```bash
cd apps/api
uv sync --locked
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
uv run python -m libris.modules.bibliographic \
  ../../tests/fixtures/bibliographic/book.ttl --output-dir /tmp/libris-rdf
uv run python -m libris.modules.bibliographic \
  /tmp/libris-rdf/book.jsonld --format json-ld
uv run alembic heads
uv run alembic upgrade head --sql
```

Para integração use **banco PostgreSQL dedicado descartável**, nunca SQLite. Os
testes criam registros com UUID novo e preservam o histórico no banco de teste.
Não apontar `TEST_DATABASE_URL` ao banco de trabalho ou produção.

```bash
# Exemplo: container sem volumes, porta livre diferente dos serviços de trabalho.
docker run -d --name libris-semantic-test \
  -e POSTGRES_PASSWORD=semantic-disposable -e POSTGRES_DB=libris_test \
  -p 127.0.0.1:55439:5432 postgres:17-bookworm
# Aguarde pg_isready antes de migrar.
docker exec libris-semantic-test pg_isready -U postgres -d libris_test
export DATABASE_URL=postgresql+asyncpg://postgres:semantic-disposable@localhost:55439/libris_test
export TEST_DATABASE_URL="$DATABASE_URL"
uv run alembic upgrade head
uv run alembic check
uv run pytest -c pyproject.toml ../../tests/integration -m integration
# Verifica reversibilidade SOMENTE no banco descartável; descarta dados experimentais.
uv run alembic downgrade base
uv run alembic upgrade head
docker rm -f libris-semantic-test
```

Sem `TEST_DATABASE_URL`, integração é pulada explicitamente. A suíte padrão em
`tests/api` não necessita PostgreSQL/Elasticsearch. `scripts/check.sh` executa a
suíte padrão, qualidade Python, build/tipos web e Compose. Não adicionamos endpoints:
`/health` mantém somente liveness e OpenAPI permanece com a mesma rota.

## Limitações conhecidas

O adaptador aceita Turtle e JSON-LD expandido ou compacto com objetos de contexto
embutidos. Bloqueia URLs/listas de contextos, imports, reverse e qualquer `@graph`,
inclusive wrappers de grafo padrão. Não aceita datasets/named graphs ou RDF-star.
Entrada JSON-LD tem profundidade máxima 64 e limite em bytes configurável; arquivos
locais da CLI são lidos até limite+1 antes do parsing. Propriedades desconhecidas
com URI continuam sendo dados e não instruções executáveis.

RDFLib pode normalizar lexicais de literais numéricos durante parsing. O objetivo é
fidelidade semântica do grafo, não fidelidade textual do documento. Termos construídos
manualmente que mudam no round-trip são rejeitados; literais malformados conhecidos
são rejeitados. Datatypes desconhecidos permanecem opacos. JSONB não representa
U+0000 e o serviço o rejeita sem gravação. Contextos embutidos não são um catálogo
remoto controlado: o perfil local orienta futuras interfaces, sem downloads.

O limite e o isomorfismo não substituem isolamento e quotas de CPU para futuros
endpoints de ingestão expostos. Não há escrita HTTP pública, autenticação,
indexação, benchmarks, editor, MARC ou domínio público escolhido. Migrações são
experimentais; a reversão apaga suas tabelas. RDFLib e Starlette emitem avisos de
depreciação conhecidos nos testes; não foram suprimidos nem resolvidos alterando
bibliotecas fora do escopo.

Para a Etapa 3, validar um perfil institucional com catalogadores, definir limites
de agregados Work/Instance/Item, estabelecer autenticação/autorização e política de
resolução das URIs antes de criar APIs de escrita ou um editor mínimo.
