# Representação semântica — M03.01.05 / issue #18

Contrato **1.0**; contexto **bibframe-v1**; implementação técnica, sem homologação
institucional. [ADR 0020](../decisions/0020-jsonld-rdf-serialization.md).
JSON operacional e DTO Read não substituem Graph RDFLib canônico.

## Diagnóstico do checkout

HEAD inicial `c0a375d77404f006084635d681ddb0bf5b43feea`, branch main, sem alterações
locais. A issue #18 foi lida integralmente pelo conector GitHub. Convenções, README,
pyproject, check.sh, arquitetura indicada, ADRs 0007/0012–0015/0017–0019, schemas,
serviços, ownership, adaptador RDF, perfis/SHACL e fixtures existentes foram examinados.
As referências locais main e feat/m03-01-02-catalogographic-schemas não continham
serializador de DTOs/contexto versionado/negociação. Git ls-remote não conseguiu
resolver github.com; consulta pelo conector não encontrou branch com serialization.
A listagem remota pelo conector foi paginada até o fim e retornou somente main.
Isso cobre as branches visíveis à conexão, sem afirmar acesso a trabalho não publicado.
Não houve fetch, merge, push ou encerramento de issue.

Reutilizáveis: new_graph/check_graph, parsing limitado, serialize_document com
isomorfismo, check_snapshot/compose_snapshots, DEFAULT_REGISTRY, ReadIdentity,
ResourceIdentity, ResolvedEntity e os cinco Read. Lacunas: mapeamento explícito,
contexto de saída, caminho de publicação integral distinguido dos DTOs e Accept.
Decisão necessária: reconciliar saída compacta com rejeição de @graph sem mudar
persistência; usar compactação limitada de arrays e contexto em cada nó.

## Evolução M05.02

Os [adaptadores DTO ↔ RDF](catalogographic-dto-rdf-adapters.md) acrescentam Create,
projeção Graph → Read e Update parcial sobre cópia do snapshot completo. O writer
abaixo é reutilizado; limites de projeção e preservação integral estão nesse contrato.

## API pública

Importar `libris.modules.bibliographic.infrastructure.serialization`:

```python
from libris.modules.bibliographic.infrastructure.serialization import (
    resource_to_graph, serialize_resource, serialize_graph,
    serialize_composed, parse_representation, negotiate_format,
)

# resource é WorkRead, InstanceRead, ItemRead, AgentRead ou SubjectRead.
graph = resource_to_graph(resource, references=stored_references)
jsonld = serialize_resource(resource, format="json-ld", references=stored_references)
turtle = serialize_graph(graph, format="turtle", root=resource.uri)
restored = parse_representation(jsonld, "json-ld")

# Snapshot vindo do serviço: exportação integral, sem reduzir a DTO.
full_document = serialize_graph(canonical_snapshot, format="json-ld", root=stored_uri)
# O chamador escolhe cada raiz/revisão. A função não consulta entidades.
composed = serialize_composed(selected_snapshots, format="turtle")
selected = negotiate_format(accept_header)  # default REST: json
```

| Operação | Entrada / saída | Garantia |
| --- | --- | --- |
| resource_to_graph | ResourceRead; references opcional → Graph | Revalida DTO, mapeia campos cobertos, verifica snapshot proprietário |
| serialize_resource | ResourceRead; format json-ld/turtle → str | Mesmo pipeline Graph; não exporta propriedades fora do DTO |
| serialize_graph | Graph; format; root opcional → str | Exporta grafo integral; root exige ownership/tipo; sem root aceita grafo explicitamente composto |
| serialize_composed | Iterable[tuple[URIRef, Graph]]; format → str | Reutiliza compose_snapshots; raízes distintas, auxiliares privados, blank nodes renomeados e inversas derivadas |
| parse_representation | str; format; limit opcional → Graph | Política de contexto da release e adaptador seguro; nenhuma consulta remota |
| local_context / context_digest | Sem argumentos → dict novo / SHA-256 | Contexto confiável do pacote, não configuração de clientes |
| negotiate_format | Accept opcional; available/default → RepresentationFormat | Decisão isolada; NotAcceptable equivale a HTTP 406 |

`ReferenceMapping = Mapping[UUID | str, ResolvedEntity]`. Cada chave é UUID interno
ou URI exata armazenada; aliases não são inferidos. A aplicação pode resolver com
ReferenceResolver dentro de sua transação e fornecer os resultados ao serializador
síncrono. Para URI-only, fornecer a chave URI; para UUID-only, a chave UUID. Quando
ambas as chaves estiverem presentes no mapa, seus resultados devem ser iguais.
UUID+URI na referência deve concordar com o par retornado, mesmo que apenas uma
chave tenha resultado. A raiz Read é um par já armazenado; o serializador valida
sua estrutura, sem extrair UUID da URL ou comprovar existência no banco.

Falhas estruturais são ValidationError; RDF/mapeamento/parser/round-trip usam
RdfDocumentError (ValueError); ownership pode produzir ValueError. Sem mutações
em DTOs, triplas ou namespaces dos grafos fornecidos. serialize_document legado
continua com assinatura/array expandido usados na persistência; a compactação
é exclusiva do novo caminho de representação.

## Contexto, formato e segurança

Artefato: `apps/api/src/libris/modules/bibliographic/resources/contexts/bibframe-v1.jsonld`.
@version=1.1, namespaces bf/rdf/rdfs/skos/dcterms/prov/xsd e termos explícitos.
Referências têm @type=@id; textos não recebem coerção de IRI. Sem @vocab, @import,
contexto remoto, base alterável ou aliases de palavras reservadas perigosas.

A saída é array de nós, cada um com contexto local inteiro. A compactação altera
somente nomes de predicados conhecidos. @id, @type, @value, @language, datatype e
estruturas @list eventualmente produzidas para coleções RDF existentes são mantidos.
Textos como "@graph" continuam dados. Não há framing, language maps, @reverse,
@direction, @json, contextos escopados arbitrários ou suporte genérico a JSON-LD 1.1.
Qualquer @graph, inclusive wrapper do grafo padrão, continua rejeitado; named graphs
exigiriam Dataset e contrato separado. Arrays contêm declarações de um único Graph.

parse_representation admite forma expandida sem contexto ou o contexto exato da
release. Termo compacto sem contexto ou desconhecido falha; uma IRI de predicado
explícita desconhecida é preservada como extensão RDF. Nenhuma entrada redefine
contextos de saída. O adaptador legado parse_document mantém seu contrato de
contextos objetos locais; não é automaticamente o validador de contexto desta release.

O contexto vem somente do pacote via importlib.resources, sem paths fornecidos
pelo cliente. Não há cache mutável compartilhado: cada chamada lê uma cópia.
Integridade por SHA-256 de JSON canônico (sort_keys, UTF-8, separators compactos):
`bfefbcf7a9db2811487d174879dcf311c066a935807cf661b805dd19f7482f16`.
Teste fixa o digest. Publicação futura pode oferecer URL institucional versionada
imutável com cache e hash; o parser não passará a buscá-la automaticamente. Novo
contexto ou interpretação incompatível exige novo arquivo/versão; não editar v1.

Entrada e exportação usam RDF_MAX_DOCUMENT_BYTES (default 1 MiB, máximo configurado
10 MiB). O limite conta UTF-8, inclusive repetição de contexto. JSON tem profundidade
máxima 64; cadeia de auxiliares no grafo também é limitada, sem travessia HTTP.
Ciclos RDF não provocam expansão infinita; ausência global de ciclos de relações
bibliográficas continua responsabilidade da aplicação com closure explícita.
O parser também recusa propriedades JSON duplicadas, documentos escalares e objetos
de valor incompatíveis, evitando descartes silenciosos. check_graph rejeita Dataset,
termos RDF inválidos, rdf:type sem classe por IRI,
IRIs relativas/malformadas, datatype com IRI inválida e literais ill_typed conhecidos.
Datatypes não conhecidos pela biblioteca são opacos e preservados, sem afirmar
validação lexical universal. Nenhum arquivo, URL, ontologia ou import é resolvido.

## Mapeamento completo da superfície Read

Fonte executável: `infrastructure/serialization/mapping.py`. As relações entre
entidades reutilizam campo/predicado/caminho/classe do DEFAULT_REGISTRY.
A tabela é o mapeamento de campos Pydantic, não uma segunda ontologia.

Convenções comuns a **todas** as linhas: campos 0..* ausentes/listas vazias omitem
triplas; obrigatórios ausentes/invalidos falham na revalidação Pydantic. Coleções
são declarações RDF sem ordem; duplicatas da mesma tripla colapsam. Cada auxiliar
declarado tem blank node próprio com rdf:type; auxiliares de snapshots preexistentes
podem ser URI-raiz#fragmento. Não há URI pública auxiliar inventada. Literais T
preservam Unicode/grafia e idioma declarado (rdf:langString); sem idioma são literais
simples (xsd:string na semântica RDF 1.1). Literais S são strings sem idioma;
PublicationDate tem datatype explícito. Todos os predicados têm origem no contrato
Pydantic correspondente, especificado na coluna Campo. Limitações por linha somam-se
às políticas comuns descritas nesta seção.

| Proprietário / classe RDF | Campo Pydantic | Predicado / objeto | Cardinalidade | Tipo/datatype e limitação |
| --- | --- | --- | --- | --- |
| Todos Read | uri | Sujeito/@id, URI armazenada | 1 | HTTP(S), sem reconstrução |
| Todos Read | internal_id | Nenhuma tripla | 1 operacional | UUID técnico, usado somente na resolução |
| Work / bf:Work | title | bf:title → auxiliar Title/VariantTitle | 1..* | Ao menos um Title |
| Work | language | bf:language → URI | 0..* | Vocabulário, sem dereferência |
| Work | content | bf:content → URI | 0..* | Vocabulário |
| Work | contribution | bf:contribution → bf:Contribution | 0..* | Nó intermediário obrigatório se declarado |
| Work | subject | bf:subject → URI de Subject | 0..* | Não inclui descrição/tipo do alvo |
| Work | classification | bf:classification → bf:Classification | 0..* | Auxiliar |
| Work | related_to | bf:relatedTo → URI Work | 0..* | Sem escrita simétrica automática |
| Work | translation_of | bf:translationOf → URI Work | 0..* | Sem derivar bf:translation |
| Work | note | bf:note → bf:Note | 0..* | Auxiliar |
| Instance / bf:Instance | instance_of | bf:instanceOf → URI Work | 1 | Não escreve hasInstance no pai |
| Instance | title | bf:title → Title/VariantTitle | 0..* | Não copia título Work |
| Instance | edition_statement | bf:editionStatement → T | 0..* | Edição bibliográfica, não revisão |
| Instance | provision_activity | bf:provisionActivity → bf:Publication | 0..* | Agrupa agentes/lugares/datas |
| Instance | identified_by | bf:identifiedBy → Identifier/Local/Isbn | 0..* | Auxiliar; sem checksum |
| Instance | extent | bf:extent → bf:Extent | 0..* | Auxiliar |
| Instance | carrier | bf:carrier → URI | 0..* | Vocabulário |
| Instance | note | bf:note → bf:Note | 0..* | Auxiliar |
| Item / bf:Item | item_of | bf:itemOf → URI Instance | 1 | Não escreve hasItem no pai |
| Item | identified_by | bf:identifiedBy → Identifier/Local/Isbn | 1..* | Ao menos Local; não é identidade de entidade |
| Item | held_by | bf:heldBy → URI Agent | 0..* | Organization é regra de integridade/perfil; sem circulação |
| Item | note | bf:note → bf:Note | 0..* | Auxiliar |
| Item | custodial_history | bf:custodialHistory → T | 0..* | Texto bibliográfico |
| Item | shelf_mark | bf:shelfMark → bf:ShelfMark | 0..* | Não substitui por itemLocation |
| Item | provenance | prov:wasDerivedFrom → URI | 0..* | Fonte semântica, não ator técnico |
| Agent / bf:Agent, bf:Person, bf:Organization | kind | rdf:type → classe bf correspondente | 1 | Somente os três tipos atuais |
| Agent | authorized_name | rdfs:label → T | 1..* | Uma forma por idioma |
| Agent | variant_name | skos:altLabel → T | 0..* | Preserva idioma |
| Agent | identified_by | bf:identifiedBy → Identifier/Local/Isbn | 0..* | Auxiliar |
| Agent | external_reference | rdfs:seeAlso → URI | 0..* | Sem sameAs automático |
| Agent | provenance | prov:wasDerivedFrom → URI | 0..* | Fonte semântica |
| Agent | related_authority | dcterms:relation → URI Agent/Subject | 0..* | Sem equivalência |
| Subject / skos:Concept | preferred_label | skos:prefLabel → T | 1..* | Uma forma por idioma |
| Subject | alternative_label | skos:altLabel → T | 0..* | Disjunto de prefLabel |
| Subject | scheme | skos:inScheme → URI | 1..* | Não cria descrição do esquema |
| Subject | broader | skos:broader → URI Subject | 0..* | Sem narrower automática |
| Subject | related | skos:related → URI Subject | 0..* | Sem escrita simétrica automática |
| Subject | external_reference | rdfs:seeAlso → URI | 0..* | Sem equivalência |
| Subject | provenance | prov:wasDerivedFrom → URI | 0..* | Fonte semântica |
| LocalizedText | value, language | Literal T na propriedade proprietária | value 1, language 0..1 | Sem idioma presumido |
| Title | kind | rdf:type → bf:Title/bf:VariantTitle | 1 | Preserva distinção |
| Title | main_title | bf:mainTitle → T | 1..* | Uma forma por idioma |
| Title | subtitle | bf:subtitle → T | 0..* | Sem ordenação |
| Contribution / bf:Contribution | agent | bf:agent → URI Agent | 1 | Nunca ligação direta Work→Agent |
| Contribution | role | bf:role → URI | 1..* | Sem whitelist global de papéis |
| Publication / bf:Publication | agent | bf:agent → URI Agent | 0..* | Sem copiar autoridade |
| Publication | place | bf:place → URI | 0..* | Lugar fora do inventário de cinco entidades |
| Publication | date | bf:date → literal PublicationDate | 0..* | Sem inferência de ano |
| PublicationDate | value, datatype | Forma lexical + datatype | 1 cada | xsd:string/gYear/date; normalize=False; exportação recusa perdas |
| Identifier | kind | rdf:type → bf:Identifier/bf:Local/bf:Isbn | 1 | Tipos atuais apenas |
| Identifier | value | rdf:value → S | 1 | Valor transcrito; sem checksum |
| Identifier | source | bf:source → URI | 0..* | Não constrói URL pelo valor |
| Extent / bf:Extent | label | rdfs:label → T | 1..* | Descrição literal |
| Note / bf:Note | label | rdfs:label → T | 1..* | Descrição literal |
| Note | note_type | bf:noteType → S | 0..* | Não é IRI |
| Classification / bf:Classification | classification_portion | bf:classificationPortion → S | 1..* | Não converte em número |
| Classification | source | bf:source → URI | 0..* | Esquema explícito |
| ShelfMark / bf:ShelfMark | value | rdf:value → S | 1 | Mantém o contrato existente |
| ShelfMark | source | bf:source → URI | 0..* | Fonte explícita |

Relação Instance related_to existe no registro da #16, mas não no DTO InstanceRead:
nenhum campo novo foi inventado. Um snapshot canônico que a contenha é exportado
integralmente. authorized_name e preferred_label compartilham predicados com label
ou alternative_label no contexto; os aliases são nomes semânticos únicos por
predicado, sem mudar a origem Pydantic. O contexto não converte JSON operacional
em JSON-LD automaticamente: auxiliares e identidade passam pelo mapeamento.

## Identidade e fronteira de referências

LocalReference sem UUID pode reutilizar URI armazenada; com UUID exige resolução
confiável, sem banco dentro do adaptador. Um mapa fornecido exige correspondência
para toda referência explicitamente local utilizada. ResourceReference legado e
ExternalReference conservam URI, inclusive URN/Unicode/fragmentos permitidos,
sem classificar localidade pelo prefixo ou buscar autoridade. entity_type orienta
validação estrutural/resolução, sem adicionar tipos RDF à descrição alheia.

ExternalReference.namespace/external_id são dados de origem/reconciliação; não
há predicado canônico aprovado para exportá-los sobre o alvo no snapshot proprietário.
São omitidos como metadados operacionais, sem fabricar Identifier ou equivalência.
Se tal informação já existir num snapshot RDF, serialize_graph a preserva.
UnreconciledReference é rejeitada. Futuro rascunho pode conservar label/namespace/key
no contrato operacional separado até resolução; não contaminar Linked Data com URI
provisória ou literal no lugar de Agent/Subject. A política não cria reconciliação.

## Valores, equivalência e limitações

Unicode, caixa, pontuação e idioma são preservados; não presumir pt-BR. Ausência
não gera literais vazios/defaults. Datas são texto e datatype explícito; não usar
inteiros para anos transcritos. Números/booleanos não existem nos campos bibliográficos
atuais: não são coercidos por um mecanismo genérico. O caminho Graph admite termos
RDF válidos, sujeitos a check_graph e round-trip. Listas operacionais não são rdf:List;
a ordem não muda semântica. Duplicatas de literais/IRIs colapsam por conjunto RDF;
dois auxiliares explicitamente declarados continuam dois nós.

JSON-LD e Turtle vêm do mesmo grafo. RDFLib pode normalizar alguns termos lexicais
na leitura, inclusive datas com timezone ou números; exportação que altere termos
falha com RdfDocumentError. Não há promessa de serializar todo valor estruturalmente
aceito por PublicationDate nem todo datatype RDF; limitações reais da biblioteca
ficam explícitas em vez de perdas silenciosas. RDFLib também omite ciclos de blank
nodes desconectados na saída JSON-LD: o adaptador os recusa por isomorfismo. Coleções
RDF existentes e ciclos ligados à raiz têm round-trip testado; DTOs não criam rdf:List.
Graph é o caminho de extensões;
DTOs fechados não oferecem metadata genérica ou uma segunda interpretação canônica.

## Integração HTTP

| Representação | Content-Type | Suporte |
| --- | --- | --- |
| JSON operacional | application/json | DTOs existentes; não RDF |
| JSON-LD | application/ld+json | Implementado pelo adaptador |
| Turtle | text/turtle | Implementado pelo adaptador |
| RDF/XML, N-Triples, HTML | — | Não implementados por este contrato |

negotiate_format separa decisão HTTP do serializador semântico. Ausência de Accept,
*/* e empate escolhem default REST application/json. available/default permitem
preferência de um futuro resolvedor: por exemplo available=(JSON_LD,TURTLE),
default=JSON_LD. HTML/default humano do ADR 0019 só poderá integrar após implementar
essa representação em outro adaptador. Não alterar contratos REST existentes.

Para cada formato, a faixa mais específica determina q (q=0 específico exclui
apesar de curinga positivo); escolhe-se maior q, maior especificidade, depois
preferência do servidor com default primeiro. Duplicatas igualmente específicas
usam menor q, tornando exclusão conservadora/determinística. Cabeçalho vazio não
é ausente: nenhuma representação aceitável. Tipos desconhecidos são ignorados
quando há alternativa aceitável. q inválido/duplicado ou sintaxe inválida gera
NotAcceptable; não há fallback silencioso. Qualidade admite 0..1 com até três
casas, conforme RFC 9110. Nomes de mídia/parâmetros são case-insensitive.

Parâmetros de mídia são restrições: nenhuma representação oferece profile/charset
neste contrato; uma faixa parametrizada não corresponde. Strings entre aspas
podem conter vírgula/ponto e vírgula; escapes e controles são recusados neste
subconjunto. Extensões Accept arbitrárias não são anunciadas.

Um futuro handler pode usar MEDIA_TYPES[selected] e Response(body, media_type=...),
traduzir NotAcceptable para 406, retornar DTO para JSON e usar snapshot canônico
para publicação integral. Deve configurar Vary: Accept em todas as respostas cuja
representação/status/destino dependa da negociação. URI pública e documentos
continuam distintos (303/200 conforme ADRs). Content-Type de futura ingestão
é validado separadamente, com 415 para mídia incompatível. Token de revisão do
domínio não é ETag universal; cache por representação e dependências compostas
exige contrato próprio. Não foram registradas novas rotas.

A M05.06 integra este negociador e a exportação integral nos GET individuais
editoriais/públicos. Veja [contrato HTTP implementado](catalogographic-listing.md)
para caminhos, visibilidade, ETags e 406. A descrição de integração futura acima
registra o contrato original M03; ingestão/resolução de identidades permanecem futuras.

## Exemplos, testes e evolução

[Exemplos pareados](../examples/serialization/) contêm os cinco Read, Organization
adicional e composição explícita. Dados sintéticos. related.json é uma lista
operacional de seis Read, não um snapshot único nem endpoint. Gerar novamente:

```bash
cd apps/api
uv run python ../../scripts/generate_serialization_examples.py
uv run pytest ../../tests/api/test_semantic_serialization.py
uv run pytest
uv run ruff check . ../../tests ../../scripts/generate_serialization_examples.py
uv run mypy src
cd ../..
bash scripts/check.sh
```

Ambiente sincronizado sem uv funcional pode usar apps/api/.venv/bin/python,
pytest/ruff/mypy. O gerador grava somente os exemplos novos e não toca os legados.
Testes conferem mapeamentos, tipos, URI, campos ausentes, Unicode, idiomas, datas,
referências inválidas, contextos/imports, limites, composição, extensões canônicas,
exemplos e Accept. Conversões usam rdflib.compare.isomorphic, sem igualdade textual.
As fixtures inválidas têm manifest com camada de rejeição; todas são executadas.

#20 aprofundará perfis configuráveis/cardinalidades/vocabulários; #21 aprofundará
SHACL e conformidade institucional. A saída atual já pode ser entregue a validate_profile
local; serialização não escolhe nem força perfil. #25 ampliará ontologias com
namespaces próprios e mapeamentos aprovados; extensões Graph já sobrevivem à
exportação integral. #30/#31 consolidarão conformidade, versionamento e homologação.
Novos termos sem mudar interpretação exigem release nova de contexto; mudanças
incompatíveis exigem contrato major. Releases JSON/SHACL atuais permanecem intactas.
Fusão, aliases HTTP, ingestão pública, quotas, editor, MARC, busca e circulação
continuam fora do escopo. Ver [evidências](semantic-serialization-verification.md).

Referências consultadas: [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/),
[ontologia BIBFRAME oficial](https://github.com/lcnetdev/bibframe-ontology/blob/master/bibframe.rdf)
e [Accept RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5.1).
