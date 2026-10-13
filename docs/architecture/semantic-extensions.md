# Extensibilidade semântica — M03.03.02

## Objetivo e diagnóstico inicial

Incorporar ontologias por artefatos locais revisados, mantendo BIBFRAME como modelo
principal e Graph RDFLib como representação canônica. Issue #25 e entregas
#15, #16, #17, #18, #20, #21, #22 e #24 consultadas no GitHub.
Estado inicial: branch `main`, HEAD `180f45aeddd06b469cca2394ffb0203fbaf8fd32`,
workspace limpo. Não há arquitetura paralela, novas dependências ou tabelas.

O registro 1.0 já reconhece DCTERMS, SKOS, PROV e Schema.org; `check_field`
exige propriedade registrada e suportada. A presença do prefixo não autoriza
termos arbitrários. Há resolução por herança, contratos de apresentação,
validação suplementar SHACL e exportação integral de Graph.
Lacunas: metadados de governança incompletos, classes sem verificação de namespace
ou homologação, ausência de fixação do conteúdo do registro por release e de
um exemplo candidato com `dcterms:abstract`.

Divergência documental: a fundação semântica descreve o adaptador legado que aceita
contextos embutidos. O contrato de representação da issue #18 é mais restrito:
`parse_representation` exige o contexto local exato. Os exemplos desta entrega
usam essa interface; não ampliam o parser legado nem o contexto bibframe-v1.
Os campos `sources`, `value_kinds`, `minimum` e `maximum` do registro anterior
representam compatibilidade Libris, não axiomas universais da ontologia.

## Matriz inicial de implementação e lacunas

| Requisito | Existente | Lacuna real | Arquivos e mudança | Evidência planejada |
| --- | --- | --- | --- | --- |
| Namespaces | SemanticRegistry; unicidade e sobreposição | Governança e release fixada | profile_registry.py; profiles.py; semantics-v2.json | conflitos, IRI, homologação, imutabilidade |
| Classes externas | ClassDefinition por IRI; SKOS Concept | Namespace e autorização da classe | profile_registry.py; classe auxiliar PROV | classe válida, desconhecida e não homologada |
| Propriedades externas | check_field; tipos e destinos | Descrição e origem explícitas | profile_registry.py; abstract registrado | origem, tipo, destino, namespace divergente |
| Perfis mistos | ProfileRegistry; herança; layout | Demonstração candidata | work-extensions-2.0.0.json | herança, campo opcional e obrigatório |
| SHACL | pySHACL; add_profile_constraints | Exercitar extensão real | reutilizar validation.py e validation_policy.py | cardinalidade, datatype, nó, severidade |
| RDF e JSON-LD | serialize_graph; parse_representation; ownership | Exemplos pareados e regressão de preservação | fixtures extensions; testes | isomorfismo, idioma, datatype, URI e auxiliares |
| Revisões | prepare_document; serviço legado | Evidência de extensão preservada | testes com contrato atual, sem transações novas | snapshot de entrada/saída e atualização simulada |
| API e frontend | DTOs fechados; ResolvedProfile | Limites explícitos de edição e descoberta | documentação; nenhuma rota nova | DTO rejeita extra; descoberta de campo |
| Versionamento | fingerprints de perfil; compare_profiles | Registro histórico fixado por perfil | loader e lock semântico | release histórica, mutação rejeitada |
| Mapeamentos | Não há inferência | Especificação suficiente para #25 | documentação com exemplos | nenhum axioma automático |

## Arquitetura e pontos de extensão

`SemanticRegistry`, `NamespaceDefinition`, `ClassDefinition` e
`PropertyDefinition` permanecem no domínio. O formato de configuração 1.1 é
aditivo e exige metadados de governança; o formato 1.0 continua carregável.
`semantics-v1.json` não foi alterado. A release 2.0 em `semantics-v2.json`
acrescenta metadados, `dcterms:abstract` e a classe auxiliar `prov:Entity`.
Não cria entidades principais: Work, Instance, Item, Agent e Subject conservam
suas classes canônicas e ownership. Auxiliares não ganham tabelas ou CRUD.

O carregador `load_semantic_registry(release)` resolve somente um mapa de
artefatos do pacote, verifica SHA-256 e confere a identidade da release.
`semantic-release-lock.json` fixa também os bytes do registro histórico 1.0.
É um índice de integridade, não uma segunda fonte de namespaces. Clientes não
fornecem caminhos, URLs, shapes ou ontologias executáveis.

`semantic-profile-releases.json` declara as associações tipadas de arquivos,
releases de perfis e registros; o carregador verifica sua coerência.
`ProfileRegistry.semantics_by_release` associa o novo perfil à release 2.0;
`semantic_registry_for(release_id)` devolve uma cópia do registro associado.
Descendentes herdam a associação. Transições de disponibilidade, adição de releases
e substituição de drafts preservam essas associações. Perfis anteriores continuam
resolvidos com 1.0. O carregador chama `check_extension_of` para impedir remoção
ou redefinição dos contratos históricos na release aditiva.

### Registro de namespaces, classes e propriedades

Namespace: prefixo, IRI absoluta terminada em `/`, `#` ou `:`, identificação da
ontologia, release de origem quando conhecida, rótulos/descrições multilíngues,
mantenedor por IRI, referência de inclusão e aprovação técnica/institucional/pendente.
Datas de release da ontologia são texto: não precisam seguir SemVer. As versões
históricas `1.0` eram marcadores locais, não prova de uma versão oficial da
ontologia. Em 2.0 DCTERMS informa `2020-01-20`, conforme a
[especificação DCMI](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/); Schema.org e PROV não alegam
uma versão de origem verificada. Rótulos e descrições são metadados Libris.

Rejeitam-se prefixos e bases duplicados, sobreposição, IRIs inválidas e tentativa
de remapear `bf` ou substituir a ontologia BIBFRAME. Um prefixo é abreviação;
nunca identidade. `namespace` explícito nos termos deve corresponder à IRI.
`status=supported` e aprovação técnica/institucional autorizam a namespace;
`review_required` ou aprovação pendente impedem novos campos.

Classes: IRI, namespace, rótulo, descrição, classificação principal/auxiliar e
status. A ontologia é resolvida no namespace, sem duplicar sua identidade em cada
classe. `check_class` distingue reconhecimento de autorização e rejeita classes
não homologadas como origem ou destino de campos. `prov:Entity` é reconhecida
como auxiliar; sua presença no registro não cria um formulário nem autoriza
triplas operacionais. Edição de um auxiliar requer recurso de perfil e cobertura
SHACL locais, segundo os contratos existentes.

Propriedades: IRI completa, namespace, rótulo/descrição, referência à fonte
ontológica, origens Libris admitidas, variantes de valor, datatypes, classes e
entidades de destino, derivação e status. `check_field` valida todas essas
associações. Fontes da ontologia não são baixadas. `sources` e `value_kinds`
são a superfície suportada pelo Libris, não declarações `rdfs:domain/range`.
Os limites históricos `minimum/maximum` continuam contratos canônicos da aplicação;
novas regras institucionais ficam em `CatalogPolicy`, nunca nesses limites.
Vocabulário/autoridade usam `ReferenceValue` e os contratos de valores controlados
(#24); enums usam `CatalogPolicy.allowed_values`. Não duplicamos sua validação.

### Integração com BIBFRAME e mapeamentos

Uma obra conserva `bf:Work` e sua URI, mesmo quando recebe `dcterms:abstract`.
O resumo é complementar ao título e às notas; não renomeia ou substitui `bf:note`.
Não há inferência baseada em prefixos, rótulos ou semelhança de nomes.

Nesta issue mapeamentos são especificações revisadas, sem motor executável.
Cada proposta deve identificar IRIs de origem/destino, classes de aplicação,
relação, evidência, responsável, release e eventual transformação. Relações:
`equivalent_property`, `equivalent_class`, `related`, `export`, `transformation`
e `no_equivalence`. Equivalência exige prova explícita; exportação não a implica.

Exemplos: `dcterms:abstract` e `bf:note` têm `no_equivalence` no modelo Libris:
um literal resumo não é o auxiliar estruturado de nota. Exportar `bf:mainTitle`
como `dcterms:title` seria `export`, com seleção do título, idioma e tratamento
de múltiplos títulos especificados. Converter `bf:note` em texto seria
`transformation`, com relatório de possíveis perdas e preservação do original.
Essas propostas não executam conversões nem geram `owl:sameAs`,
`owl:equivalentProperty` ou `owl:equivalentClass`; os testes verificam sua ausência.
Um contrato tipado executável só será necessário com um caso real de conversão.

## Perfis declarativos e validação

`work-extensions-2.0.0.json` é candidato, herda Work/core 2.0.0 e acrescenta resumo
textual, multilíngue, opcional, máximo de dois valores e idioma único. Apresentação
`textarea`, seção `description`, ordem 20 e rótulos pt/en são consumo futuro do editor.
O campo permite especialização da política; o teste deriva um perfil que exige
resumo, sem editar a release base ou transformar obrigatoriedade em axioma DCTERMS.

Os contratos existentes continuam responsáveis por cardinalidade coerente,
datatypes, condições, defaults, enums, grupos, ordem, herança, relações, referências
a shapes e vocabulários. `compare_profiles` considera adição opcional compatível
na mesma família; adição obrigatória, alterações de tipos/cardinalidades/destinos,
remoção de campos e mudança de associação SHACL exigem análise explícita.
Trocar de família não é declarado compatível apenas pela semelhança de campos.

Pydantic valida configuração; o registro valida autorização/compatibilidade;
`validate_resolved_profile` usa RDFLib/pySHACL e as mesmas shapes locais existentes.
`add_profile_constraints` já produz as regras adicionais do resumo sem condicional
DCTERMS. Shapes históricas permanecem intactas, sem `sh:closed`. Violation bloqueia;
Warning e Info são preservados no relatório e não bloqueiam por si sós.
Auxiliares/classes de destino, enums e valores controlados seguem #21/#24.
Não há download de ontologias, imports ou shapes indicadas por clientes.

Três conceitos independentes:

1. Preservar triplas RDF importadas: não descartar dados porque não são campos.
2. Autorizar novos campos: exige namespace, propriedade/classe e perfil aprovados.
3. Conformidade: avalia as regras do perfil escolhido; não certifica toda tripla
   complementar como homologada. Um grafo vazio pode ser vacuamente conforme;
   identidade e ownership são verificados pelo serviço/snapshot, não pelo targeting SHACL.

## Persistência, serialização e API

O Graph integral continua canônico. Snapshots JSON-LD expandidos em PostgreSQL
JSONB preservam triplas, idioma, datatype, IRIs e auxiliares. Revisões existentes
usam URI armazenada, revisão esperada, perfil original e proveniência. O serviço
recebe um grafo completo na revisão: o chamador deve preservar as triplas que
pretende manter; não é um patch que automaticamente combina o grafo anterior.

`prepare_document` e `BibliographicService` continuam aceitando apenas os perfis
legados de persistência. A demonstração 2.0 é executável por resolução/validação,
mas não passa a ser aceita implicitamente pela camada transacional. Extensões
RDF, incluindo resumo, já são preservadas por criação/revisão sob o perfil legado
institucional. O teste executa a preparação e o caminho real de revisão com
repositório simulado; não afirma execução PostgreSQL. Nenhuma mudança transacional,
de armazenamento ou migração foi necessária.

Interface atual de extensões: `parse_representation(document, format)` recebe
Turtle ou JSON-LD seguro e devolve Graph; `check_snapshot` valida ownership;
`load_profile_registry().resolve(release_id)` e `validate_resolved_profile`
validam o perfil; `serialize_graph` recupera o grafo integral. Termos externos
são identificados por IRI completa. Identidade não muda ao selecionar perfil.

DTOs Create/Read/Update de #15 continuam fechados. Não recebem `abstract` ou
propriedades arbitrárias por `extra=allow`, nem representam todo o Graph.
A conversão Read→Graph é uma projeção limitada; reconstruir um snapshot integral
somente a partir do DTO pode perder extensões. Para exportar, usar o Graph lido
pelo serviço. Não há rota pública de ingestão/catalogação ou descoberta de perfil;
uma futura rota deverá fixar release, permissões, validação e revisão esperada.

Next.js poderá descobrir campos autorizados pelo `ResolvedProfile`: IRI,
namespace, variante de valor, regras, fontes de vocabulário, seção/grupo/ordem,
rótulos e condições. A release semântica correspondente é recuperada no registro
por `semantic_registry_for`. Não foram alterados frontend ou formulários.

`serialize_graph` trabalha sobre cópia e verifica isomorfismo do round-trip.
`parse_representation` aceita somente o contexto embutido exato de bibframe-v1,
ou representação expandida com IRIs. Contextos remotos, imports e substituição de
aliases são rejeitados. O contexto já contém DCTERMS; `abstract` usa sua IRI,
sem nova release de contexto. Predicados não catalogáveis podem permanecer em
forma absoluta no Graph: isso é preservação, não autorização de edição nem
expansão de prefixos novos no contexto de entrada.

## Versionamento e governança

| Identificador | Significado nesta entrega |
| --- | --- |
| Formato semântico 1.1 | Estrutura Pydantic e schema, distinta do conteúdo |
| Ontologia de origem | Release declarada pelo mantenedor, texto ou ausência |
| Registro 1.0/2.0 | Snapshot local imutável de namespaces e termos suportados |
| Perfil 2.0.0 | Release candidata e lineage fixada, fingerprint independente |
| Shapes institucional 1.1 | Regras RDF locais mantidas; suplemento determinístico do perfil |
| Contexto bibframe-v1 | Aliases locais históricos, sem alterações |
| Revisão bibliográfica | Número, URI, proveniência e perfil usado por recurso |

Inclusão de namespace/termo exige revisão de IRI, fonte, significado, status,
risco de duplicação e compatibilidade; publicar novo registro, associar perfis e
fixar fingerprints. Homologação técnica permite a demonstração; homologação
institucional continua decisão dos mantenedores/catalogadores. Este ADR é a
referência de inclusão, não um registro de aprovação humana inventado.

| Mudança | Procedimento e compatibilidade |
| --- | --- |
| Namespace ou propriedade opcional | Nova release do registro/perfil; preservar históricos; testar adição |
| Propriedade obrigatória | Nova release de perfil; avaliar registros sem valor; migração explícita se adotada |
| Tipo, cardinalidade ou destino | Tratar como incompatível conservadoramente; novas releases e validação final |
| Atualização de ontologia | Não trocar IRIs nem revalidar automaticamente; revisar diff e suporte local |
| Depreciação | Status em nova release; recusar novos campos; manter triplas e registros históricos |
| Substituição | Nova IRI e especificação revisada de mapeamento; nunca substituição silenciosa |
| Mapeamento | Nova especificação/release com evidência e perdas; sem inferência automática |
| Alteração incompatível | Planejar, aprovar e auditar migração; manter revisões anteriores |

`check_extension_of` protege o caminho aditivo: não remove classes/propriedades
anteriores, não altera classificação de classes ou características semânticas
suportadas das propriedades, nem remapeia prefixos/ontologias. Metadados descritivos
e status podem evoluir em nova release; o snapshot anterior permanece disponível.
Uma alteração que exige modificar esses contratos não é uma extensão aditiva e
precisa de ADR/procedimento próprio, não de contornar o verificador.

Migração futura: selecionar revisões e releases de origem/destino, definir
transformação e relatório de perdas, validar antes e depois, preservar URI e
proveniência, gravar nova revisão com concorrência otimista e registrar decisão
humana. Nenhuma atualização de pacote dispara esse fluxo. Não implementamos
migrador genérico, raciocínio ontológico, editor RDF, cache remoto ou novas entidades.

## Exemplos e evidências

Fixtures executáveis: `tests/fixtures/bibliographic/extensions/work.ttl` e
`work.jsonld`. Contêm Work, Title privado, resumo pt, data tipada e um auxiliar
PROV. `dcterms:created` e `dcterms:provenance` demonstram preservação fora da edição;
não são declaradas campos aprovados no perfil. O teste confere isomorfismo,
validação do resumo e ausência de mutação do grafo.

```python
from libris.modules.bibliographic.domain.profile_contract import ProfileValidationContext
from libris.modules.bibliographic.infrastructure.profiles import load_profile_registry
from libris.modules.bibliographic.infrastructure.serialization import parse_representation, serialize_graph
from libris.modules.bibliographic.infrastructure.validation import validate_resolved_profile

release = "urn:libris:profile:work-extensions:2.0.0"
profile = load_profile_registry().resolve(release)
graph = parse_representation(document, "json-ld")  # document: fixture local autorizada
report = validate_resolved_profile(graph, profile, ProfileValidationContext(profile_release=release))
exported = serialize_graph(graph, format="turtle", root="https://example.org/works/123")
```

## Matriz dos critérios de aceitação

| Critério #25 | Evidência executável/documental |
| --- | --- |
| Registrar namespaces | SemanticRegistry 1.1; testes namespace_conflicts, governed_namespace_requires_traceability |
| Identificar classes/propriedades por URI | registered_terms_and_origin_without_new_entities; invalid_term_metadata |
| Combinar BIBFRAME e termos externos | work-extensions-2.0.0; examples_roundtrip_preserve_all_terms |
| Perfis configuráveis | required_extension_inherits_and_composes_without_ontology_cardinality; testes históricos declarativos |
| Validação semântica | shacl_external_policy_rejections; extension_warning_and_info_nonblocking |
| Preservação RDF/JSON-LD | examples_roundtrip_preserve_all_terms; owned_snapshot_and_revision_preserve_extension |
| Política de versionamento | semantic_release_tampering_rejected; historical_registry_and_profile_are_not_reinterpreted |
| Inclusão sem alterações invasivas | contratos reutilizados, predicados configurados e suplemento SHACL genérico |
| Interoperabilidade complementar | fixtures DCTERMS e PROV; isomorfismo JSON-LD/Turtle |
| Decisões compatíveis com M03 | ADR 0025; regressões #15–#24; DTOs e releases anteriores preservados |

Os resultados efetivamente executados e as limitações do ambiente são registrados
em `semantic-extensions-verification.md`.
