# Estratégia bibliográfica: BIBFRAME 2.0

A Etapa 2 implementou o protótipo descrito abaixo. Consulte
[fundação semântica](semantic-foundation.md), [ADR 0007](../decisions/0007-semantic-core.md)
e [ADR 0008](../decisions/0008-experimental-rdf-persistence.md).
O restante deste documento registra a estratégia inicial e requisitos futuros;
as tabelas existentes são experimentais, sem esquema bibliográfico definitivo.

## Entidades e limites

BIBFRAME 2.0 será o modelo semântico principal, utilizando o namespace
`http://id.loc.gov/ontologies/bibframe/`. RDF expressará relações como triplas e
preservará identificadores de vocabulários externos.

- **Work**: conteúdo intelectual, assuntos, contribuições e relações entre obras.
- **Instance**: materialização/publicação de um Work, edição, suporte e publicação.
- **Item**: cópia individual de uma Instance, com características próprias e holdings.

As relações fundamentais são `bf:instanceOf` e `bf:itemOf`, com inversas como
`bf:hasInstance` e `bf:hasItem` quando necessárias ao perfil. O perfil catalográfico
institucional determinará cardinalidades e campos; não confundir exemplos do
vocabulário com regras de obrigatoriedade. Nenhum esquema definitivo é criado agora.

Um Item BIBFRAME e um exemplar administrativo não são a mesma entidade de software.
O inventário terá identidade interna própria e poderá referenciar a URI do Item e
da Instance. Empréstimos, leitor, prazo, multa, condição operacional e reserva ficam
em módulos administrativos. Dados pessoais nunca entram no grafo bibliográfico
público. Um Item pode conter informação pública de acervo sem expor transações.

## Identificadores e relacionamentos

Proposta: UUID opaco para identidade interna e URI HTTP(S) persistente sob domínio
controlado para recursos públicos, por exemplo `/resources/{uuid}`. Não usar ISBN,
barcode ou chave de índice como identidade canônica. ISBN e outros identificadores
são atributos/relações; identificadores externos mantêm esquema, valor e origem.
A URI não deve conter título, localização ou idioma que possam mudar. O domínio
real e a política de resolução/conneg precisam de decisão antes de publicar dados.

Relações entre recursos usam URIs. Não copiar nomes de autoridades como substituto
de vínculo; rótulos multilíngues e formas variantes são metadados. Extensões locais
precisam de namespace controlado e definição documentada. SKOS, Dublin Core e PROV-O
poderão complementar BIBFRAME em perfis explícitos, preservando os URIs originais.

## Persistência inicial proposta

PostgreSQL deve manter registros e revisões semânticas canônicas (possivelmente
JSON-LD/RDF em JSONB, com projeções relacionais para restrições e consultas), além
de dados administrativos relacionais. Essa direção foi validada por um protótipo de snapshots JSON-LD em JSONB:
JSONB não é triplestore e não fornece SPARQL. Não criar uma tabela genérica de
triplas nem modelo relacional definitivo sem validar casos de catalogação reais.

A representação deve preservar tipos RDF, URIs, datatypes, tags de idioma,
multivalores e blank nodes; nunca reduzir o grafo a um dicionário de strings.
Contextos JSON-LD serão locais, versionados e controlados. Não buscar contextos
remotos arbitrários durante processamento de documentos não confiáveis.
Importação futura terá limites de tamanho e proteção contra acesso de rede indevido.

## Versionamento e proveniência

Planejar revisões imutáveis, referência para revisão atual, controle otimista de
concorrência (revision/ETag) e histórico que permita reconstruir e auditar mudanças.
Cada revisão registra agente, instante UTC, fonte, processo/importação, identificador
externo e perfil de validação. Identidade do recurso permanece estável entre revisões.
Histórico público e auditoria interna têm controles de acesso diferentes.
PROV-O pode representar proveniência exportável; não substitui auditoria operacional.
Fusões, exclusões e redirecionamentos de URIs precisam de política própria.

## Validação, busca e interoperabilidade

Pydantic valida os contratos HTTP; SHACL validará grafos segundo perfis versionados.
Validade de JSON não implica validade RDF ou conformidade catalográfica. RDFLib e
pySHACL são utilizados pelo protótipo da Etapa 2, com perfis locais versionados.
JSON-LD será formato de intercâmbio, com Turtle opcional para inspeção técnica.

Elasticsearch receberá documentos por recursos/projeções de descoberta. Índices
com mapeamentos versionados, aliases e reindexação serão definidos posteriormente.
MARC 21 será formato de entrada/saída com mapeamento documentado; conversões podem
ser parciais e precisarão de relatórios de perdas, sem se tornar o modelo interno.

Não implantar triplestore nesta fase. Reavaliar se travessias de grafos, federação
ou SPARQL público exigirem desempenho/funções não atendidos por PostgreSQL e índices.
Um protótipo deverá medir consultas, volume e custo operacional antes dessa decisão.

## Referências normativas

- [Modelo BIBFRAME 2.0 — Library of Congress](https://www.loc.gov/bibframe/docs/bibframe2-model.html)
- [Vocabulário BIBFRAME](https://id.loc.gov/ontologies/bibframe.html)
- [RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/)
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)
- [SHACL](https://www.w3.org/TR/shacl/)
- [PROV-O](https://www.w3.org/TR/prov-o/)
