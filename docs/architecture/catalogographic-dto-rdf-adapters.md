# Adaptadores DTO ↔ RDF — M05.02 / #46

Implementação interna sobre os contratos v1, sem endpoints novos. RDFLib Graph
continua canônico; os quinze DTOs, contexto `bibframe-v1`, perfis, shapes e snapshots
históricos não foram modificados. Aplicam-se ADRs 0017–0023/0025/0028/0029.
[Evidências da execução](catalogographic-m0502-verification-2026-10-16.md).

## Interfaces e responsabilidades

Importar de `libris.modules.bibliographic.infrastructure.serialization`:

| Função | Entrada / saída | Validação |
| --- | --- | --- |
| `create_to_graph(resource, identity, *, profile, references=None)` | Um dos cinco Create + ResourceIdentity atribuída → Graph novo | Revalidação Pydantic, resolução fornecida, registro semântico/perfil, ownership e SHACL |
| `graph_to_read(graph, identity)` | Snapshot + ResourceIdentity armazenada → união dos cinco Read | Ownership, classe raiz, cardinalidade, tipos de termos e invariantes Pydantic; sem revalidar histórico contra outra release |
| `resource_to_graph(resource, *, references=None)` | Read → Graph novo | Writer existente, Pydantic e ownership; não promete SHACL nem exportação integral |
| `apply_update(graph, update, identity, *, profile, references=None)` | Snapshot completo + Update parcial → Graph completo novo | Tipo correspondente, Pydantic do patch e estado completo, autorização dos campos escritos, ownership e SHACL final |

`profile` é o ID legado local ou `ResolvedProfile` obtido pelo registro confiável.
A aplicação deve fornecer **a release armazenada** na revisão, nunca selecionar
outra automaticamente. `ResolvedProfile` não é configuração aceita de cliente.
Os IDs legados carregam semântica 1.0; perfis resolvidos usam
`ProfileRegistry.semantic_registry_for(release_id)`, incluindo a associação 2.0 do
perfil `work-extensions:2.0.0`. O adaptador não torna o serviço persistente compatível
com perfis 2.0: `BibliographicService` conserva os três IDs históricos suportados.

`mapping.py` mantém o writer compartilhado, agora verificando também evidências de
tipo/subtipo fornecidas para relações. `projection.py` contém somente a leitura
explícita e as fronteiras dos campos consumidos. `adapters.py` coordena Create e
PATCH sem banco, transação, Request, rede ou estado bibliográfico global. Não há
framework de mapeamento, resolvedor alternativo ou nova representação persistente.

## Cobertura de campos

O mapeamento direto continua na [tabela campo/predicado/classe](semantic-serialization.md#mapeamento-completo-da-superfície-read).
O inverso lê esses mesmos predicados, sem heurística pelo nome. Relações e caminhos
contribution/agent e provisionActivity/agent usam `DEFAULT_REGISTRY`.

| Tipo / classe | Campos de conteúdo reconstruídos; todos disponíveis em Create e PATCH salvo indicação |
| --- | --- |
| Work / bf:Work | title, language, content, contribution, subject, classification, related_to, translation_of, note |
| Instance / bf:Instance | instance_of, title, edition_statement, provision_activity, identified_by, extent, carrier, note |
| Item / bf:Item | item_of, identified_by, held_by, note, custodial_history, shelf_mark, provenance |
| Agent / bf:Agent, bf:Person, bf:Organization | kind (Create/Read, imutável no Update), authorized_name, variant_name, identified_by, external_reference, provenance, related_authority |
| Subject / skos:Concept | preferred_label, alternative_label, scheme, broader, related, external_reference, provenance |

Auxiliares: Title/VariantTitle (main_title/subtitle); Note (label/note_type);
Identifier/Local/Isbn (value/source); Contribution (agent/role); Classification
(classification_portion/source); Publication (agent/place/date); Extent (label);
ShelfMark (value/source). Associações permanecem agrupadas por nó, incluindo
publicações repetidas com o mesmo agente. Nenhuma inversa é materializada na leitura.

## Identidade e referências

A identidade da raiz vem do armazenamento por `ResourceIdentity`, sem extração do
UUID da URI, concatenação de base atual ou geração no mapper. Create exige identidade
já atribuída; Read devolve esse UUID/URI; Update não permite nenhum desses campos.
A raiz deve existir no grafo recebido. Evidência divergente no `ReferenceMapping`
para UUID/URI da raiz é rejeitada. O grafo não contém o UUID técnico; portanto o
mapper sozinho não pode provar que um UUID fornecido pertence àquela URI. Essa
associação é responsabilidade do chamador que carrega a identidade persistida.

Referências locais UUID-only usam o `ReferenceMapping` existente de `ResolvedEntity`
resolvidos pela aplicação. UUID+URI precisam concordar; entradas por UUID e URI não
podem divergir. Tipo resolvido deve ser permitido pelo registro; held_by resolvido
exige Organization. URI-only não comprova existência, localidade ou tipo: quando
há evidência no mapa pela chave URI, ela é conferida; sem evidência não se inventa
um alvo. Autorreferências diretas/auxiliares e aliases resolvidos são rejeitados.

A forma canônica de referência reconstruída é `ResourceReference(uri=...)`, tanto
para URI local quanto externa. Não é possível recuperar do RDF o discriminador
local/external, UUID do alvo, namespace/external_id, ou metadados de reconciliação.
O Read não inventa tais dados. São metadados operacionais fora da projeção RDF.
`UnreconciledReference` continua rejeitada pelo writer: não criar URI provisória,
identidade fictícia ou literal no lugar de uma relação. Existência, ciclo de vida
e fecho transitivo de ciclos continuam nos contratos de aplicação existentes.

## Algoritmo de PATCH

1. Conferir snapshot/identidade e reconstruir a projeção normativa, registrando
   os predicados por campo e as triplas efetivamente lidas de cada auxiliar.
2. Exigir o Update do mesmo tipo da raiz e revalidar também objetos DTO mutados.
   Usar `model_dump(exclude_unset=True)`; nunca `exclude_none=True`.
3. Combinar os campos presentes com a projeção e revalidar o Read completo. Omissão
   preserva, null opcional remove, lista substitui integralmente; null/lista vazia
   em campo obrigatório falha. Isso detecta também conflito prefLabel/altLabel
   entre patch e estado anterior. Auxiliares são substituições completas.
4. Construir a representação dos novos valores pelo writer existente. Autorizar
   somente os campos escritos no perfil/registro da release; namespace conhecido
   não autoriza propriedade arbitrária. Campos de identidade/classe e extras não
   fazem parte de Update.
5. Copiar todas as triplas e namespaces do snapshot. Remover apenas as arestas da
   raiz dos predicados presentes. Calcular quais auxiliares deixaram de ser
   alcançáveis conforme `owned_nodes`. Auxiliares compartilhados com campos
   preservados permanecem integralmente, inclusive suas extensões.
6. Remover auxiliares órfãos somente quando **todas** as suas triplas foram
   reconhecidas pela projeção. Se houver anotação, classe adicional ou subgrafo
   fora da projeção, rejeitar a substituição antes de devolver qualquer resultado.
   Assim, uma edição não apaga extensões escondidas nem as realoca por heurística.
7. Importar somente os novos valores dos campos presentes e seus auxiliares.
   Validar ownership, aplicabilidade de perfil e SHACL do **grafo completo** final.

Qualquer falha deixa o grafo e seus namespaces originais intactos. Não há escrita,
CAS ou transação no adaptador. Erros estruturais usam ValidationError; erros RDF
usam RdfDocumentError; propriedade/perfil usam CatalogError/ProfileError;
não conformidade conserva CatalogValidationRejected com diagnósticos existentes.
Falha técnica de validação permanece técnica e não se torna falsa não conformidade.

## Extensões, histórico e limites da projeção

Predicados independentes, classes adicionais e subgrafos auxiliares não mencionados
são copiados termo a termo. Isso inclui `dcterms:abstract "Resumo"@pt-BR` e
auxiliares históricos que a release não permite editar. Preservação não autoriza
novas propriedades arbitrárias. A validação final continua obrigatória: se regras
da release armazenada impedirem o estado completo, a edição é rejeitada, sem
migrar a release nem remover histórico para obter conformidade.

A projeção Read **não** substitui o snapshot. Não contém extensões, identidade de
auxiliares por IRI, compartilhamento entre auxiliares, classes RDF adicionais nem
a distinção sintática de literal simples versus xsd:string explícito em campos
LocalizedText/string. PublicationDate conserva lexical e datatype explícito;
textos conservam idioma ou ausência de tag. Datatype incompatível com o tipo do
campo é rejeitado, sem coerção silenciosa. Um grafo válido mas não representável
pelas cardinalidades/invariantes v1 pode ter a projeção recusada. PATCH também
recusa esse caso conservadoramente; não reduz o snapshot para fazê-lo caber.

Graph → Read → Graph é isomorfo para a superfície normativa produzida pelo writer
com auxiliares privados não compartilhados. Não se promete isomorfismo integral de
snapshots arbitrários. IRIs auxiliares viram blank nodes novos ao reconstruir pelo
Read; triplas adicionais continuam somente no snapshot. PATCH independente conserva
os termos originais, inclusive datatypes/IRIs auxiliares fora do campo escrito.
Exportar integralmente com `serialize_graph(snapshot, ...)`, nunca pelo Read.

Coleções RDF são conjuntos sem ordem. Duplicatas idênticas de literais/IRIs colapsam;
auxiliares distintos continuam distintos. A projeção ordena listas pelo conteúdo
serializado deterministicamente, sem usar labels de blank nodes como identidade.
Não foram acrescentadas propriedades de ordenação ou listas RDF artificiais.
JSON-LD/Turtle usam os parsers limitados existentes; contextos remotos permanecem
bloqueados. Snapshots persistentes usam JSON-LD expandido pelo serviço existente.

## Composição com o serviço existente

Exemplo dentro de um caso de uso autorizado; `context`, `provenance`, `identity`,
`references` e o DTO vêm das fronteiras confiáveis existentes:

```python
graph = create_to_graph(create_dto, identity,
                        profile=INSTITUTIONAL_PROFILE_ID, references=references)
revision = await service.create(identity, graph, provenance,
                                profile=INSTITUTIONAL_PROFILE_ID, context=context)

stored, current = await service.read(identifier, context=context)
updated = apply_update(current, update_dto, stored.identity,
                       profile=stored.profile, references=references)
revision = await service.revise(identifier, stored.number, updated, provenance,
                                context=context)
response = graph_to_read(updated, revision.identity)
```

O chamador HTTP futuro precisa vincular `stored.number` à revisão efetivamente
esperada pelo cliente (If-Match), sem atualizar silenciosamente a expectativa.
O CAS de `revise` impede que uma leitura anterior sobrescreva mudança concorrente.
Versão editorial esperada pode ser passada pela assinatura vigente. Resolução de
referências sob transação, precondições HTTP e autorização por operação continuam
responsabilidades da #47 e dos serviços. Nenhuma assinatura transacional foi alterada;
auditoria, proveniência, publicação da revisão aprovada e histórico append-only
continuam sob os serviços existentes. Teste de `prepare_document` comprova o formato
aceito pela persistência, sem afirmar execução PostgreSQL real.
