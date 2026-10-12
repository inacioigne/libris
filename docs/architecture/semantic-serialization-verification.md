# Verificação — M03.01.05 / issue #18

Data: 2026-10-12. Resultado técnico local, **não homologação institucional**.
Referência funcional: [issue #18](https://github.com/inacioigne/libris/issues/18),
lida integralmente, e tarefa anexada. Especificação [v1](semantic-serialization.md);
decisão [ADR 0020](../decisions/0020-jsonld-rdf-serialization.md).

## Diagnóstico e implementação

Checkout inicial main `c0a375d77404f006084635d681ddb0bf5b43feea`, limpo. Reutilizados
Graph nativo, new_graph/check_graph, parse_document/serialize_document/isomorphic,
ownership/composição, registro de relações, DTOs e identidades/resolução existentes.
Não havia mapeamento completo dos Read, contexto versionado ou função Accept.
A consulta paginada de branches visíveis no conector GitHub retornou somente main;
a busca por serialization retornou vazia. git ls-remote falhou em DNS. Nenhum
histórico, branch existente ou release de perfil foi sobrescrito.

Implementação acrescenta um pipeline Read→Graph para Work/Instance/Item/Agent/Subject,
exportação integral Graph→sintaxe, composição explícita, compactação limitada com
contexto local e negociação HTTP isolada. Separação de camadas preservada; domínio
não importa API/HTTP, serializers não importam ORM/FastAPI. A validação de IRI foi
movida sem mudar suas regras de common.py para domain/iris.py, reutilizada por RDF;
common.py continua expondo o import validate_iri para compatibilidade. check_graph
foi reforçado contra Dataset, IRI malformada, tipo literal e datatype IRI inválida.
A assinatura/saída expandida da persistência não foi alterada.

Mapeamentos incluem bf:Title/VariantTitle, Contribution(agent/role), Publication
(agent/place/date), Identifier/Local/Isbn, Extent, Note, Classification e ShelfMark.
Subject usa SKOS Concept, rótulos/esquema/hierarquia/associação; autoridades usam
rdfs:label/skos:altLabel/seeAlso, dcterms:relation e proveniência PROV. Nenhum sameAs
é inferido. Tabela completa de campos/objetos/datatypes/cardinalidades/ausência e
limitações está na especificação; testes afirmam triplas concretas por entidade.

URI raiz é exatamente a ReadIdentity.uri. UUID não vira atributo bibliográfico nem
sufixo recalculado. Mapa confiável de ResolvedEntity fornece referências locais;
UUID/URI/tipo inconsistentes e não reconciliadas são erros. Referências exteriores
mantêm a URI sem busca; namespace/external_id operacionais não recebem predicados
inventados. Descrições alheias não são incorporadas automaticamente.

## Inventário dos arquivos

Criados:

- `apps/api/src/libris/modules/bibliographic/domain/iris.py` — validador compartilhado.
- `apps/api/src/libris/modules/bibliographic/infrastructure/serialization/__init__.py` — API pública.
- `.../serialization/mapping.py` — cinco Read, auxiliares, referências e registro.
- `.../serialization/representation.py` — contexto, parsing da release, grafos e sintaxes.
- `.../serialization/negotiation.py` — mídia, qualidade, especificidade e erro 406.
- `apps/api/src/libris/modules/bibliographic/resources/contexts/bibframe-v1.jsonld` — contexto versionado.
- `tests/api/test_semantic_serialization.py` — testes independentes de serviços.
- `tests/fixtures/bibliographic/serialization/` — sete Read válidos, dezoito documentos
  inválidos e manifest de camada de rejeição; todos executados.
- `scripts/generate_serialization_examples.py` — gerador reproduzível a partir das fixtures.
- `docs/examples/serialization/` — 21 exemplos JSON/JSON-LD/Turtle (cinco entidades,
  Organization adicional, composição explícita) e README; todos os pares testados.
- `docs/decisions/0020-jsonld-rdf-serialization.md` — decisão/alternativas/consequências.
- `docs/architecture/semantic-serialization.md` — especificação, API, tabela, HTTP e evolução.
- Este relatório `docs/architecture/semantic-serialization-verification.md`.

Modificados: README.md (entrada da entrega), api/schemas/common.py (reutiliza
validador) e infrastructure/rdf.py (verificação de termos/grafo). Nenhuma dependência,
lock, migração, perfil/shape existente, código web ou rota pública foi alterado.

## Critérios de aceitação da issue #18

| Critério da issue | Classificação | Evidência |
| --- | --- | --- |
| Especificação versionável JSON-LD 1.1/RDF com formatos reais | Implementado | ADR 0020; semantic-serialization.md; CONTRACT_VERSION/CONTEXT_VERSION; somente json-ld/turtle |
| Contexto documentado e mapeamento dos cinco recursos | Implementado | bibframe-v1.jsonld; mapping.py; tabela completa; test_work_structure_and_all_fields, test_instance_structure_identifiers_publication_extent, test_item_structure_and_shelfmark_contract, test_agent_types_labels_and_external_links, test_subject_skos_hierarchy |
| Identificadores, relações, tipos, idiomas e referências preservados | Implementado no contrato descrito | test_local_references_resolve_exact_stored_identity; test_inconsistent_reference_mapping; test_five_resources_owned_equivalence_and_no_mutation; metadata externa sem correspondência explicada |
| Exemplos JSON-LD/RDF semanticamente equivalentes | Implementado | 21 exemplos; test_paired_examples_are_executable compara todos com Graph de origem |
| Conversão reproduzível e cenários válidos/inválidos/limites | Implementado | 118 testes novos; fixtures/manifest; gerador; isomorfismo em ambos os formatos |
| Mídia, negociação e erros documentados para FastAPI | Implementado no contrato; integração futura documentada | negotiation.py; test_negotiation/test_negotiation_not_acceptable/test_negotiation_available_formats_and_configured_default; especificação HTTP sem rotas novas |
| Extensível a ontologias, sem persistência/busca | Implementado pelo caminho Graph | test_direct_canonical_graph_preserves_extension_and_namespaces; IRIs explícitas conservadas; DTOs fechados preservados; #25 detalhada |
| Limites, decisões e dependências registradas | Implementado | ADR 0020, especificação e este relatório; #20/#21/#25/#30/#31 e homologação futura |

## Critérios adicionais de conclusão da tarefa

| Requisito | Classificação | Evidência específica |
| --- | --- | --- |
| Contexto versionado/documentado | Implementado | resources/contexts/bibframe-v1.jsonld; test_context_version_integrity_and_freshness, hash fixado |
| Conversão efetiva dos cinco Read | Implementado | resource_to_graph; sete fixtures válidas, incluindo Organization/Work mínima |
| Todos os campos mapeados ou limites explícitos | Implementado | mapping.py/tabela completa; metadados de reconciliação externos explicitamente operacionais |
| JSON-LD/Turtle do mesmo grafo | Implementado | serialize_resource chama resource_to_graph/serialize_graph; testes em FORMATS |
| Equivalência semântica | Implementado | parse seguro + isomorphic obrigatório; teste de recusa lexical evita sucesso falso |
| URIs persistidas preservadas | Implementado | URI raiz reutilizada; mudança de RESOURCE_BASE_URI no teste; Unicode em IRIs |
| Referências/auxiliares conservados | Implementado na superfície atual | Triplas específicas de Contribution/Publication/Identifier/Note/ShelfMark; resolvedor e rejeições |
| Sem equivalências fortes automáticas | Implementado | teste de ausência OWL.sameAs; rdfs:seeAlso; dcterms:relation |
| Caminho direto dos snapshots | Implementado | serialize_graph com root opcional; teste de predicados/datatype fora dos DTOs |
| Proteção contra contextos externos | Implementado | parser da release exige contexto exato; parser legado continua seguro; fixtures e bloqueio de acesso externo nos testes |
| Negociação HTTP reutilizável | Implementado | Accept específico/q/coringas/default/empate/exclusão/406 em negotiation.py |
| Fixtures válidas/inválidas | Implementado | serialization/valid, invalid, manifest; toda fixture inválida carregada |
| Exemplos pareados completos | Implementado | work/instance/item/agent/subject/organization/related em três formatos; gerador/teste |
| Cenários principais cobertos | Implementado | test_semantic_serialization.py: estruturas, multilinguismo, Unicode, datas, ausência, composição, segurança e HTTP |
| Documentação/ADR | Implementado | ADR 0020; especificação; relatório; README |
| Limites/verificações registrados | Implementado | Seções seguintes distinguem bloqueios ambientais, testes executados e trabalho futuro |
| Compatibilidade existente | Implementado e verificado | Suíte completa; funções RDF de persistência e perfis existentes preservados |

## Integrações documentadas e decisões adiadas

Implementado: representação dos campos Read, preservação integral de grafos que
sobrevivem ao round-trip, contexto v1, parsing seguro e negociação desacoplada.
Documentado para integração futura: handler FastAPI, Vary: Accept, 406/415,
resolução 303/200, ETags específicos por representação e escolha de revisões compostas.
Pendente fora do escopo: endpoints catalográficos/Linked Data, publicação institucional
do contexto/domínio, homologação, reconciliação/rascunhos, aliases/tombstones e
quotas de ingestão pública. RDF/XML, N-Triples, HTML e Dataset não implementados.

#20 aprofundará perfis; #21, validação SHACL; #25, mapeamentos de novas ontologias;
#30/#31, conformidade/versionamento institucional. Os perfis candidatos atuais foram
aplicados nos testes dos grafos DTO, sem modificar shapes e sem confundir essa
conformidade automatizada com homologação humana ou existência de alvos no banco.

Limites observados: contexto completo repetido por nó aumenta bytes; parser
continua rejeitando todo @graph; não há framing/JSON-LD 1.1 genérico. Ordem de listas
DTO não vira ordem RDF. Datatypes opacos não recebem validação lexical universal.
Datas e termos lexicais que RDFLib normaliza são recusados, não alterados.
Ciclos de blank nodes desconectados são omitidos pelo serializer JSON-LD de RDFLib:
a verificação de isomorfismo detecta e recusa; test_orphan_blank_cycle_refuses_lossy_jsonld.
Coleções RDF e ciclos ligados à raiz sobrevivem nos dois formatos. Não houve
integração PostgreSQL/Elasticsearch, benchmarks ou publicação HTTP.

## Verificações executadas

Ambiente: Python 3.13.15 da .venv existente, Node 24.16.0 instalado via nvm.
A tabela registra resultados finais; tentativas anteriores com falhas foram corrigidas
quando eram do novo código/testes, e limites ambientais estão separados abaixo.

| Comando / diretório | Resultado observado |
| --- | --- |
| `uv run pytest` / apps/api | Impedido por snap-confine; não executou pytest |
| `uv run ruff check . ../../tests` / apps/api | Impedido por snap-confine |
| `uv run mypy src` / apps/api | Impedido por snap-confine |
| `bash scripts/check.sh` / raiz | Parou no uv/Snap, exit 1; script agregado não passou |
| `.venv/bin/pytest ../../tests/api/test_semantic_serialization.py -q` / apps/api | **118 passed**, 55 avisos RDFLib; 3,19 s |
| `.venv/bin/pytest` / apps/api, execução final fora do sandbox | **595 passed**, 329 avisos; 27,62 s; inclui todos os testes anteriores |
| `.venv/bin/ruff check . ../../tests ../../scripts/generate_serialization_examples.py` / apps/api | **All checks passed** |
| `.venv/bin/mypy src` / apps/api | **Success**, 49 arquivos, strict |
| `apps/api/.venv/bin/python scripts/generate_serialization_examples.py` / raiz | 21 exemplos gerados; testes conferem sua equivalência aos DTOs/composição |
| `npm run build` / apps/web, Node 24 no PATH, fora do sandbox | **Passou**, build Next.js 16.4.0 com webpack; páginas /, /pt, /en e not-found |
| `npm run typecheck` / apps/web, mesmo Node | **Passou**, tsc --noEmit |
| `docker compose --env-file .env.example config --quiet` / raiz | **Passou**, configuração somente; não iniciou serviços |
| `git diff --check` / raiz | **Passou** |

Os três comandos uv e check.sh emitiram a recusa snap-confine por confinamento
AppArmor/Snap; não foram apresentados como verificações bem-sucedidas. As partes
do script foram executadas separadamente com .venv, Node instalado e Docker Compose.
A execução pytest dentro do sandbox travou em TestClient/streams e foi interrompida;
fora dessa restrição a suíte completa concluiu. O primeiro build web dentro do
sandbox falhou ao interpretar TypeScript --showConfig; fora do sandbox passou,
sem alterar código web ou dependências. Não houve rejeição de aprovação automática.

Os avisos são deprecações Starlette/httpx e RDFLib/ConjunctiveGraph já presentes nas
bibliotecas usadas; novos round-trips exercitam o mesmo aviso RDFLib. Não foram
suprimidos. Não há falha preexistente de testes a relatar na suíte final executada.
PostgreSQL/Elasticsearch não foram necessários; testes de integração não foram
executados e não há alegação de prontidão dos serviços ou homologação institucional.

Resultado: os oito critérios da issue estão implementados no contrato técnico
explicitamente delimitado, com integrações futuras e limitações registradas.
Alterações permanecem locais no checkout, sem commit/push/PR/merge automático.
A issue #18 não foi encerrada. Publicação institucional continua dependente das
políticas futuras; este relatório serve como evidência técnica para revisão.
