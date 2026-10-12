# Erros e validação catalográfica — #22 / contrato 1.0

A implementação reutiliza o mesmo Graph RDFLib, pySHACL e registros locais das
#15/#17/#19/#20/#21. [ADR 0023](../decisions/0023-catalogographic-diagnostics.md).
A [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) define o envelope HTTP e
`application/problem+json`; os códigos abaixo pertencem ao domínio Libris.

## Inventário e integração efetiva

ValidationIssue/ValidationReport já conservavam termos, mensagens, severidades,
shape, constraint e valor; FieldValidationIssue/correlate_validation_issues já
associavam múltiplos campos por rdf:type/resultPath. validate_monograph,
validate_profile e validate_resolved_profile mantêm suas assinaturas/semântica.
Não foram duplicados validadores nem alterados perfis/shapes versionados.

Novos contratos neutros ao transporte ficam em application/diagnostics.py, com
nomes públicos reexportados em api/schemas/diagnostics.py. O adaptador de RDF fica
em infrastructure/diagnostics.py; validate_catalog coordena pré-validação interna.
prepare_document rejeita não conformidade com CatalogValidationRejected e o relatório
público, antes de create abrir transação ou dentro de revise após CAS. Continua
compatível com captura ValueError. Ownership/referências usam CatalogError tipado;
ausência persistente usa ResourceNotFoundError, subclasse de LookupError.

create_app instala handlers, middleware de correlação e documentação OpenAPI reais.
HTTP 404, autenticação e validação estrutural usam Problem Details. Health permanece
200 JSON. Nenhum endpoint de catálogo/pré-validação foi criado; exemplos de rotas
em testes e abaixo demonstram integração futura, não disponibilidade no produto.

## Schemas

CatalogValidationResult:

| Campo | Significado |
| --- | --- |
| contract_version | Literal `1.0`, versão deste contrato |
| state | `completed` ou `failed` |
| conforms | Booleano obrigatório em completed; omitido em failed |
| profile_id | Família 2.0; ID histórico original para perfil legado |
| profile_release | ID imutável da release realmente utilizada |
| profile_version | Release numérica do perfil, distinta da versão SHACL/contrato |
| context | `snapshot` ou `composed`, contexto do grafo fornecido |
| request_id | UUID da requisição; opcional fora de HTTP |
| issues | Lista ordenada de Diagnostic, inclusive warnings/info/globais |

Diagnostic:

| Campo | Significado |
| --- | --- |
| code / message | Código independente de idioma e mensagem pública legível |
| category | schema, semantic, profile, identity, reference, state ou technical |
| severity | Violation, Warning ou Info |
| field_ids | Zero, um ou múltiplos identificadores, ordenados/sem duplicatas |
| path | RdfPath estruturado da propriedade, quando disponível |
| focus_node | IRI exata segura ou identificação anônima local ao diagnóstico |
| value | Somente IRI segura; literais sempre omitidos |
| constraint | URI do sourceConstraintComponent original, quando segura |
| source_shape | Shape IRI ou identificação anônima, quando disponível |
| messages | Mensagens autorais fixas SHACL seguras; nenhuma mensagem dinâmica refletida |
| parameters | Parâmetros estruturados para tradução; component para componentes conhecidos |

Nenhum termo RDFLib, Graph, objeto pySHACL, input/context Pydantic ou exceção é
serializado. RdfPath usa kind=iri (iri inteira), sequence/alternative (items),
inverse/zero_or_more/one_or_more/zero_or_one (um item), ou opaque (identifier).
Recursão além de 16 níveis, listas cíclicas ou mais de 64 itens permanecem opaque;
o diagnóstico é mantido global. Não resolver caminhos/referências externamente.

## Estado e conformidade

- completed + conforms=true: execução confiável; sem Violation. Pode conter Warning/Info.
- completed + conforms=false: execução confiável; dados não conformes.
- failed: execução técnica falhou; conforms é omitido e somente diagnósticos técnicos
  são permitidos. Nunca interpretar omissão como true.

A escrita exige conformidade, bloqueia Violation e preserva exceção técnica original.
Warning/Info sozinhos não bloqueiam, conforme allow_warnings/allow_infos existente.
Não modificar regras de apresentação/required_in_form para torná-las SHACL.
Grafo vazio pode ser conforme por vacuidade; ownership/raiz continuam necessários
para persistência. SHACL não prova existência de referências no banco.

validate_catalog aceita IDs históricos ou ResolvedProfile do registro confiável,
com release/contexto explícitos. Nunca aceitar um ResolvedProfile arbitrário vindo
do cliente. Falhas conhecidas do motor viram state=failed na pré-validação; erros
sobre perfil/entrada permanecem exceções tipadas, mapeáveis no HTTP. Falhas de
programação não são convertidas em resultados SHACL. A escrita ainda usa apenas
os três perfis históricos; perfis declarativos não foram adotados silenciosamente.

## Taxonomia e evolução

| Código | Situação / origem confiável |
| --- | --- |
| request.malformed | JSON malformado, RDF inválido/limitado, If-Match inválido |
| schema.invalid | Estrutura Pydantic não suportada ou inconsistência genérica |
| schema.required | Tipo Pydantic missing |
| schema.cardinality | Tipos Pydantic too_short/too_long |
| schema.value | Tipos Pydantic de valor incompatível conhecidos |
| shacl.violation | SHACL genérico; componente ausente ou não classificado |
| shacl.min_count / max_count | MinCountConstraintComponent / MaxCountConstraintComponent |
| shacl.qualified_min_count / qualified_max_count | Componentes qualified de cardinalidade |
| shacl.datatype / node_kind / class / in | Componentes SHACL exatos correspondentes |
| profile.unknown | Perfil/release inexistente |
| profile.incompatible | Contexto, aplicabilidade, release ou shapes contraditórias |
| profile.unavailable | Perfil local indisponível ou nenhuma seleção aplicável |
| profile.policy | Restrição de configuração/política de perfil não especializada |
| identity.invalid / reference.invalid | Ownership/identidade e integridade de referências |
| resource.unknown | Recurso/revisão inexistente |
| state.conflict | Integridade, identidade de release ou estado incompatível |
| revision.stale | Precondição obsoleta ou CAS rejeitado |
| revision.precondition_required | If-Match obrigatório ausente |
| validation.rejected | Operação rejeitada por relatório não conforme |
| validator.failure | Motor, shapes/configuração interna inválida, falha de execução |
| infrastructure.unavailable | Shapes temporariamente indisponíveis ou conexão DB indisponível |
| internal.failure | Falha inesperada, inclusive ValueError/KeyError não tipados |

Componentes são comparados por URI, nunca pelo texto da mensagem. Componentes
não catalogados preservam URI e recebem código genérico; não inferir cardinalidade
mínima zero versus campo ausente nem classificar sh:Node pelo conteúdo de mensagens.
Falhas internas malformed_shapes e engine_failure compartilham validator.failure;
a classificação pública não depende de heurísticas textuais internas legadas.
Códigos profile existentes são traduzidos por mapa explícito; demais ProfileError
recebem profile.policy. O código original não é exposto indiscriminadamente.

Campos/códigos novos são aditivos em 1.x; clientes ignoram atributos desconhecidos,
aceitam códigos desconhecidos e exibem message como fallback. Não reaproveitar
um código para outro significado. Remoções/mudanças incompatíveis exigem nova major,
novo contrato e novos URIs de type. Perfis/releases mantêm versões independentes.

## Associação, ordenação e serialização

IDs RDF de campo são `rdf_class/name` completos, definidos pelo perfil. Um foco
com várias classes pode afetar vários campos. Caminho simples + classe desconhecida,
caminho complexo ou propriedade não editável mantém field_ids=[] e erro global.
Não associar por rótulo. A correlação legado reproduz a mesma regra usando descritores
históricos, sem reinterpretar cardinalidades de v1. Erros estruturais usam JSON
Pointer dos campos DTO, como `/title/0/main_title`; não afirmar que o nome DTO é
igual ao identificador RDF. Extras inválidos não refletem o nome recebido.

Severidade ordena Violation, Warning, Info; dentro de cada grupo, chave é o JSON
canônico do diagnóstico completo, com chaves ordenadas e sem espaços. Preserva
multiplicidade. field_ids/messages são ordenados e deduplicados. Identificadores
anônimos usam descrições RDF canonizadas, com valores literais redigidos antes do
digest, não rótulos arbitrários do parser. São escopados ao relatório, não IDs de
regras ou entidades; nós estruturalmente indistinguíveis podem ter o mesmo digest.
Ausência de descrição de shape não inventa constraint identificável globalmente.

public_dict/public_json usam exclude_none=True; listas vazias e parameters={} são
mantidos. public_json ordena chaves com UTF-8 e separadores compactos. Uma rota
futura que devolva response_model deve usar response_model_exclude_none=True.
A igualdade de grafos continua usando isomorfismo, não comparação JSON/Turtle.

## Problem Details e exceções HTTP

ProblemDetails usa type=`urn:libris:problem:v1:{code}`, title padrão HTTP, status
igual ao status real, detail fixo e seguro, instance=`urn:uuid:{request_id}`.
Extensões: contract_version, code, request_id, issues e validation opcional.
Validação que rejeita escrita inclui o relatório em validation e issues; um
relatório de pré-validação normal pode ser retornado 200 sem Problem Details.

| HTTP | Exceção / situação aplicada |
| --- | --- |
| 400 | RdfDocumentError, JSON malformado, CatalogError request.malformed |
| 404 | ResourceNotFoundError, ProfileError unknown_profile/unknown_release, HTTP 404 |
| 409 | CatalogError state.conflict; estados imutáveis; PostgreSQL 23505/23503 |
| 412 | StaleRevisionError, incluindo CAS e comparação de ETag forte |
| 422 | RequestValidationError estrutural, CatalogValidationRejected, CatalogError de dados/perfil/referência |
| 428 | CatalogError revision.precondition_required |
| 500 | ShaclValidationError interna, configuração de shapes inválida, exceção inesperada |
| 503 | Shapes indisponíveis, perfil indisponível, DBAPIError com conexão invalidada/SQLSTATE de indisponibilidade |

DBAPIError só vira 409 para IntegrityError com SQLSTATE 23505/23503; somente
conexão invalidada, classe 08 ou 57P01/57P02/57P03/53300 vira 503. Outros erros
SQL continuam 500: não transformar programação/DDL/configuração em erro de usuário.
HTTPException também preserva status e headers existentes (incluindo WWW-Authenticate),
mas substitui detail recebido por mensagem segura. 401/403 recebem códigos de
identidade; não altera política OIDC já existente. Todas as respostas Problem
Details usam application/problem+json. OpenAPI real inclui schemas e respostas
com esse media type; respostas globais representam o contrato dos handlers, não
prometem que health execute operações de escrita. Rotas reais continuam health/me.

require_if_match(value, current_etag=...) é adaptador reutilizável de API futura:
428 ausente, 400 formato fraco/lista/curinga/token não delimitado, 412 forte obsoleto.
ETag atual deve ser forte e específico da representação fornecida pelo chamador.
Não gera ETag de Revision.concurrency_token nem devolve expected_revision. A futura
API deve validar a representação e obter a revisão antes de chamar revise; CAS
continua o árbitro final. Nenhuma escrita HTTP ou ETag publicado foi acrescentado.

## Segurança e observabilidade

Literais problemáticos sempre omitidos, sem truncamento parcial que revelaria
prefixos pessoais. IRIs são preservadas integralmente somente para http/https/urn,
sem query, credenciais, caracteres de controle/espaço ou mais de 2048 caracteres;
casos recusados são omitidos, nunca transformados em outra identidade. IRIs de
entidades também podem conter dados pessoais: fornecer somente grafos autorizados;
esta política não substitui controle de acesso/catalogação institucional.

message vem de templates fixos por código; messages conserva somente mensagens
SHACL fixas autorais do pacote (cache de metadados imutáveis). Valores/defaults
refletidos pelo motor, mensagens arbitrárias de exceções e contextos/input Pydantic
não são expostos. Falta/sintaxe inválida de metadado auxiliar de mensagem não
invalida uma execução SHACL já bem-sucedida; a mensagem fica omitida.

X-Request-ID aceita UUID normalizado ou gera UUID uma única vez. ContextVar oferece
o mesmo ID aos serviços; fora de HTTP pode-se fornecer request_id ou omiti-lo.
Cabeçalho é exposto por CORS. Middleware reseta contexto ao encerrar requisição;
o handler de 500 usa ID guardado no scope mesmo depois desse reset. instance não
reflete paths, queries, credenciais ou conteúdo recebido. Logs HTTP técnicos
registram ID, tipo de exceção e locais internos de execução, sem texto da exceção,
SQL, parâmetros, tokens ou locals. Pré-validação registra ID e código técnico.
Não há stack trace/configuração/caminhos locais no payload público.

Transações continuam nos serviços: create valida antes da transação; revise valida
entre avanço CAS e inserção, com rollback automático em rejeição/falha técnica.
Nenhuma rota controla commit. Testes reais verificam que revisão inválida não
consome número nem altera snapshot/histórico.

## Exemplos e integração futura

Arquivos JSON produzidos pelos contratos reais em [examples/validation](../examples/validation/):
[conforme](../examples/validation/conformant.json),
[warnings](../examples/validation/warnings.json),
[violações](../examples/validation/violations.json),
[estrutura](../examples/validation/schema-error.json),
[perfil desconhecido](../examples/validation/unknown-profile.json),
[revisão obsoleta](../examples/validation/stale-revision.json),
[falha operacional](../examples/validation/operational-failure.json).
Os exemplos são sintéticos; request_id fixo identifica documentação, não chamada real.

Uso interno implementado:

```python
from libris.modules.bibliographic.application.validation import validate_catalog
from libris.modules.bibliographic.infrastructure.profiles import load_profile_registry

profile = load_profile_registry().resolve("urn:libris:profile:monograph:2.0.0")
result = validate_catalog(graph, profile, context="snapshot")
print(result.public_json())
```

Exemplo FastAPI **futuro**, com graph/profile fornecidos pela aplicação após parsing
limitado e resolução confiável; não registrar endpoint de demonstração no produto:

```python
from libris.modules.bibliographic.api.schemas.diagnostics import CatalogValidationResult

# @router.post("/prevalidate", response_model=CatalogValidationResult,
#              response_model_exclude_none=True)
# def prevalidate(...):
#     return validate_catalog(graph, resolved_profile)
```

[consume.ts](../examples/validation/consume.ts) demonstra distribuição por campo,
múltiplos diagnósticos, globais, tradução por code/parameters, fallback e bloqueio
em failed/não conformidade. Gerar cliente completo pelo OpenAPI na integração real;
validar payload no transporte. Traduções futuras entram em src/i18n/messages.ts,
sem vincular API a React, rótulos ou estado de formulário. Sem editor Next.js nesta issue.

## Limitações e trabalhos futuros

Não existem CRUD/prevalidate HTTP, criação/verificação de ETags de representações,
cliente gerado, editor ou tradução negociada por Accept-Language. Formatos e
mapeamentos necessários estão implementados/testados para essas integrações.
Mensagem pública de fallback é em português; títulos HTTP são padronizados em inglês.
Não há reconciliação externa/inferência/novo motor/novas tabelas. Perfis continuam
candidatos à homologação; categorias/códigos genéricos conservam informação quando
faltam constraints específicas. Nenhuma classificação é inventada por mensagem.
Canonização de diagnósticos não foi homologada para grafos de escala institucional;
limites do parser RDF existente continuam vigentes.
