# Inventário SHACL — #21

Inventário das quatro fontes locais, sem alteração de conteúdo. Constraints anônimas
são descritas recursivamente; severidade omitida equivale a `sh:Violation`.
NodeShapes reutilizadas por `sh:node` conservam os identificadores publicados.

| Arquivo | Associação / release | Contexto | Dependências / cobertura |
| --- | --- | --- | --- |
| monograph-v1.ttl | monograph:v1; experimental 1.0 | snapshot legado (já exige inversas) | test_bibliographic.py; regressão histórica #20 |
| monograph-v1.1.ttl | monograph:v1:1; institutional 1.1 | snapshot e composed | authority-v1.ttl para autoridades; corpus institucional e test_shacl_validation.py |
| authority-v1.ttl | authority:v1 1.0; institutional 1.1 | snapshot e composed | p:Identifier definido em monograph-v1.1.ttl; testes de autoridade/SKOS |
| monograph-v1.1-composed.ttl | institutional 1.1 | somente composed | duas fontes anteriores; compose_snapshots, testes de inversas |

Os IDs completos e a associação aos perfis 2.0 constam na [especificação](shacl-validation.md).
PropertyShapes históricas são anônimas (sem `rdf:type sh:PropertyShape` explícito);
sua vinculação por `sh:property`/`sh:path` identifica o papel SHACL.
Não há `sh:closed`, `sh:languageIn`, `sh:in` ou `sh:qualifiedMaxCount` nas fontes históricas.
Constraints de idioma usam `sh:uniqueLang`, sem whitelist institucional inventada.
As constraints suplementares 2.0 estão no ADR 0022 e não integram estas fontes.

## monograph-v1.ttl

85 triplas; 4 NodeShapes; 16 PropertyShapes vinculadas.

### profile:Instance

Regras do nó: `sh:nodeKind sh:IRI`; `sh:targetClass bf:Instance`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `[ sh:inversePath bf:hasInstance ]` | `sh:equals bf:instanceOf`; `sh:message "instanceOf e hasInstance devem ser consistentes."@pt` |
| `[ sh:inversePath bf:itemOf ]` | `sh:equals bf:hasItem` |
| `bf:hasItem` | `sh:class bf:Item`; `sh:nodeKind sh:IRI` |
| `bf:identifiedBy` | `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:instanceOf` | `sh:class bf:Work`; `sh:maxCount "1"^^xsd:integer`; `sh:message "Neste perfil, Instance referencia exatamente um Work descrito."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `bf:title` | `sh:minCount "1"^^xsd:integer`; `sh:node profile:Title` |

### profile:Item

Regras do nó: `sh:nodeKind sh:IRI`; `sh:targetClass bf:Item`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `[ sh:inversePath bf:hasItem ]` | `sh:equals bf:itemOf`; `sh:message "itemOf e hasItem devem ser consistentes."@pt` |
| `bf:heldBy` | `sh:nodeKind sh:IRI` |
| `bf:identifiedBy` | `sh:message "Recomenda-se um identificador bibliográfico para o Item."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:nodeKind sh:BlankNodeOrIRI`; `sh:severity sh:Warning` |
| `bf:itemOf` | `sh:class bf:Instance`; `sh:maxCount "1"^^xsd:integer`; `sh:message "Neste perfil, Item referencia exatamente uma Instance descrita."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:nodeKind sh:IRI` |

### profile:Title

Regras do nó: `sh:class bf:Title`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:mainTitle` | `sh:message "O título deve ter ao menos um bf:mainTitle literal."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:nodeKind sh:Literal` |

### profile:Work

Regras do nó: `sh:nodeKind sh:IRI`; `sh:targetClass bf:Work`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `[ sh:inversePath bf:instanceOf ]` | `sh:equals bf:hasInstance` |
| `bf:content` | `sh:nodeKind sh:IRI` |
| `bf:hasInstance` | `sh:class bf:Instance`; `sh:nodeKind sh:IRI` |
| `bf:language` | `sh:message "Idioma deve referenciar uma URI de vocabulário."@pt`; `sh:nodeKind sh:IRI` |
| `bf:title` | `sh:message "Work requer um título estruturado."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:node profile:Title`; `sh:nodeKind sh:BlankNodeOrIRI` |

## monograph-v1.1.ttl

607 triplas; 14 NodeShapes; 64 PropertyShapes vinculadas.

### p:Classification

Regras do nó: `sh:or ([ sh:class bf:Classification ])`; `sh:targetClass bf:Classification`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:classificationPortion` | `sh:message "Código de classificação: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ])` |
| `bf:source` | `sh:message "Esquema de classificação: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |

### p:Contribution

Regras do nó: `sh:or ([ sh:class bf:Contribution ])`; `sh:targetClass bf:Contribution`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:agent` | `sh:maxCount "1"^^xsd:integer`; `sh:message "Agente: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Agent ] [ sh:class bf:Person ] [ sh:class bf:Organization ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:role` | `sh:message "Papel: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:nodeKind sh:IRI` |

### p:Extent

Regras do nó: `sh:or ([ sh:class bf:Extent ])`; `sh:targetClass bf:Extent`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `rdfs:label` | `sh:message "Descrição: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |

### p:Identifier

Regras do nó: `sh:or ([ sh:class bf:Identifier ] [ sh:class bf:Local ] [ sh:class bf:Isbn ])`; `sh:targetClass bf:Identifier`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:source` | `sh:message "Fonte: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdf:value` | `sh:maxCount "1"^^xsd:integer`; `sh:message "Valor: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ])` |

### p:Instance

Regras do nó: `sh:nodeKind sh:IRI`; `sh:or ([ sh:class bf:Instance ])`; `sh:targetClass bf:Instance`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:carrier` | `sh:message "Suporte: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `bf:editionStatement` | `sh:message "Indicação de edição: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |
| `bf:extent` | `sh:message "Extensão: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Extent`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:hasItem` | `sh:message "Exemplares: Derivada de itemOf; não gravar no snapshot proprietário."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Item ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:identifiedBy` | `sh:message "Identificadores: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Identifier`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:instanceOf` | `sh:maxCount "1"^^xsd:integer`; `sh:message "Obra: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Work ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:note` | `sh:message "Notas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Note`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:provisionActivity` | `sh:message "Publicação: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Publication`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:title` | `sh:message "Título: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Title`; `sh:nodeKind sh:BlankNodeOrIRI` |

### p:Isbn

Regras do nó: `sh:or ([ sh:class bf:Isbn ])`; `sh:targetClass bf:Isbn`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:source` | `sh:message "Fonte: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdf:value` | `sh:maxCount "1"^^xsd:integer`; `sh:message "Valor: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ])` |

### p:Item

Regras do nó: `sh:nodeKind sh:IRI`; `sh:or ([ sh:class bf:Item ])`; `sh:targetClass bf:Item`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:custodialHistory` | `sh:message "Histórico de custódia: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |
| `bf:heldBy` | `sh:message "Instituição detentora: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Organization ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:identifiedBy` | `sh:message "Identificador institucional: Ao menos um bf:Local com rdf:value não vazio; barcode/inventário são atributos."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:node p:Identifier`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:identifiedBy` | `sh:qualifiedMinCount "1"^^xsd:integer`; `sh:qualifiedValueShape [ sh:class bf:Local ]` |
| `bf:itemOf` | `sh:maxCount "1"^^xsd:integer`; `sh:message "Manifestação: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Instance ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:note` | `sh:message "Notas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Note`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:shelfMark` | `sh:message "Marca de estante bibliográfica: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:ShelfMark`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `prov:wasDerivedFrom` | `sh:message "Proveniência semântica: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |

### p:Local

Regras do nó: `sh:or ([ sh:class bf:Local ])`; `sh:targetClass bf:Local`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:source` | `sh:message "Fonte: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdf:value` | `sh:maxCount "1"^^xsd:integer`; `sh:message "Valor: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ])` |

### p:Note

Regras do nó: `sh:or ([ sh:class bf:Note ])`; `sh:targetClass bf:Note`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:noteType` | `sh:message "Tipo da nota: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ])` |
| `rdfs:label` | `sh:message "Texto: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |

### p:Publication

Regras do nó: `sh:or ([ sh:class bf:Publication ])`; `sh:targetClass bf:Publication`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:agent` | `sh:message "Publicador: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Agent ] [ sh:class bf:Person ] [ sh:class bf:Organization ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:date` | `sh:message "Data de publicação: Texto transcrito ou data/gYear bem tipados; conservar incerteza como texto."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype xsd:gYear ] [ sh:datatype xsd:date ])` |
| `bf:place` | `sh:message "Local de publicação: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |

### p:ShelfMark

Regras do nó: `sh:or ([ sh:class bf:ShelfMark ])`; `sh:targetClass bf:ShelfMark`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:source` | `sh:message "Fonte: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdf:value` | `sh:maxCount "1"^^xsd:integer`; `sh:message "Valor: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ])` |

### p:Title

Regras do nó: `sh:or ([ sh:class bf:Title ] [ sh:class bf:VariantTitle ])`; `sh:targetClass bf:Title`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:mainTitle` | `sh:message "Título principal: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])`; `sh:uniqueLang "true"^^xsd:boolean` |
| `bf:subtitle` | `sh:message "Subtítulo: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |

### p:VariantTitle

Regras do nó: `sh:or ([ sh:class bf:VariantTitle ])`; `sh:targetClass bf:VariantTitle`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:mainTitle` | `sh:message "Título principal: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])`; `sh:uniqueLang "true"^^xsd:boolean` |
| `bf:subtitle` | `sh:message "Subtítulo: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |

### p:Work

Regras do nó: `sh:nodeKind sh:IRI`; `sh:or ([ sh:class bf:Work ])`; `sh:targetClass bf:Work`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:classification` | `sh:message "Classificação: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Classification`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:content` | `sh:message "Conteúdo: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `bf:contribution` | `sh:message "Contribuições: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Contribution`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:editionStatement` | `sh:maxCount "0"^^xsd:integer` |
| `bf:hasInstance` | `sh:message "Manifestações: Derivada de instanceOf; não gravar no snapshot proprietário."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Instance ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:instanceOf` | `sh:maxCount "0"^^xsd:integer` |
| `bf:itemOf` | `sh:maxCount "0"^^xsd:integer` |
| `bf:language` | `sh:message "Idioma: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `bf:note` | `sh:message "Notas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Note`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:provisionActivity` | `sh:maxCount "0"^^xsd:integer` |
| `bf:relatedTo` | `sh:message "Obras relacionadas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Work ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:subject` | `sh:message "Assuntos: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class skos:Concept ]) ]`; `sh:nodeKind sh:IRI` |
| `bf:title` | `sh:message "Títulos principal e alternativos: Ao menos um título não variante; um mainTitle por idioma em cada nó."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:node p:Title`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `bf:title` | `sh:qualifiedMinCount "1"^^xsd:integer`; `sh:qualifiedValueShape [ sh:not [ sh:class bf:VariantTitle ] ]` |
| `bf:translationOf` | `sh:message "Tradução de: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node [ sh:or ([ sh:not [ sh:property [ sh:minCount "1"^^xsd:integer ; sh:path rdf:type ] ] ] [ sh:class bf:Work ]) ]`; `sh:nodeKind sh:IRI` |

## authority-v1.ttl

225 triplas; 4 NodeShapes; 25 PropertyShapes vinculadas.

### p:Agent

Regras do nó: `sh:nodeKind sh:IRI`; `sh:or ([ sh:class bf:Agent ])`; `sh:targetClass bf:Agent`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:identifiedBy` | `sh:message "Identificadores: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Identifier`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `dcterms:relation` | `sh:message "Autoridade relacionada: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `prov:wasDerivedFrom` | `sh:message "Proveniência: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdfs:label` | `sh:message "Forma autorizada: Uma forma autorizada por idioma; preservar forma transcrita."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])`; `sh:uniqueLang "true"^^xsd:boolean` |
| `rdfs:seeAlso` | `sh:message "Referências externas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `skos:altLabel` | `sh:message "Formas variantes: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |

### p:Concept

Regras do nó: `sh:nodeKind sh:IRI`; `sh:or ([ sh:class skos:Concept ])`; `sh:targetClass skos:Concept`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `prov:wasDerivedFrom` | `sh:message "Proveniência: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdfs:seeAlso` | `sh:message "Referências externas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `skos:altLabel` | `sh:message "Termos variantes: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |
| `skos:broader` | `sh:message "Conceito mais amplo: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `skos:inScheme` | `sh:message "Vocabulário: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `skos:prefLabel` | `sh:disjoint skos:altLabel`; `sh:message "Termo autorizado: Um prefLabel por idioma; disjunto de altLabel."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])`; `sh:uniqueLang "true"^^xsd:boolean` |
| `skos:related` | `sh:message "Conceito relacionado: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |

### p:Organization

Regras do nó: `sh:nodeKind sh:IRI`; `sh:or ([ sh:class bf:Organization ])`; `sh:targetClass bf:Organization`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:identifiedBy` | `sh:message "Identificadores: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Identifier`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `dcterms:relation` | `sh:message "Autoridade relacionada: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `prov:wasDerivedFrom` | `sh:message "Proveniência: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdfs:label` | `sh:message "Forma autorizada: Uma forma autorizada por idioma; preservar forma transcrita."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])`; `sh:uniqueLang "true"^^xsd:boolean` |
| `rdfs:seeAlso` | `sh:message "Referências externas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `skos:altLabel` | `sh:message "Formas variantes: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |

### p:Person

Regras do nó: `sh:nodeKind sh:IRI`; `sh:or ([ sh:class bf:Person ])`; `sh:targetClass bf:Person`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `bf:identifiedBy` | `sh:message "Identificadores: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:node p:Identifier`; `sh:nodeKind sh:BlankNodeOrIRI` |
| `dcterms:relation` | `sh:message "Autoridade relacionada: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `prov:wasDerivedFrom` | `sh:message "Proveniência: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `rdfs:label` | `sh:message "Forma autorizada: Uma forma autorizada por idioma; preservar forma transcrita."@pt`; `sh:minCount "1"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])`; `sh:uniqueLang "true"^^xsd:boolean` |
| `rdfs:seeAlso` | `sh:message "Referências externas: Referência RDF explícita; sem resolução remota."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:nodeKind sh:IRI` |
| `skos:altLabel` | `sh:message "Formas variantes: Literal não vazio; preservar idioma/datatype."@pt`; `sh:minCount "0"^^xsd:integer`; `sh:minLength "1"^^xsd:integer`; `sh:nodeKind sh:Literal`; `sh:or ([ sh:datatype xsd:string ] [ sh:datatype rdf:langString ])` |

## monograph-v1.1-composed.ttl

22 triplas; 3 NodeShapes; 4 PropertyShapes vinculadas.

### p:ComposedInstance

Regras do nó: `sh:targetClass bf:Instance`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `[ sh:inversePath bf:hasInstance ]` | `sh:equals bf:instanceOf` |
| `[ sh:inversePath bf:itemOf ]` | `sh:equals bf:hasItem` |

### p:ComposedItem

Regras do nó: `sh:targetClass bf:Item`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `[ sh:inversePath bf:hasItem ]` | `sh:equals bf:itemOf` |

### p:ComposedWork

Regras do nó: `sh:targetClass bf:Work`.

| Path | Constraints da PropertyShape |
| --- | --- |
| `[ sh:inversePath bf:instanceOf ]` | `sh:equals bf:hasInstance` |
