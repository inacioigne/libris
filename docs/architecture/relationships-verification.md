# Verificação da M03.01.03 — issue #16

Data: 2026-10-11. Implementação local, sem commit, push, PR ou escrita no GitHub.
Requisitos obtidos da descrição completa de #16; contexto e matriz em
[relationships.md](relationships.md), decisões no [ADR 0018](../decisions/0018-bibliographic-relationships.md).

## Implementação e arquivos

| Arquivo ou conjunto | Alteração e finalidade |
| --- | --- |
| `apps/api/src/libris/modules/bibliographic/domain/relationships.py` | Novo: EntityType, 14 definições semânticas, cardinalidades, caminhos auxiliares, inversas/simetria e registro extensível imutável por leitura |
| `apps/api/src/libris/modules/bibliographic/api/schemas/common.py` | Referências discriminadas locais/externas/não reconciliadas; aliases de tipo; contribuição/publicação aceitam referências tipadas e legadas |
| `api/schemas/work.py` | Referências tipadas para assunto, obras relacionadas e tradução nos três DTOs |
| `api/schemas/instance.py` | instance_of tipada, preservando URI-only e obrigatoriedade |
| `api/schemas/item.py` | item_of e held_by tipadas |
| `api/schemas/agent.py` | related_authority tipada, limitada a Agent/Subject |
| `api/schemas/subject.py` | broader e related tipadas |
| `api/schemas/relationships.py` | Novo: DirectLink, ContributionLink, PublicationLink; Create/Read/Replace/Update; add/remove/replace e aplicação pura atômica |
| `api/schemas/__init__.py` | Exporta os quatro contratos de relacionamentos junto dos quinze DTOs existentes |
| `application/relationships.py` | Novo: protocolo de resolução, relatório de pendências, verificação de identidade/tipo/existência, normalização de aliases, atualização resolvida e ciclos sobre closure fornecida |
| `tests/api/test_relationships.py` | Novo: 108 casos de conformidade, incluindo os 41 exemplos |
| `tests/fixtures/bibliographic/relationships/manifest.json` | Novo: versão, schemas, camadas de validação e resultados esperados |
| `tests/fixtures/bibliographic/relationships/valid/*.json` | Novos: 23 payloads de criação, leitura, substituição, PATCH, URI externa e referência provisória |
| `tests/fixtures/bibliographic/relationships/invalid/*.json` | Novos: 18 payloads rejeitados na camada estrutural, referencial ou de operação |
| `docs/architecture/relationships.md` | Novo: diagnóstico, matriz completa, contratos, atualização, integridade e integrações futuras |
| `docs/decisions/0018-bibliographic-relationships.md` | Novo: decisões e limites arquiteturais |
| `docs/architecture/relationships-verification.md` | Este relatório, critérios e evidências executadas |
| `docs/architecture/catalogographic-schemas.md` | Nota explícita de evolução, preservando o registro histórico da M03.01.02 |
| `README.md` | Links para o contrato e evidências |

Os caminhos abreviados de código nesta tabela são relativos a
`apps/api/src/libris/modules/bibliographic/`. Não houve mudança de dependências,
locks, rotas, migrações, perfis publicados, frontend ou mecanismos de persistência.

## Critérios de aceitação, um a um

Os nove critérios abaixo reproduzem os requisitos da issue, avaliados pelo
comportamento implementado, sem confundir menção documental com execução.

| Critério da #16 | Resultado e implementação | Arquivos | Testes que comprovam | Limites / dependências |
| --- | --- | --- | --- | --- |
| Matriz versionável das relações iniciais com semântica e cardinalidades | Atendido: 14 definições, matriz v1.0 e distinção contrato/perfil | `domain/relationships.py`, `relationships.md` | `test_matrix_covers_the_executable_registry`, `test_registered_relationships`, `test_registered_profile_cardinality_minimum_and_maximum`, `test_profile_minimum_is_not_an_ontology_axiom` | Homologação institucional e política futura #20/#21 |
| Origem, destino, direção, restrições e mapeamento documentados em todas as relações | Atendido: predicados completos, tipos, caminhos, inversas formais e simetria separadas | `domain/relationships.py`, `api/schemas/relationships.py`, matriz | `test_registered_relationships`, `test_incompatible_targets`, `test_metadata_inverses_match_verified_vocabulary`, `test_json_schema_and_semantic_paths`, `test_cycles_require_complete_supplied_closure` | Closure deve ser carregada pela aplicação; inversas de navegação não inventadas |
| Referências internas/externas sem identificação incompatível com #17 | Atendido: UUID/URI existentes; três modalidades; igualdade conferida com identidade armazenada | `api/schemas/common.py`, `application/relationships.py`, cinco DTOs | `test_reference_roundtrip`, `test_invalid_local_reference`, `test_required_reference_attributes`, `test_alias_duplicates_and_identity_mismatch_after_resolution`, `test_application_update_resolves_local_aliases_and_preserves_stored_uri` | Resolução pública/fusão/tombstones #17; sem inferência de localidade por prefixo |
| Exemplos JSON Create/Read/Update compatíveis com M03.01.02 | Atendido: exemplos dos DTOs existentes e das coleções; payloads URI-only preservados | cinco DTOs, `api/schemas/relationships.py`, fixtures/manifest | `test_versioned_examples`, `test_existing_dtos_accept_typed_and_legacy_references_without_recursion`; suíte anterior `test_catalogographic_schemas.py` | Instance related_to usa o contrato de vínculos; não altera release do perfil ou DTO Instance unilateralmente |
| Vínculos inválidos, ausentes e removidos verificáveis | Atendido: ausência preserva; null rejeitado nas operações; limpeza/substituição explícita; rejeição de duplicata, ausência, tipo, cardinalidade e ciclos | `api/schemas/relationships.py`, `application/relationships.py`, fixtures inválidas | `test_collection_operations_are_atomic_and_distinguish_omission`, `test_invalid_operations`, `test_remove_mandatory_link_and_unknown_replace_rejected`, `test_operation_cannot_hide_wrong_origin_or_derived_link`, `test_self_alias_rejected_after_resolution`, `test_versioned_examples` | Referência inexistente verificada com double, não banco; sem cascade delete de autoridade |
| Sem incorporação recursiva ou dependência de ORM | Atendido: referências rasas, source/target tipados, protocolo independente | `common.py`, schemas de vínculos e aplicação | `test_reference_roundtrip`, `test_versioned_examples`, `test_existing_dtos_accept_typed_and_legacy_references_without_recursion`; importações e mypy executados | Integração transacional futura usa serviço explícito, nunca tabelas de outro módulo |
| Serialização JSON-LD/RDF e outras ontologias preservando significado | Atendido como contrato: caminhos Contribution/Publication, papéis, agrupamento e extensões diretas autorizadas; nenhum predicado canônico redefinido | registro, schemas, ADR 0018, especificação | `test_extension_is_explicit_and_does_not_redefine_canonical_semantics`, `test_json_schema_and_semantic_paths`, `test_publication_groups_remain_distinct_and_roles_are_preserved`, round-trip JSON dos exemplos | Transformação desta superfície em Graph pertence à #18; não se alegou round-trip RDF novo ou exportação genérica lossless dos DTOs |
| Separação entre metadados e operações ILS | Atendido: Instance/Item bibliográficos e held_by sem estados operacionais; campos extras rejeitados | registro, schemas, documentação, ADR | `test_versioned_examples`, `test_held_by_candidate_requires_organization`; testes preexistentes de campos extras dos DTOs | Disponibilidade/circulação continuam módulos futuros, sem indexação Elasticsearch |
| Exemplos e conformidade permitem validar etapas seguintes | Atendido: 41 fixtures executáveis, manifest com camada de rejeição e 108 testes novos | fixtures, manifest, `test_relationships.py`, especificação | `test_versioned_examples` valida todos os arquivos; casos estruturais, de aplicação, atualização, JSON e metadados | Double explícito; integração PostgreSQL, resolução externa e SHACL de perfis futuros não simulados como entregues |

## Comandos e resultados executados

Em `apps/api`, ambiente virtual já existente, sem instalar pacotes:

- `.venv/bin/pytest -q`: **423 aprovados**, sem falhas, em 18,69 s. Inclui os
  108 testes novos e a suíte anterior de contratos/FastAPI, RDF, autenticação e saúde.
- `.venv/bin/pytest ../../tests/api/test_relationships.py -q`: execução direcionada
  final após ampliar as leituras compostas dos exemplos: **108 aprovados**, sem falhas.
- `.venv/bin/ruff check . ../../tests`: aprovado, sem alterar configuração global.
- `.venv/bin/mypy src`: aprovado, strict, **44 arquivos**, sem suppressions novas.
- `.venv/bin/ruff format --check` nos onze arquivos Python novos/alterados:
  aprovado; arquivos existentes fora da alteração não foram reformatados.
- `.venv/bin/python -c '...'`: importação dos quatro contratos públicos e da função
  de atualização resolvida aprovada, sem inicializar serviços externos.

A suíte emite **273 avisos de depreciação** em FastAPI/Starlette/httpx e
RDFLib/ConjunctiveGraph, nos arquivos preexistentes. Não foi alterado o adaptador RDF
nem instalada uma dependência para ocultar avisos.

Em `apps/web`, usando Node 24.16.0 existente:

- `PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH /home/inacio/.nvm/versions/node/v24.16.0/bin/node node_modules/next/dist/bin/next build --webpack`:
  aprovado, compilação e geração das páginas /pt e /en.
- `/home/inacio/.nvm/versions/node/v24.16.0/bin/node node_modules/typescript/bin/tsc --noEmit`:
  aprovado.

Na raiz:

- `docker compose --env-file .env.example config --quiet`: aprovado.
- `git diff --check`: aprovado.
- Leitura JSON e conferência de completude do manifest: aprovado, **42 arquivos
  JSON** (41 exemplos + manifest), **23 válidos e 18 inválidos**. A validação Pydantic
  e a rejeição na camada declarada ocorrem em `test_versioned_examples`.
- `git status --short`: executado; resultado abaixo.

Limites observados: `bash scripts/check.sh` foi tentado e interrompido pelo
snap-confine do uv/Snap. A suíte no sandbox parou após 35 testes e timeout de 55 s
por restrição de streams, sem completar; a suíte completa passou fora desse sandbox.
O primeiro build no sandbox falhou ao executar TypeScript --showConfig; o build
com PATH de Node e fora da restrição passou. As partes disponíveis do script foram
executadas individualmente, com as ferramentas locais. Mensagens de streams do
shell também apareceram em verificações que terminaram com código zero; os
resultados acima provêm da saída e do status real de cada ferramenta.

Não foram executados testes de integração PostgreSQL/Elasticsearch, migrações em
banco ou resolução de URIs externas. Não há alteração de persistência nesta tarefa;
existência foi testada somente com double em memória. O serviço futuro deve fornecer
resolução no PostgreSQL dentro da transação, SHACL final, closure e revisão esperada.

## Pendências reais e integrações

- #17: resolução pública, tratamento de fusão/exclusão e consolidação da política
  de identidade; UUID e URI existentes foram reutilizados, sem reescrever identidades.
- #18: adaptação dos DTOs/vínculos para JSON-LD/RDF, preservando agrupamentos privados,
  literais/propriedades fora da superfície e identidades; nenhuma URI fictícia para
  referência não reconciliada. Novo serializador não fazia parte da #16.
- #20/#21: perfis configuráveis, vocabulários autorizados, homologação institucional
  e shapes locais independentes/versionados. O mecanismo existente permanece intacto.
- API/persistência futuras: injetar resolvedor real, validar closure completa e perfil,
  aplicar CAS/revisões e delimitar commit/rollback no serviço. Não há endpoints
  definitivos ou tabela bibliográfica nova nesta entrega de contratos.

## Estado do repositório

```text
 M README.md
 M apps/api/src/libris/modules/bibliographic/api/schemas/__init__.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/agent.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/common.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/instance.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/item.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/subject.py
 M apps/api/src/libris/modules/bibliographic/api/schemas/work.py
 M docs/architecture/catalogographic-schemas.md
?? apps/api/src/libris/modules/bibliographic/api/schemas/relationships.py
?? apps/api/src/libris/modules/bibliographic/application/relationships.py
?? apps/api/src/libris/modules/bibliographic/domain/relationships.py
?? docs/architecture/relationships-verification.md
?? docs/architecture/relationships.md
?? docs/decisions/0018-bibliographic-relationships.md
?? tests/api/test_relationships.py
?? tests/fixtures/bibliographic/relationships/
```

## Verificação do pré-requisito de relacionamentos (#16)

Os contratos da #16 estavam publicados no GitHub, mas ausentes do checkout
2f2b61c. Foram reaproveitados na #17, com os 108 testes e as 41 fixtures + manifest
originais, sem importar o relatório histórico como evidência de execução local.

Os resultados executados nesta sessão e os limites estão no
[relatório de identificadores](persistent-identifiers-verification.md).
A suíte inclui test_relationships.py, test_catalogographic_schemas.py e os
testes novos de identidade, preservando formatos URI-only, modalidades tipadas,
operações, agrupamentos Contribution/Publication e resolvedor desacoplado.

Existência em banco, aliases de fusão, workflow e endpoints são integrações futuras
onde não houver persistência implementada; doubles não comprovam PostgreSQL.
