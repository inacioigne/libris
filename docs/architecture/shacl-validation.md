# Validação semântica SHACL — M03.02.02

Especificação técnica da [issue #21](https://github.com/inacioigne/libris/issues/21).
A implementação reutiliza RDFLib/pySHACL, ADRs 0007/0014/0021 e o
[ADR 0022](../decisions/0022-shacl-profile-policies.md). Perfis institucionais
continuam candidatos à homologação; não há endpoints ou editor novos.

## Fronteiras

| Responsabilidade | Mecanismo | O que não comprova |
| --- | --- | --- |
| Estrutura de DTO/configuração, tipos, coerência min/max/required/repeatable | Pydantic 2, schemas locais, ProfileRegistry | Conformidade de um grafo concreto |
| Conformidade RDF segundo perfil/release/modo | SHACL local e suplemento controlado 2.0 | Existência PostgreSQL, identidade real ou pertinência a vocabulário remoto |
| Raiz, nós proprietários/auxiliares, descrição alheia, inversas indevidamente gravadas | check_snapshot/owned_nodes/compose_snapshots | Estado transacional de referências |
| Existência/tipo local, revisão esperada/CAS, commit/rollback | Serviços de aplicação e contratos de resolução/persistência | Identidade de autoridades externas |

Um Graph vazio pode ser conforme porque nenhum target é selecionado. prepare_document
continua rejeitando raiz ausente; SHACL não autoriza sua gravação. Work não exige
Instance. Item bibliográfico não é exemplar administrativo de empréstimo.

## Registro, composição e releases

| Conjunto / release / modo | Artefatos locais |
| --- | --- |
| urn:libris:shapes:experimental / 1.0 / snapshot | monograph-v1.ttl |
| urn:libris:shapes:institutional / 1.1 / snapshot | monograph-v1.1.ttl + authority-v1.ttl |
| urn:libris:shapes:institutional / 1.1 / composed | fontes de snapshot + monograph-v1.1-composed.ttl |

SHAPE_RELEASE_FILES é a resolução executável única. LEGACY_SHAPE_RELEASES associa
urn:libris:profile:monograph:v1 ao experimental 1.0, e
urn:libris:profile:monograph:v1:1 / urn:libris:profile:authority:v1 ao institucional 1.1.
PROFILE_SHAPES permanece como visão derivada de compatibilidade.
ShapeRegistry da #20 declara disponibilidade/classes/contextos, sem caminhos;
testes conferem que suas entradas possuem resolução executável e vice-versa.
Não são dois catálogos concorrentes: domínio descreve a associação, infraestrutura
fixa recursos do pacote. Fontes indisponíveis não são substituídas por outra release.

A família monográfica v1.1 tem release 1.1; authority-v1 tem release de perfil 1.0,
mas reutiliza o conjunto institucional 1.1. Releases 2.0.0 de core, Work, Instance,
Item, Agent, Subject, monograph, serial, digital e work-minimal fixam explicitamente
validation id/release/context, herdado pelo registro. O perfil resolvido confiável
acrescenta somente políticas expressíveis pelo suplemento versionado do ADR 0022.
Não carregar configurações administrativas não confiáveis diretamente no adaptador.

validate_resolved_profile exige context.profile_release igual a profile.release_id;
valida referências declaradas mesmo quando não aplicáveis ao modo. Snapshot ignora
regras compostas conhecidas. Composed carrega também regras básicas; experimental
não oferece um segundo contexto pelo contrato 2.0. A chamada histórica composed=True
continua compatível: seu único arquivo já verifica inversas. Vários conjuntos são
unidos somente quando registrados, deduplicando arquivos.

Revisões persistidas conservam previous.profile, sem migração nem revalidação com
outra release. validate_profile não recebe o suplemento. Novas regras incompatíveis
nas fontes manuais requerem outra release/artefato; os hashes históricos continuam
protegidos pelos testes da #20. Nenhum JSON/TTL publicado foi reescrito.

## Convenções e regras por entidade

O [inventário integral](shacl-inventory.md) registra cada NodeShape, PropertyShape,
path, cardinalidade, datatype, nodeKind, classe, referência, mensagem e severidade.

| Termo | Convenção |
| --- | --- |
| sh:NodeShape / sh:targetClass | Regra da entidade/auxiliar; targets selecionam tipos declarados, sem inventar rdf:type nem garantir a presença da raiz |
| sh:PropertyShape / sh:path | Propriedade direta; caminho complexo apenas quando a regra o exige (inversas compostas) |
| sh:nodeKind / sh:class / sh:node | Tipo RDF, classe local e validação auxiliar; referências URI não descritas usam alternativa explícita sem tipo local |
| sh:minCount / sh:maxCount | Política do perfil, não axioma universal de BIBFRAME; opcional omite triplas |
| sh:datatype | Literais textuais xsd:string/rdf:langString; publicação xsd:string/gYear/date; sem coerção ou checksum |
| sh:languageIn / sh:uniqueLang | Lista de idiomas somente se configurada; matching SHACL aceita subtag (pt inclui pt-BR); uniqueLang não limita quantidade de strings sem idioma |
| sh:in | Enum de termos RDF configurado, com idioma/datatype preservados; não consulta vocabulário remoto |
| sh:qualifiedValueShape / qualifiedMinCount / qualifiedMaxCount | Quantidade de valores que atendem ao subshape; mínimo não variante e Local nas fontes; máximo qualificado só em futura release explícita |
| sh:severity | Violation bloqueia; Warning/Info conservam diagnóstico sem bloquear |

As shapes permanecem abertas: não usar sh:closed para impedir ontologias externas.
Propriedades fora do perfil são conservadas. A superfície configurável da #20 é
registrada; o grafo RDF integral não recebe uma whitelist universal.

| Entidade | Regras locais reutilizadas |
| --- | --- |
| Work institucional | IRI; ao menos um Title não VariantTitle; mainTitle textual não vazio e uniqueLang; contribuições, assuntos e relações opcionais; sem obrigação de Instance |
| Instance institucional | Exatamente um instanceOf IRI; tipo Work quando declarado; título/ISBN opcionais; editionStatement textual; Publication, Extent, Identifier e Note estruturados |
| Item institucional | Exatamente um itemOf IRI; tipo Instance quando declarado; ao menos um Local com rdf:value string não vazio, unitário; heldBy opcional Organization; notas/custódia/proveniência |
| Agent/Person/Organization | IRI; rdfs:label textual não vazio e um por idioma; altLabel, identificadores e referências externas opcionais |
| Subject/skos:Concept | IRI; prefLabel não vazio, uniqueLang e disjunto de altLabel; inScheme obrigatório; broader/related URI com classe se descritos; sem equivalência presumida |
| Auxiliares | Title/VariantTitle, Contribution (um agente, papéis 1..*), Identifier/Local/Isbn, Publication (variante contratada de ProvisionActivity), Extent, Note, Classification e ShelfMark |
| Legado experimental | Títulos Work/Instance obrigatórios; alvos Work/Instance/Item; relações com classe local e inversas exigidas; identificação Item é Warning |

Work identifiedBy, subclasses não contratadas de ProvisionActivity e tipos novos de
identificadores não são inventados: requerem perfil/release explícitos quando houver
necessidade aprovada. ISBN é transcrição opcional sem checksum; título Work não é
copiado para Instance. Datas incertas usam xsd:string. Não consultar VIAF/ORCID/
Wikidata nem declarar owl:sameAs por mera referência.

## Políticas 2.0 e contradições

Suplemento determinístico aplica min/max, nodeKind, datatypes, texto não vazio,
language.required/allowed/unique, allowed_values e destinos de propriedades novas.
Não altera os targets/constraints qualificados existentes. Metadados de apresentação,
condições e defaults não criam triplas nem constraints. Os mínimos/maximos e nodeKind
locais não podem ser relaxados; datatypes/classes explicitamente incompatíveis
produzem ProfileError(contradictory_shapes) antes da execução sobre os dados.
Ausência de campo no formulário não remove regra local. Não há geração de SPARQL.

Divergência encontrada: Item.identifiedBy no descritor core lista Identifier/Local,
enquanto a shape aceita Isbn adicional e exige Local por mínimo qualificado.
A lista declarativa indica edição suportada; não invalida RDF historicamente aceito.
O adaptador confere classes incompatíveis, mas conserva alternativas locais em campos
já cobertos. Ausências/enum/mínimos mais restritos agora têm execução demonstrada;
serial.frequency e digital.encodingFormat/dateCreated recebem constraints simples.

## Snapshot e grafo composto

Snapshot contém raiz e auxiliares; referências locais/externas podem permanecer só
como IRI. Tipo incorreto explicitamente descrito é diagnosticado, sem download nem
tripla fictícia. Em composed, compose_snapshots renomeia blank nodes e deriva
hasInstance/hasItem de instanceOf/itemOf. As shapes verificam igualdade nos dois
sentidos, inclusive inversas extras/ausentes. O validador não deriva nem corrige
relações: o chamador escolhe e compõe revisões antes de validar. Context.snapshots
registra URI/revisão/release, sem resolver automaticamente histórico ou existência.

Graph não é alterado: inplace=False, inferência none, nenhum preenchimento. Testes
usam termos exatos para imutabilidade e isomorfismo para conversões/composição.

## Resultado intermediário e erros

ValidationReport(conforms, issues, graph) preserva o relatório SHACL RDF.
ValidationIssue conserva focus_node/path/severity/messages compatíveis e acrescenta
source_shape, source_constraint_component e value quando presentes. focus_term,
path_term, source_shape_term, value_term e message_terms preservam identidade de
blank nodes, datatypes e idiomas sem converter tudo em texto ambíguo.

As strings são visão legada de apresentação, **não serialização RDF sem perdas**.
Termos e caminhos complexos devem ser interpretados no grafo do relatório; rótulos
blank node não são identificadores persistentes entre execuções. A #22 já mapeia
esse contrato interno para [DTOs seguros](catalogographic-errors.md), sem publicar
tipos RDFLib/pySHACL. Ver [referência v1](catalogographic-contract.md).
correlate_validation_issues usa termo focal exato e classes locais. Propriedade
compartilhada é correlacionada por classe. Caminho complexo/desconhecido ou foco
ambíguo sem termo conserva o resultado com field_ids vazio; não aproximar por label.

| Situação | Resultado |
| --- | --- |
| RDF não conforme | ValidationReport(conforms=False), com Violation e grafo |
| Warning/Info sem Violation | conforms=True, issues continuam presentes |
| Entrada RDF inválida/limite excedido | RdfDocumentError do adaptador |
| Perfil desconhecido | ProfileError unknown_profile |
| Release/contexto/conjunto incompatível | ProfileError validation_release_mismatch / unknown_shapes / missing_shapes |
| Configuração contraditória | ProfileError contradictory_shapes |
| Arquivo indisponível | ShaclValidationError shapes_unavailable |
| Turtle ou constraints inválidas | ShaclValidationError malformed_shapes |
| Exceção interna / ValidationFailure em vez de Graph | ShaclValidationError engine_failure |

Falhas internas não viram uma falsa violação catalográfica. Mensagens internas não
são automaticamente payload HTTP. prepare_document rejeita não conformidade antes
de create abrir transação; revise falha dentro da transação, revertendo CAS e sem
salvar revisão. Testes com doubles verificam ordem/saída; atomicidade física só é
comprovada por PostgreSQL dedicado, não pelos doubles.

## Segurança, custo e isolamento

Entradas passam por parse_document/check_graph: Graph simples, IRIs válidas, tipos
RDF válidos; bytes default 1 MiB, máximo configurável 10 MiB, profundidade JSON 64.
Contextos/imports remotos são recusados antes do parser. Validação in-memory não
impõe novamente limite de bytes de uma serialização arbitrária nem depende de banco.

Shapes vêm somente do pacote por dados Turtle em memória; URLs/paths do cliente,
sh:shapesGraph/OWL imports no RDF e shapes injetadas não escolhem regras. Flags são
inference=none, advanced=False, js=False, do_owl_imports=False, sparql_mode=False,
inplace=False, allow_warnings=True, allow_infos=True. Meta-SHACL usa recurso local
embutido no pySHACL. Fontes confiáveis atuais não possuem SERVICE SPARQL; adicionar
consultas federadas seria mudança de segurança a revisar, não extensão automática.

Cache LRU de 16 documentos/16 verificações usa conteúdo imutável, depois da resolução
id/release/context; Graph de execução é reconstruído. Arquivos são relidos, inclusive
para detectar remoção/alteração. Suplementos têm digest de conteúdo/release e Graph
privado. Não há cache de resultados nem compartilhamento mutável. Testes comprovam
hit de parsing/meta-verificação, isolamento e conteúdo distinto. O cache reduz custo
da meta-validação repetida, sem prometer throughput ou quotas de produção.

Limites de bytes/profundidade não são deadline de CPU. Exposição futura de endpoints
precisa de medições/limites de concorrência e timeout/isolamento de processo; não se
introduziu worker, fila ou threads que finjam interromper pySHACL. Não há Elasticsearch,
triplestore, imports de ontologia ou chamada externa na validação.

## Exemplos equivalentes

Snapshot de Instance com Work externa sem descrição, título/ISBN opcionais:

```turtle
@prefix bf: <http://id.loc.gov/ontologies/bibframe/> .
<urn:libris:example:instance> a bf:Instance ;
    bf:instanceOf <https://example.invalid/work> .
```

```json
[{"@id":"urn:libris:example:instance",
  "@type":["http://id.loc.gov/ontologies/bibframe/Instance"],
  "http://id.loc.gov/ontologies/bibframe/instanceOf":[{"@id":"https://example.invalid/work"}]}]
```

Ambos usam parse_document e validate_profile com INSTITUTIONAL_PROFILE_ID.
Exemplos integrais das cinco entidades em [serialization](../examples/serialization/)
e corpus institucional com manifest (dez cenários originais válidos preservados,
novos cenários explicitamente adicionados). Não mudar expected para contornar falha.

## Pendências e homologação

#20 fornece configurações/resolução; administração/publicação persistida e integração
v2 à escrita não foram antecipadas. #22 define códigos/payloads HTTP e formulário;
#24 valida valores/fontes controladas; #25 revisa novas ontologias/componentes;
#30 reutiliza/amplia fixtures e medições. Identidade real, existência de autoridades
externas e validade em vocabulário remoto não são demonstradas por SHACL.
Homologação por catalogadores, domínio público, equivalência/proveniência e políticas
novas continuam humanos. Evidências e critérios: [verificação](shacl-validation-verification.md).

Referências técnicas: [SHACL W3C](https://www.w3.org/TR/shacl/) e
[opções/erros pySHACL](https://github.com/RDFLib/pySHACL), consultados em 2026-10-12.
