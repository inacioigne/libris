# ADR 0020 — Contratos de serialização JSON-LD e RDF

Status: aceito para implementação técnica da M03.01.05 (#18); homologação institucional pendente

Data: 2026-10-12

## Contexto

Graph RDFLib é a representação canônica dos snapshots. Os cinco DTOs Read são a
superfície operacional dos perfis candidatos, não uma descrição completa de RDF.
ADRs 0012/0019 fixam a URI armazenada; ADR 0015 fixa propriedade e composição.
O parser legado rejeita qualquer `@graph`, inclusive wrappers do grafo padrão;
a persistência depende de arrays JSON-LD expandidos e deve continuar compatível.

## Decisão

Contrato de representação **1.0**, contexto local **bibframe-v1**, JSON-LD 1.1
no subconjunto testado e Turtle. RDF/XML e N-Triples são possibilidades futuras,
sem API ou negociação anunciada. JSON operacional (`application/json`) contém
campos/UUID; JSON-LD (`application/ld+json`) representa RDF; RDF é o grafo,
Turtle (`text/turtle`) é outra sintaxe do mesmo grafo.

Um pipeline DTO Read → Graph → sintaxe, com mapeamento explícito. O caminho
Graph → sintaxe publica todas as propriedades, inclusive extensões fora dos DTOs;
jamais Graph → DTO → Graph para exportação integral. A infraestrutura recebe
contratos tipados sem importar FastAPI, ORM, banco ou índice. Não há novos endpoints,
tabelas, migrações, dependências, Dataset, SPARQL ou store.

Descrição padrão: raiz proprietária, auxiliares privados e referências por URI,
sem expansão de descrições referenciadas. Auxiliares novos usam blank nodes;
seus rótulos não são identidade persistente. Snapshots existentes também podem
usar URI-raiz#fragmento, preservada integralmente. Não derivar URI auxiliar da
posição de listas como identidade pública. Composição usa somente snapshots
explicitamente fornecidos, reutiliza ownership, renomeia blank nodes e deriva
hasInstance/hasItem conforme o contrato existente. Não grava inversas no proprietário.
Grafos nomeados exigiriam contrato separado com Dataset.

Contexto imutável no pacote, sem `@vocab`, contextos de clientes, URLs ou imports.
A compactação limitada renomeia somente predicados conhecidos de nós expandidos.
Não achata literais nem altera @id/@type. Cada nó do array recebe o contexto
completo: é JSON-LD válido e evita @graph. O custo de repetição é aceito nesta etapa;
um wrapper mais compacto exigiria contrato/alteração futura do parser, não exceção
silenciosa. Não se promete compactação/framing genéricos ou suporte integral a 1.1.
O parser específico da release aceita somente esse contexto ou a forma expandida,
reutilizando o parser seguro legado. O parser legado continua aceitando contextos
objetos locais conforme seu contrato, sem adotar automaticamente o novo contexto.

Exportações são interpretadas novamente e comparadas por **isomorfismo** após
serialização e compactação. Não exigir igualdade de texto, ordem de triplas ou
nomes de blank nodes. Limites em bytes seguem RDF_MAX_DOCUMENT_BYTES; JSON e
estruturas auxiliares têm profundidade 64. Isomorfismo não certifica conformidade
institucional, ausência global de ciclos de relações ou existência dos alvos.

Referências locais UUID-only ou UUID+URI exigem um mapa confiável fornecido pelo
chamador, contendo ResolvedEntity/identidade armazenada; IDs, URIs e tipos devem
concordar. URI-only local pode usar a URI persistida quando não há mapa; se o mapa
for fornecido, a resolução torna-se obrigatória também para essa referência.
Referências legadas/exteriores conservam a URI sem consulta nem equivalência forte.
Referências não reconciliadas falham na representação publicável; rascunhos futuros
exigirão formato e política próprios. Namespace/external_id de referência externa
são metadados de reconciliação operacional, sem equivalência RDF inventada.

Campos desconhecidos do DTO são erros Pydantic; termos compactos desconhecidos
falham no parser de representação. Predicados RDF por IRI explícita são conservados
nos grafos canônicos, sem whitelist universal que impeça outras ontologias.
Mudança do contexto/mapeamento que mude interpretação exige nova versão/artefato;
não sobrescrever releases JSON/SHACL ou revisões existentes.

Negociação isolada considera especificidade, q e curingas; q=0 específico vence
um curinga. Empates usam preferência do servidor, com default configurável.
REST operacional prefere JSON; um futuro resolvedor de identidades configura
outra lista/default conforme ADR 0019. HTML não foi implementado aqui. Incompatível
ou Accept malformado resulta em decisão equivalente a 406. Vary: Accept é obrigatório
em respostas negociadas; Content-Type de ingestão e ETag são contratos separados.

## Alternativas rejeitadas e consequências

| Alternativa | Motivo / consequência |
| --- | --- |
| Mapeamento independente por formato | Divergência semântica; um Graph é fonte de ambas as saídas |
| Exportar snapshot via DTO | Descartaria extensões fora da edição; caminho integral separado |
| Compactação automática RDFLib com @graph | Incompatível com o parser seguro atual; compactação limitada e testada |
| Permitir @graph somente por aparência | Pode introduzir named graphs; nenhum caminho libera essa palavra reservada |
| Contextos remotos ou @vocab | Dependência de rede ou interpretação silenciosa de campos desconhecidos |
| URI reconstruída pela configuração/UUID | Viola identidade persistida, inclusive bases históricas |
| owl:sameAs automático | Reconciliação não demonstrada; seeAlso e referências continuam associações |
| Expansão recursiva/ORM no serializador | Escopo indeterminado e acoplamento; composição explícita apenas |
| URIs auxiliares por conteúdo/posição | Acrescenta identidade sem necessidade; blank nodes são suficientes |
| Listas RDF para todas as coleções | DTOs não garantem ordem semântica; RDF conserva conjunto de declarações |

RDFLib pode normalizar lexicais: quando a forma não sobreviver ao round-trip,
a exportação falha explicitamente. Datas aceitas estruturalmente pelo DTO podem
não ser exportáveis pela versão instalada de RDFLib. O teste mantém esse limite
visível; não normalizar silenciosamente nem alterar o DTO. Limites em bytes e
profundidade não substituem quotas de CPU/isolamento de futura ingestão pública.

## Referências

- [Issue #18](https://github.com/inacioigne/libris/issues/18), lida integralmente.
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/), contexto/objetos de valor/arrays.
- [Ontologia BIBFRAME oficial](https://github.com/lcnetdev/bibframe-ontology/blob/master/bibframe.rdf).
- [RFC 9110 §12.5.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5.1).
- [Especificação](../architecture/semantic-serialization.md) e
  [verificação](../architecture/semantic-serialization-verification.md).
