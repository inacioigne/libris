# Contrato de perfis declarativos — #20 / formato 2.0

Implementação técnica; exemplos candidatos/rascunho, sem homologação institucional.
[ADR 0021](../decisions/0021-declarative-catalog-profiles.md).
Configurações descrevem edição de Graph RDFLib canônico, não registros bibliográficos,
DTOs de recursos, banco de dados ou um segundo modelo de entidades.

## Diagnóstico e pré-requisitos

Reutilizados ProfileField/ProfileResource/CatalogProfile, entidades e auxiliares dos
ADRs 0009–0015, validação de IRIs, EntityType/DEFAULT_REGISTRY, shapes locais e
pySHACL. Faltavam metadados de família/release, composição/seleção, tipos discriminados
e separação entre formulário e política catalográfica. O formato experimental v1
não satisfazia o descritor candidato atual; recebeu adaptador explícito de leitura.

Foram consultadas #14–#18 e #20–#22/#24/#25/#27/#30/#31. #14 retornou estado fechado
sem descrição; #15–#18 têm contratos implementados localmente; #21 detalha a evolução
de SHACL. As demais integrações posteriores retornaram título/estado e corpo vazio:
o escopo abaixo segue os títulos e os contratos locais, sem inventar requisitos.

## Modelos, responsabilidades e artefatos

| Componente | Responsabilidade |
| --- | --- |
| domain/profiles.py | Preserva modelos/aliases legados e publica ProfileDefinition/ResolvedProfile |
| domain/profile_contract.py | Pydantic v2: metadados, variantes, políticas, apresentação, condições e contexto |
| domain/profile_registry.py | Registro semântico/SHACL, resolução pura, seleção, evolução e erros de domínio |
| infrastructure/profiles.py | Manifest do pacote e adaptador de leitura histórica; nunca paths do cliente |
| infrastructure/validation.py | Adaptador de referências versionadas e correlação; mesmo motor pySHACL |
| resources/profiles-v2/ | Dez definições, manifest, registros locais e quatro JSON Schemas gerados |
| scripts/generate_profile_artifacts.py | Geração/verificação reproduzível dos schemas e exemplos públicos |
| docs/examples/profiles/ | Definições normalizadas e payload resolvido de monografia |
| tests/fixtures/bibliographic/profiles/ | Casos inválidos, hashes históricos e inventário BIBFRAME revisado |

Domínio não importa HTTP, API, ORM, infraestrutura, rede ou arquivos. Erros
estruturais são ValidationError Pydantic; erros de interpretação são ProfileError
com code estável. Esses códigos ainda não são a resposta HTTP definitiva da #22.

## Identidade, versões e ciclo de vida

| Atributo | Significado |
| --- | --- |
| format / format_version | libris.catalog-profile / 2.0; contrato declarativo |
| id | Família estável, por exemplo urn:libris:profile:monograph |
| release_id | Identidade inequívoca da release, por exemplo urn:libris:profile:monograph:2.0.0 |
| release | Número da release do perfil; não edição bibliográfica/revisão RDF |
| bibliographic_contract | 1.0, superfície canônica já implementada |
| validation[].id/release/context | Conjunto SHACL fixado separadamente, por snapshot/composição |
| namespaces[].release | Release local revisada do registro de vocabulário; bf fixa o inventário 2.0.1 |

Os identificadores antigos continuam sendo **IDs de releases históricas**, sem nova
interpretação como famílias. O novo formato exige id e release_id distintos.
Versões numéricas têm dois ou três componentes; a identidade operacional sempre
é release_id, nunca somente um número de versão ou nome de arquivo.

category=system identifica configuração comum do sistema; institutional exige
institution (IRI); specialization exige base_release. Especializações podem ter
contexto institucional e restringem aplicabilidade/tipo/finalidade da base.
resource_types são IRIs de classificação documental para seleção, não classes RDF
inventadas; os exemplos usam urn:libris:resource-type:monograph/serial/digital.

Estados: draft admite revisão quando não usado nem fixado por descendente; candidate
fixa conteúdo para revisão; published é disponibilizável por padrão; deprecated
preserva leitura histórica e é excluído da seleção padrão. Transições explícitas
são draft→candidate, candidate→published/deprecated e published→deprecated.
transition_release retorna um **novo snapshot do registro**, mudando apenas
status/replacement. Conteúdo, campos e shapes permanecem iguais; o registro anterior
permanece intacto. Não é persistência de workflow administrativo. Uma publicação
institucional real exige homologação e retenção dos artefatos/bases correspondentes.

replace_draft rejeita modificação de candidata/publicada/descontinuada, de release
usada e de qualquer base fixada em composição. add_release rejeita ID ou versão de
família duplicados. Mudança de conteúdo exige outra release_id/release. replacement
exige sucessora existente da mesma família, sem ciclos; não é seguido silenciosamente.
A recuperação resolve sempre a release solicitada, mesmo descontinuada. Seleção
para nova catalogação confere estado/contexto; falha em vez de substituir a release.

## Campos e separação de regras

Cada recurso tem rdf_class, entity opcional, label, sections, groups e fields.
Work/Instance/Item usam classes BIBFRAME; Agent inclui Agent/Person/Organization;
Subject usa skos:Concept. entity ausente identifica descritor de auxiliar privado.
O núcleo compartilhado contém descritores dos cinco tipos; um perfil especializado
restringe applies_to, sem duplicar os descritores. O frontend deve escolher raízes
que correspondam a applies_to e expandir somente auxiliares referenciados.

Campos: name local, property absoluta, namespace alias, label/description
multilíngues, value, policy, presentation, derived, validation e overrides.
Identidade semântica é a URI inteira, não prefixo/nome local. Names e IDs de seções
são tokens em inglês; chaves de traduções/tags seguem sintaxe estrutural compatível
com RDFLib (sem consulta IANA). Rótulos não selecionam nem identificam releases.

1. **Contrato/domínio:** registro confiável autoriza propriedade, origem, destino,
   tipo de nó/valor, datatype, derivação e limites da superfície Libris. O registro
   de relacionamentos existente impede misturar destinos de Work/Instance quando
   compartilham bf:relatedTo. Máximo 1 de instanceOf/itemOf é limite do contrato de
   edição atual, não axioma ontológico universal.
2. **Catalogação:** policy.min_count/max_count/repeatable/required,
   allowed_values/default e specializable. required corresponde a mínimo positivo;
   repeatable corresponde a máximo diferente de 1. Especialização autorizada somente
   restringe mínimos, máximos e valores permitidos; não relaxa a base/domínio.
3. **Apresentação:** input, order, section/group, visible/editable,
   required_in_form, help e conditions. required_in_form pode ser diferente de
   policy.required. Não muda a cardinalidade RDF. Campos derived não são editáveis
   e não recebem default; inversas permanecem derivadas fora do snapshot proprietário.

No formato antigo requiredInForm=(minCount>0), repeatable=(maxCount!=1),
absent=violation/omit segundo minCount. Esses invariantes continuam exigidos pelos
modelos antigos. O novo contrato separa required_in_form da política, mantendo
cardinalidade/repetibilidade coerentes. Ausência opcional não inventa tripla.
Default é sugestão validada; não é aplicado automaticamente ao grafo nem supre
sozinho um mínimo maior que 1. Políticas não são geradas como shapes nesta issue.

## Variantes RDF, controles e condições

| value.kind | Nó/estrutura | Controles suportados |
| --- | --- | --- |
| text | Literal textual; LanguagePolicy enabled/required/allowed/unique | text, textarea, select |
| typed | Literal com datatype RDF explícito | text, number, boolean, date, select |
| iri | Referência genérica, sem descrição embutida | reference, select |
| entity / relationship | IRI de entidade com target_entities/classes compatíveis | reference, select |
| authority | IRI de Agent/Subject e fonte authority obrigatória | reference, select |
| vocabulary | IRI de termo e fonte vocabulary obrigatória | reference, select |
| structured | BlankNodeOrIRI e target_classes de auxiliares definidos | structured |

Referências conservam IRI; local/externa/não reconciliada continuam contratos de
#16/#17, não são deduzidas pelo prefixo. Não gerar identidades para auxiliares nem
embutir autoridades. Title/VariantTitle usam mainTitle/subtitle com idioma;
Contribution conserva agent/role; Identifier/Local/Isbn conserva rdf:value/source;
Publication é a variante suportada de bf:ProvisionActivity, conservando agent/place/date.
Não se adicionam tipos ISSN ou subclasses arbitrárias aos DTOs existentes.

LiteralDefault contém kind=literal, value lexical textual e language **ou** datatype;
IRIDefault contém kind=iri e iri. Números/booleanos usam lexicais RDF explícitos,
sem coercão para strings. Defaults/enums verificam datatype, idioma, classe de valor
e pertença ao enum. Não se aceitam defaults escalares de auxiliares estruturados.
Datatypes suportados: xsd:string/integer/decimal/double/boolean/date/dateTime/gYear.
Defaults de data usam calendário gregoriano 0001–9999; isso é limite do componente
atual, não de RDF. Datas transcritas continuam possíveis via xsd:string.

Conditions são declarativas: field do mesmo recurso, operator=present/absent/equals,
effect=visible/editable/required; somente equals recebe value discriminado e válido
para a dependência. Dependências ausentes, autorreferências e ciclos são rejeitados.
Não há expressões, eval, JavaScript ou chamadas externas. São instruções para o
formulário futuro, não constraints SHACL condicionais. A
[validação SHACL da #21](shacl-validation.md) aplica políticas catalográficas
expressíveis; condições de apresentação continuam separadas.

## Composição e seleção determinísticas

base_release é herança simples; toda a base resolvida é reutilizada. Merge por
rdf_class, fields por name. Mesmo predicado com outro name é conflito, não alias.
Campos existentes exigem overrides=true; URI, valor/nó, namespace, derivação e
vínculos SHACL devem permanecer iguais. presentation/label/description podem mudar.
policy só muda se specializable autorizar, sempre restringindo. Campo novo exige
propriedade/componente já registrado. Seções/grupos são substituídos por ID.
Ordenação efetiva: recursos por URI; campos por order/name; seções/grupos por order/id;
shapes por id/context. Referências desconhecidas e ciclos falham antes da exposição.
Recursão auxiliar de formulário também é rejeitada.

ProfileRegistry.definition/release_id retorna entrada; resolve retorna
libris.resolved-profile 2.0, lineage com releases fixadas, recursos efetivos e
validation herdada. Releases fixadas no pacote têm fingerprints SHA-256 em release-lock.json, incluindo
as bases transitivas. O carregador rejeita conteúdo alterado, remoção de release
fixada ou dependência sem fingerprint. Status/replacement são disponibilidade,
excluídos do digest semântico. O gerador só acrescenta locks novos e recusa substituir
um digest existente, inclusive quando chamado com --lock-new-releases.
Instâncias de entrada/saída são copiadas, evitando mutação
indireta do registro pelos dicionários de tradução. Não há cache persistente nem
promessa de gerenciamento dinâmico. Perfis usam a mesma classe Python, configurada
por JSON; novas subclasses não são necessárias.

candidates filtra entidade, resource_type, purpose, institution e statuses.
Seleção padrão usa published; candidatos exigem inclusão explícita nos estados.
Precedência: instituição específica, tipo documental específico, priority maior,
especialização mais profunda, id de família, versão numérica maior e release_id.
Não há preferência implícita por label/filename. Pedido explícito confere
aplicabilidade/estado e nunca escolhe outra release.

## Como criar e especializar

Use o exemplo completo independente
[work-minimal-2.0.0.json](../examples/profiles/work-minimal-2.0.0.json).
Ele declara Work e Title, seções, cardinalidade, idioma, autoridade, relacionamento e a release SHACL. O
[núcleo](../examples/profiles/core-2.0.0.json) contempla as cinco entidades e auxiliares.
[monograph](../examples/profiles/monograph-2.0.0.json) reorganiza o título herdado;
[serial](../examples/profiles/serial-2.0.0.json) acrescenta bf:frequency por IRI de
vocabulário; [digital](../examples/profiles/digital-2.0.0.json) acrescenta
schema:encodingFormat controlado, schema:dateCreated tipado e condição sobre carrier.
Todos são carregados/testados; tipos documentais não criam um novo modelo de registro.

Especialização mínima válida da configuração compartilhada (mesmo mecanismo dos
cinco exemplos de entidade, sem repetir campos):

```json
{
  "format": "libris.catalog-profile", "format_version": "2.0",
  "id": "urn:example:profile:work", "release_id": "urn:example:profile:work:1.0.0",
  "release": "1.0.0", "bibliographic_contract": "1.0",
  "status": "draft", "category": "specialization",
  "label": {"pt": "Obras da instituição"},
  "description": {"pt": "Reutiliza a release candidata do núcleo."},
  "applies_to": ["Work"], "base_release": "urn:libris:profile:core:2.0.0"
}
```

Procedimento: escolher entidade/classe e propriedades do registro local; declarar
auxiliares ou herdar base com suas definições; escolher idiomas, políticas e controles;
fixar referências SHACL; validar Pydantic e resolver no registro completo; gerar e
verificar artefatos; revisar diffs/homologar; publicar outra release sem substituir
arquivos já usados. Campos novos registrados não exigem código; novos mecanismos
de nó/controle/datatype exigem adaptação deliberada. O manifest é configuração
confiável do pacote, não um upload de caminho/URL fornecido por cliente.

Exemplos inválidos completos estão em `tests/fixtures/bibliographic/profiles/invalid/`.
Trechos que **não** podem substituir atributos do exemplo:

```json
{"property": "relative-title"}
```

```json
{"policy": {"min_count": 2, "max_count": 1, "repeatable": false, "required": true}}
```

```json
{"base_release": "urn:missing:release"}
```

Os dois primeiros falham estruturalmente; o terceiro falha durante resolução.
O schema cobre tipos/discriminadores/extras/limites locais; não cobre completamente
relações entre campos, registros, herança, imutabilidade ou compatibilidade RDF.

## Extensibilidade controlada

semantics-v1.json registra namespaces, classes e propriedades, com fontes/destinos
suportados. Prefixos são aliases; propriedades de mesmo nome local em namespaces
diferentes não colidem. Não aceitar registro semântico de um request não confiável.
unknown_namespace/namespace_mismatch/unknown_property diferenciam falhas de registro;
incompatible_property/incompatible_target/incompatible_datatype impedem combinações
fora da superfície; unsupported_property/extension_review_required indicam termos
obsoletos ou sem adaptação homologada. schema:fileFormat é registrado como obsoleto.

Para outra ontologia, incluir registro local revisado com URI, origem/destino/tipo
já suportados e release; instanciar SemanticRegistry e ProfileRegistry. Não há plugin
com descoberta automática. Não substituir BIBFRAME/SKOS nem cadastrar namespaces
sobrepostos. Descrever explicitamente o que necessita de #25 ou mapeamento de DTO.
A URI integral, idioma, datatype e estruturas permitem RDF/JSON-LD sem perda;
exportação de snapshots continua integral. Campos externos dos exemplos orientam
edição RDF futura; não passam a existir magicamente nos Create/Read atuais da #15.

Termos BIBFRAME conferidos no
[RDF oficial 2.0.1 arquivado](https://github.com/lcnetdev/bibframe-ontology/blob/main/archive/bibframe-2.0.1.rdf).
Os termos externos digitais seguem [encodingFormat](https://schema.org/encodingFormat)
e [dateCreated](https://schema.org/dateCreated). O inventário local é explícito;
nenhuma consulta à ontologia ocorre ao carregar ou validar um perfil/registro.

## Integração SHACL e erros

validation liga id/release/context a ShapeRegistry. FieldConstraint liga campo a
shape_id/shape_release e property_shape opcional conhecida. URI property liga
resultPath ao descritor. O conjunto institucional 1.1 usa os artefatos existentes de
monografia/autoridades; contexto composto acrescenta monograph-v1.1-composed.ttl.
Registro semântico não copia constraints qualificadas/idiomas/consultas das shapes.

ProfileValidationContext fixa profile_release, mode=snapshot/composed e referências
opcionais dos snapshots selecionados (URI/revisão/release). Não carrega snapshots
ou verifica existência no banco. O chamador fornece Graph já preparado pela
aplicação/ownership e suas revisões explicitamente; não combina revisões atuais
com histórico por iniciativa própria. Grafo vazio pode ser conforme por vacuidade;
o serviço existente continua exigindo raiz/ownership antes de persistir.

validate_resolved_profile verifica release/contexto e mapeia somente conjuntos
locais permitidos, usando o mesmo _validate_shapes/pySHACL. Snapshot não aplica
shapes apenas compostas; modo composto aplica snapshot e verificações inversas.
Sem downloads, paths arbitrários, inferência, imports, JS ou advanced. Novo conjunto
precisa de registro/revisão local e mapeamento seguro de infraestrutura; cadastro
puramente declarativo não autoriza carregar um arquivo arbitrário.

correlate_validation_issues conserva ValidationIssue e retorna field_ids qualificados
por classe/name. Considera rdf:type do nó focal, inclusive blank node; uma propriedade
fora do formulário, classe desconhecida ou caminho complexo mantém field_ids=[] e
erro em nível de registro. Não descartar o erro nem associar por rótulo aproximado.
Warnings/Info continuam reportados sem bloqueio; Violation bloqueia a conformidade.

A #21 acrescenta [constraints suplementares determinísticas](shacl-validation.md)
para min/max, tipos, datatypes, idiomas e enums do contrato 2.0, usando o mesmo
pySHACL. Presentation/conditions/default continuam sem efeito automático no RDF.
Configurações contraditórias com fontes locais são rejeitadas; shapes históricas e
chamadas validate_profile permanecem intactas. Ver ADR 0022 para justificativa,
limites e rastreabilidade. A #22 define o envelope/códigos HTTP finais. Nenhum
perfil v2 foi integrado à escrita persistente do BibliographicService.

## Evolução e compatibilidade

compare_profiles compara respostas resolvidas; classificação conservadora:

| Mudança | Classificação |
| --- | --- |
| Campo opcional novo | Compatível com registros; consumidor antigo pode não editar o campo |
| Campo obrigatório novo / remoção | Incompatível |
| URI, datatype, tipo de nó/destino ou vocabulário | Incompatível |
| Cardinalidade / enum / default / policy | Incompatível conservadoramente, mesmo em relaxamento entre famílias |
| Rótulo, descrição, ordem, seção/grupo/apresentação | Compatível no conteúdo RDF |
| Associação SHACL, contrato, aplicabilidade/contexto | Incompatível; requer revisão explícita |
| Depreciação | Retira seleção ativa; conteúdo histórico continua recuperável |
| Nova release | Coexiste; nunca altera automaticamente perfil de um registro |

Status/disponibilidade não migra conteúdo. Necessidade de migração deve produzir
procedimento explícito, auditável, com mapeamento, identidades preservadas, revisão
esperada/CAS, proveniência e validação final; não foi implementado. EditionStatement
é edição bibliográfica, release é configuração e revision é histórico do recurso.

Os sete artefatos legados e catalog-profile.schema.json permanecem byte a byte.
load_legacy_profile devolve CatalogProfile para IDs históricos. Só o v1 recebe valores
faltantes da visão antiga: nomes por propriedade, label de classe, cardinalidade
conforme requiredInForm/repeatable, datatype de data e status/release descritivos.
Esses preenchimentos não mudam shapes nem afirmam que são constraints RDF completas.
O serviço antigo continua validando cada ID com seus arquivos históricos originais.

## Backend, OpenAPI e Next.js futuros

```python
from libris.modules.bibliographic.domain.relationships import EntityType
from libris.modules.bibliographic.infrastructure.profiles import load_profile_registry

registry = load_profile_registry()
profile = registry.select(
    EntityType.WORK,
    release_id="urn:libris:profile:monograph:2.0.0",
    resource_type="urn:libris:resource-type:monograph",
    institution="urn:libris:institution:example",
    statuses=("candidate",),
)
response = profile.model_dump(mode="json")
```

Payload integral de resposta:
[monograph-2.0.0.resolved.json](../examples/profiles/monograph-2.0.0.resolved.json).
Inclui identidade, metadados, lineage, classes/auxiliares, campos, seções/grupos,
valores discriminados, política, apresentação e releases SHACL. Não contém ORM,
colunas de tabelas ou dados do registro. Schema/OpenAPI distingue entrada/resposta.

| Endpoint candidato, não registrado | Contrato |
| --- | --- |
| GET /api/v1/catalog-profiles?entity=&resource_type=&institution=&purpose=&status= | Lista de metadados e IDs; filtros explícitos/ordem de candidates |
| GET /api/v1/catalog-profile-releases?release_id=IRI | ProfileDefinition, inclusive histórico/descontinuado |
| GET /api/v1/catalog-profile-releases/resolved?release_id=IRI | ResolvedProfile; nenhuma troca silenciosa |
| POST /api/v1/catalog-profiles/interpret | Possível validação/resolução administrativa futura, com registro confiável |

Não implementar CRUD administrativo nesta etapa. A aplicação futura deve aplicar
permissões e traduzir unknown_release/inapplicable_profile/no_profile de maneira
compatível com #22. Campos extras/malformados são ValidationError estruturais;
nenhuma resposta HTTP nova foi fixada. Os testes geram OpenAPI numa FastAPI isolada.

Next.js deverá escolher classe raiz/locale, ordenar seções/grupos/campos e interpretar
os controles declarados, preservando idiomas, valores lexicais, nós auxiliares e
referências. Não transformar structured em string, não persistir derived nem usar
rótulos como identidade. Os dados catalográficos usam contratos/RDF existentes;
a definição de perfil não é o body de WorkCreate. Condições só orientam formulário,
e o backend revalida política/RDF antes da escrita futura. Formulários/editor,
React e páginas administrativas não foram implementados.

## Geração, testes e próximas integrações

Da pasta apps/api:

```bash
uv run python ../../scripts/generate_profile_artifacts.py
# Após revisão de candidatas novas: acrescentar locks; nunca sobrescrever os antigos.
uv run python ../../scripts/generate_profile_artifacts.py --lock-new-releases
uv run python ../../scripts/generate_profile_artifacts.py --check
uv run pytest ../../tests/api/test_declarative_profiles.py
uv run pytest
uv run ruff check . ../../tests
uv run mypy src
```

Schemas gerados por Pydantic; não editar manualmente. O modo --check compara bytes
determinísticos de quatro schemas e seis exemplos. A suíte também confere igualdade
do schema antigo, round-trips e hashes de releases históricas. Na raiz,
`bash scripts/check.sh` reúne backend, frontend e Compose. Se uv/Snap não executar,
usar o ambiente sincronizado .venv/bin; resultados/limites reais estão no
[relatório de verificação](catalog-profiles-verification.md).

[#21](shacl-validation.md): correspondência policy/SHACL e diagnóstico completo implementados;
#22: respostas/erros;
#24: vocabulários/autoridades/pertinência e políticas de valores; #25: extensão de
ontologias/componentes novos; #27: estados de **registros**, diferentes dos perfis;
#30: ampliar/reutilizar corpus; #31: consolidar documentação/versionamento.
Integração PostgreSQL, APIs definitivas, migração MARC, indexação, armazenamento
RDF adicional, reconciliação externa e administração permanecem fora do escopo.
