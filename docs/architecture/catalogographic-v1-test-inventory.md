# Inventário de fixtures e testes catalográficos v1 — #30

Data: 2026-10-12. Inventário por arquivo de `tests/fixtures/bibliographic/` e `docs/examples/`,
baseado nos consumidores inspecionados. Dados sintéticos; nomes de cenários não comprovam homologação.
IDs de requisito remetem à [matriz](catalogographic-v1-conformance-matrix.md).
Os testes `tests/api/` são locais, sem PostgreSQL/Elasticsearch; integração está identificada separadamente.

Classificação identifica a finalidade principal: **conforme**, **inválido**, **caso-limite** ou **regressão**.
JSON aceito estruturalmente pode ainda falhar na publicação (ex.: referência não reconciliada).
Manifestos, hashes e READMEs são suportes de rastreabilidade, não registros catalográficos.

## Achados da consolidação

- As 15 fixtures de contrato já cobriam Create/Read/Update. Faltava o percurso conjunto até Graph/SHACL por entidade/operação; os 15 casos novos reutilizam essas entradas.
- O corpus institucional contém 13 conformes/casos-limite e 15 inválidos. As rejeições verificavam apenas conformidade/severidade; o manifesto agora fixa também path e componente esperado, sem alterar nenhum TTL.
- Os oito exemplos públicos de diagnóstico não eram consumidos por pytest; o novo teste executa seu gerador em modo somente verificação.
- Os exemplos book JSON-LD/Turtle não eram comparados na suíte com a fixture legada; o novo teste fixa isomorfismo e a diferença de conformidade entre releases.
- Órfãos intencionais: lifecycle-proposal.json (resolução HTTP futura) e consume.ts (consumo ilustrativo). Não representam cobertura executável e permanecem preservados.
- Há sobreposição deliberada entre contratos/*-read.json, identifiers/*-read.json, serialization/valid/*.json e docs/examples/serialization: representam respectivamente DTOs, identidade, mapeamento completo e exemplos publicados. Não apagar para deduplicar suites de responsabilidades distintas.
- book.ttl e exemplos book usam autoridades embutidas/inversas e não são snapshots institucionais. Os testes novos explicitam esse limite; não reescrever legado para obter aprovação 1.1.
- Regras documentadas mais antigas sobre ator/editorial são históricas. A matriz atual usa também os serviços e testes PostgreSQL da #43, sem atribuir às issues antigas garantias posteriores.

Total: **177 arquivos** inventariados individualmente.

## tests/fixtures/bibliographic

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/book.ttl` | agregado legado Work/Instance/Item + autoridades embutidas | regressão | book | `tests/api/test_catalogographic_conformance.py::test_legacy_book_examples_remain_equivalent`; `tests/api/test_bibliographic.py::test_round_trip`; `tests/integration/test_semantic_postgres.py::test_postgres_revisions_roundtrip_and_concurrency` | H01/R01: legado experimental; conforme v1, inválido institucional 1.1 |

## tests/fixtures/bibliographic/contracts

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/contracts/agent-create.json` | agent | conforme | agent: create, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/agent-read.json` | agent | conforme | agent: read, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/agent-update.json` | agent | conforme | agent: update, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/instance-create.json` | instance | conforme | instance: create, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/instance-read.json` | instance | conforme | instance: read, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/instance-update.json` | instance | conforme | instance: update, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/item-create.json` | item | conforme | item: create, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/item-read.json` | item | conforme | item: read, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/item-update.json` | item | conforme | item: update, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/subject-create.json` | subject | conforme | subject: create, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/subject-read.json` | subject | conforme | subject: read, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/subject-update.json` | subject | conforme | subject: update, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/work-create.json` | work | conforme | work: create, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/work-read.json` | work | conforme | work: read, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |
| `tests/fixtures/bibliographic/contracts/work-update.json` | work | conforme | work: update, campos proprietários | `tests/api/test_catalogographic_schemas.py::test_fixture_round_trip`; `tests/api/test_catalogographic_conformance.py::test_contract_pipeline_preserves_identity_and_semantics` | C01–C05: DTO fechado, identidade em Read, presença/null em Update e SHACL do estado completo |

## tests/fixtures/bibliographic/extensions

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/extensions/work.jsonld` | Work + DCTerms | regressão | work | `tests/api/test_semantic_extensions.py::test_examples_roundtrip_preserve_all_terms` | V02/R01: preservação integral, sem autorizar edição implícita |
| `tests/fixtures/bibliographic/extensions/work.ttl` | Work + DCTerms | regressão | work | `tests/api/test_semantic_extensions.py::test_examples_roundtrip_preserve_all_terms` | V02/R01: preservação integral, sem autorizar edição implícita |

## tests/fixtures/bibliographic/identifiers

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/identifiers/agent-read.json` | agent | conforme | agent-read | `tests/api/test_persistent_identifiers.py::test_read_fixtures_and_metadata_updates_preserve_identity` | I01–I02: identidade persistente e referências |
| `tests/fixtures/bibliographic/identifiers/entities.jsonld` | Work/Instance/Item/Agent/Subject | conforme | entities | `tests/api/test_persistent_identifiers.py::test_jsonld_and_turtle_examples_are_isomorphic_and_profile_valid` | I01–I02: identidade persistente e referências |
| `tests/fixtures/bibliographic/identifiers/entities.ttl` | Work/Instance/Item/Agent/Subject | conforme | entities | `tests/api/test_persistent_identifiers.py::test_jsonld_and_turtle_examples_are_isomorphic_and_profile_valid` | I01–I02: identidade persistente e referências |
| `tests/fixtures/bibliographic/identifiers/instance-read.json` | instance | conforme | instance-read | `tests/api/test_persistent_identifiers.py::test_read_fixtures_and_metadata_updates_preserve_identity` | I01–I02: identidade persistente e referências |
| `tests/fixtures/bibliographic/identifiers/item-read.json` | item | conforme | item-read | `tests/api/test_persistent_identifiers.py::test_read_fixtures_and_metadata_updates_preserve_identity` | I01–I02: identidade persistente e referências |
| `tests/fixtures/bibliographic/identifiers/lifecycle-proposal.json` | lifecycle | caso-limite | lifecycle-proposal | Nenhum: proposta ilustrativa de HTTP futuro (órfã intencional) | G01: tombstone/308/410 não implementados; não é DTO executável |
| `tests/fixtures/bibliographic/identifiers/references.json` | local/external/unreconciled | conforme | references | `tests/api/test_persistent_identifiers.py::test_reference_examples_are_executable` | I01–I02: identidade persistente e referências |
| `tests/fixtures/bibliographic/identifiers/subject-read.json` | subject | conforme | subject-read | `tests/api/test_persistent_identifiers.py::test_read_fixtures_and_metadata_updates_preserve_identity` | I01–I02: identidade persistente e referências |
| `tests/fixtures/bibliographic/identifiers/work-read.json` | work | conforme | work-read | `tests/api/test_persistent_identifiers.py::test_read_fixtures_and_metadata_updates_preserve_identity` | I01–I02: identidade persistente e referências |

## tests/fixtures/bibliographic/institutional

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/institutional/controlled-subjects.ttl` | Work, Instance, Agent, Subject | conforme | controlled-subjects | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/external-identifiers.ttl` | Work, Instance, Agent | conforme | external-identifiers | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/external-property.ttl` | Work | caso-limite | external-property | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/invalid-duplicate-authorized-label.ttl` | Work, Instance, Agent | inválido | duplicate-authorized-label | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://www.w3.org/2000/01/rdf-schema#label` / `UniqueLangConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-empty-identifier.ttl` | Work, Instance, Agent | inválido | empty-identifier | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://www.w3.org/1999/02/22-rdf-syntax-ns#value` / `MinLengthConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-literal-agent.ttl` | Work, Instance, Agent | inválido | literal-agent | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/agent` / `NodeKindConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-literal-work-reference.ttl` | Work, Instance, Agent | inválido | literal-work-reference | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/instanceOf` / `NodeKindConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-missing-contribution-role.ttl` | Work, Instance, Agent | inválido | missing-contribution-role | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/role` / `MinCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-missing-item-reference.ttl` | Work, Instance, Item, Agent | inválido | missing-item-reference | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/itemOf` / `MinCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-missing-local-identifier.ttl` | Work, Instance, Item, Agent | inválido | missing-local-identifier | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/identifiedBy` / `QualifiedMinCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-missing-title.ttl` | Work, Instance, Agent | inválido | missing-title | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/title` / `MinCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-numeric-publication-date.ttl` | Work, Instance, Agent, Organization | inválido | numeric-publication-date | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/date` / `OrConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-numeric-title.ttl` | Work, Instance, Agent, Organization | inválido | numeric-title | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/mainTitle` / `OrConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-only-variant-title.ttl` | Work, Instance, Agent, Organization | inválido | only-variant-title | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/title` / `QualifiedMinCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-subject-without-scheme.ttl` | Subject | inválido | invalid-subject-without-scheme | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://www.w3.org/2004/02/skos/core#inScheme` / `MinCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-two-work-references.ttl` | Work, Instance, Agent | inválido | two-work-references | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/instanceOf` / `MaxCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-wrong-edition-owner.ttl` | Work, Instance, Agent | inválido | wrong-edition-owner | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/editionStatement` / `MaxCountConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/invalid-wrong-reference-type.ttl` | Work, Instance, Agent | inválido | wrong-reference-type | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S02: `http://id.loc.gov/ontologies/bibframe/instanceOf` / `NodeConstraintComponent` |
| `tests/fixtures/bibliographic/institutional/local-item.ttl` | Work, Instance, Item, Agent, Organization | conforme | local-item | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/manifest.json` | várias / auxiliares | regressão | catálogo de 28 cenários; 15 rejeições com path/componente esperado | `tests/api/test_catalogographic_contract.py::test_corpus_shacl` | S01–S05: expectativas por cenário |
| `tests/fixtures/bibliographic/institutional/multiple-contributions.ttl` | Work, Instance, Agent | conforme | multiple-contributions | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/multiple-items.ttl` | Work, Instance, Item, Agent, Organization | conforme | multiple-items | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/shared-authority.ttl` | Work, Instance, Agent | conforme | shared-authority | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/single-author.ttl` | Work, Instance, Agent, Organization | conforme | single-author | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/snapshot-external-work.ttl` | Instance | caso-limite | snapshot-external-work | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/snapshot-local-work.ttl` | Instance | caso-limite | snapshot-local-work | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/translated-monograph.ttl` | Work, Instance, Agent | conforme | translated-monograph | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/two-editions.ttl` | Work, Instance, Agent | conforme | two-editions | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |
| `tests/fixtures/bibliographic/institutional/without-isbn.ttl` | Work, Instance, Agent | caso-limite | without-isbn | `tests/api/test_catalogographic_contract.py::test_corpus_shacl`; `tests/api/test_catalogographic_contract.py::test_corpus_lossless_entity_snapshots` | S01/R01: conformidade institucional, snapshots e isomorfismo |

## tests/fixtures/bibliographic/profiles

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/profiles/bibframe-2.0.1-terms.json` | perfis / registro semântico | regressão | bibframe-2.0.1-terms | `tests/api/test_declarative_profiles.py::test_bibframe_terms_are_from_reviewed_official_v2_inventory` | V02: termos BIBFRAME revisados, sem download |
| `tests/fixtures/bibliographic/profiles/legacy-sha256.json` | perfis / registro semântico | regressão | legacy-sha256 | `tests/api/test_declarative_profiles.py::test_legacy_models_ids_files_and_schema_preserved` | H01: sete fontes históricas e schema preservados byte a byte |
| `tests/fixtures/bibliographic/profiles/manifest.json` | perfis / registro semântico | regressão | manifest | `tests/api/test_declarative_profiles.py::test_invalid_fixture_corpus` | P02: manifesto de cinco rejeições |

## tests/fixtures/bibliographic/profiles/invalid

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/profiles/invalid/cyclic-base.json` | perfis / registro semântico | inválido | cyclic-base | `tests/api/test_declarative_profiles.py::test_invalid_fixture_corpus` | P02: resolution; código composition_cycle |
| `tests/fixtures/bibliographic/profiles/invalid/duplicate-field.json` | perfis / registro semântico | inválido | duplicate-field | `tests/api/test_declarative_profiles.py::test_invalid_fixture_corpus` | P02: structural; código None |
| `tests/fixtures/bibliographic/profiles/invalid/relative-iri.json` | perfis / registro semântico | inválido | relative-iri | `tests/api/test_declarative_profiles.py::test_invalid_fixture_corpus` | P02: structural; código None |
| `tests/fixtures/bibliographic/profiles/invalid/unknown-namespace.json` | perfis / registro semântico | inválido | unknown-namespace | `tests/api/test_declarative_profiles.py::test_invalid_fixture_corpus` | P02: resolution; código unknown_namespace |
| `tests/fixtures/bibliographic/profiles/invalid/unknown-shapes.json` | perfis / registro semântico | inválido | unknown-shapes | `tests/api/test_declarative_profiles.py::test_invalid_fixture_corpus` | P02: resolution; código unknown_shapes |

## tests/fixtures/bibliographic/relationships/invalid

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/relationships/invalid/add-duplicate.json` | RelationshipUpdate | inválido | add-duplicate: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/bad-identifiers.json` | EntityReference | inválido | bad-identifiers: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/bad-uri.json` | EntityReference | inválido | bad-uri: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/derived-write.json` | RelationshipCreate | inválido | derived-write: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/direct-role.json` | RelationshipCreate | inválido | direct-role: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/duplicate.json` | RelationshipCreate | inválido | duplicate: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/incompatible-identity.json` | RelationshipCreate | inválido | incompatible-identity: integrity | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/maximum.json` | RelationshipCreate | inválido | maximum: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/minimum.json` | RelationshipCreate | inválido | minimum: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/missing-identity.json` | EntityReference | inválido | missing-identity: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/missing-role.json` | RelationshipCreate | inválido | missing-role: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/nonexistent.json` | RelationshipCreate | inválido | nonexistent: integrity | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/null.json` | RelationshipUpdate | inválido | null: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/remove-absent.json` | RelationshipUpdate | inválido | remove-absent: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/self.json` | RelationshipCreate | inválido | self: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/unknown-predicate.json` | RelationshipCreate | inválido | unknown-predicate: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/wrong-origin.json` | RelationshipCreate | inválido | wrong-origin: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/invalid/wrong-target.json` | RelationshipCreate | inválido | wrong-target: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |

## tests/fixtures/bibliographic/relationships

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/relationships/manifest.json` | referências | conforme | catálogo de 41 cenários | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |

## tests/fixtures/bibliographic/relationships/valid

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/relationships/valid/external-subject.json` | RelationshipCreate | conforme | external-subject: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/instance-create.json` | RelationshipCreate | conforme | instance-create: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/instance-items-read.json` | RelationshipRead | conforme | instance-items-read: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/item-create.json` | RelationshipCreate | conforme | item-create: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/patch-absent.json` | RelationshipUpdate | caso-limite | patch-absent: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/patch-add.json` | RelationshipUpdate | conforme | patch-add: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/patch-clear.json` | RelationshipUpdate | conforme | patch-clear: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/patch-empty.json` | RelationshipUpdate | caso-limite | patch-empty: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/patch-remove.json` | RelationshipUpdate | conforme | patch-remove: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/patch-replace.json` | RelationshipUpdate | conforme | patch-replace: update | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/publication.json` | RelationshipCreate | conforme | publication: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/resource-instance-create.json` | InstanceCreate | conforme | resource-instance-create: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/resource-item-create.json` | ItemCreate | conforme | resource-item-create: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-create.json` | WorkCreate | conforme | resource-work-create: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-null.json` | WorkUpdate | caso-limite | resource-work-null: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-read.json` | WorkRead | conforme | resource-work-read: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/resource-work-update.json` | WorkUpdate | conforme | resource-work-update: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/unreconciled-agent.json` | RelationshipCreate | caso-limite | unreconciled-agent: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/work-agents.json` | RelationshipCreate | conforme | work-agents: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/work-create.json` | RelationshipCreate | conforme | work-create: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/work-instance-read.json` | RelationshipRead | conforme | work-instance-read: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/work-related.json` | RelationshipCreate | conforme | work-related: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |
| `tests/fixtures/bibliographic/relationships/valid/work-replace.json` | RelationshipReplace | conforme | work-replace: structure | `tests/api/test_relationships.py::test_versioned_examples` | L01–L03: estrutura, integridade fornecida ou operação atômica, conforme stage do manifesto |

## tests/fixtures/bibliographic/serialization/invalid

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/serialization/invalid/bad-datatype.json` | instance | inválido | bad-datatype | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em pydantic |
| `tests/fixtures/bibliographic/serialization/invalid/bad-date.json` | instance | inválido | bad-date | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em pydantic |
| `tests/fixtures/bibliographic/serialization/invalid/bad-uri.json` | work | inválido | bad-uri | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em pydantic |
| `tests/fixtures/bibliographic/serialization/invalid/ill-typed.ttl` | documento RDF | inválido | ill-typed | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/inconsistent.json` | work | inválido | inconsistent | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em serialization |
| `tests/fixtures/bibliographic/serialization/invalid/malformed.jsonld` | documento RDF | inválido | malformed | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/malformed.ttl` | documento RDF | inválido | malformed | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/missing-reference.json` | work | inválido | missing-reference | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em pydantic |
| `tests/fixtures/bibliographic/serialization/invalid/missing-title.json` | work | inválido | missing-title | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em pydantic |
| `tests/fixtures/bibliographic/serialization/invalid/named-graph.jsonld` | documento RDF | inválido | named-graph | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/remote-context.jsonld` | documento RDF | inválido | remote-context | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/remote-import.jsonld` | documento RDF | inválido | remote-import | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/unauthorized-context.jsonld` | documento RDF | inválido | unauthorized-context | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/unknown-field.json` | work | inválido | unknown-field | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em pydantic |
| `tests/fixtures/bibliographic/serialization/invalid/unknown-predicate.json` | work | inválido | unknown-predicate | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em pydantic |
| `tests/fixtures/bibliographic/serialization/invalid/unknown-term.jsonld` | documento RDF | inválido | unknown-term | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em parser |
| `tests/fixtures/bibliographic/serialization/invalid/unreconciled.json` | work | inválido | unreconciled | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em serialization |
| `tests/fixtures/bibliographic/serialization/invalid/unresolved.json` | work | inválido | unresolved | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: rejeição em serialization |

## tests/fixtures/bibliographic/serialization

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/serialization/manifest.json` | várias / auxiliares | regressão | camada esperada para 18 rejeições | `tests/api/test_semantic_serialization.py::test_invalid_fixtures` | R02: separação Pydantic/serialização/parser |

## tests/fixtures/bibliographic/serialization/valid

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `tests/fixtures/bibliographic/serialization/valid/agent.json` | agent | conforme | agent | `tests/api/test_semantic_serialization.py::test_five_resources_owned_equivalence_and_no_mutation` | R01: Read → Graph → JSON-LD/Turtle; tipo, termos e ownership |
| `tests/fixtures/bibliographic/serialization/valid/instance.json` | instance | conforme | instance | `tests/api/test_semantic_serialization.py::test_five_resources_owned_equivalence_and_no_mutation` | R01: Read → Graph → JSON-LD/Turtle; tipo, termos e ownership |
| `tests/fixtures/bibliographic/serialization/valid/item.json` | item | conforme | item | `tests/api/test_semantic_serialization.py::test_five_resources_owned_equivalence_and_no_mutation` | R01: Read → Graph → JSON-LD/Turtle; tipo, termos e ownership |
| `tests/fixtures/bibliographic/serialization/valid/minimal-work.json` | minimal-work | caso-limite | minimal-work | `tests/api/test_semantic_serialization.py::test_five_resources_owned_equivalence_and_no_mutation` | R01: Read → Graph → JSON-LD/Turtle; tipo, termos e ownership |
| `tests/fixtures/bibliographic/serialization/valid/organization.json` | Agent (Organization) | conforme | organization | `tests/api/test_semantic_serialization.py::test_five_resources_owned_equivalence_and_no_mutation` | R01: Read → Graph → JSON-LD/Turtle; tipo, termos e ownership |
| `tests/fixtures/bibliographic/serialization/valid/subject.json` | subject | conforme | subject | `tests/api/test_semantic_serialization.py::test_five_resources_owned_equivalence_and_no_mutation` | R01: Read → Graph → JSON-LD/Turtle; tipo, termos e ownership |
| `tests/fixtures/bibliographic/serialization/valid/work.json` | work | conforme | work | `tests/api/test_semantic_serialization.py::test_five_resources_owned_equivalence_and_no_mutation` | R01: Read → Graph → JSON-LD/Turtle; tipo, termos e ownership |

## docs/examples

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `docs/examples/book.jsonld` | agregado legado Work/Instance/Item + autoridades embutidas | regressão | book | `tests/api/test_catalogographic_conformance.py::test_legacy_book_examples_remain_equivalent` | H01/R01: legado experimental; conforme v1, inválido institucional 1.1 |
| `docs/examples/book.ttl` | agregado legado Work/Instance/Item + autoridades embutidas | regressão | book | `tests/api/test_catalogographic_conformance.py::test_legacy_book_examples_remain_equivalent` | H01/R01: legado experimental; conforme v1, inválido institucional 1.1 |

## docs/examples/controlled-vocabularies

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `docs/examples/controlled-vocabularies/external.json` | conceito externo | conforme | external | `tests/api/test_controlled_vocabularies.py::test_schema_openapi_and_checked_examples` | V01: valores discriminados e equivalência dos exemplos RDF |
| `docs/examples/controlled-vocabularies/external.jsonld` | conceito externo | conforme | external | `tests/api/test_controlled_vocabularies.py::test_schema_openapi_and_checked_examples` | V01: valores discriminados e equivalência dos exemplos RDF |
| `docs/examples/controlled-vocabularies/external.ttl` | conceito externo | conforme | external | `tests/api/test_controlled_vocabularies.py::test_schema_openapi_and_checked_examples` | V01: valores discriminados e equivalência dos exemplos RDF |
| `docs/examples/controlled-vocabularies/local.json` | conceito local | conforme | local | `tests/api/test_controlled_vocabularies.py::test_schema_openapi_and_checked_examples` | V01: valores discriminados e equivalência dos exemplos RDF |
| `docs/examples/controlled-vocabularies/local.jsonld` | conceito local | conforme | local | `tests/api/test_controlled_vocabularies.py::test_schema_openapi_and_checked_examples` | V01: valores discriminados e equivalência dos exemplos RDF |
| `docs/examples/controlled-vocabularies/local.ttl` | conceito local | conforme | local | `tests/api/test_controlled_vocabularies.py::test_schema_openapi_and_checked_examples` | V01: valores discriminados e equivalência dos exemplos RDF |

## docs/examples/profiles

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `docs/examples/profiles/core-2.0.0.json` | perfil declarativo | regressão | core-2.0.0 | `tests/api/test_declarative_profiles.py::test_generated_schema_artifacts_examples_and_discriminators` | P01/H01: verificação indireta pelo gerador --check (inclui resolved) |
| `docs/examples/profiles/digital-2.0.0.json` | perfil declarativo | regressão | digital-2.0.0 | `tests/api/test_declarative_profiles.py::test_generated_schema_artifacts_examples_and_discriminators` | P01/H01: verificação indireta pelo gerador --check (inclui resolved) |
| `docs/examples/profiles/monograph-2.0.0.json` | perfil declarativo | regressão | monograph-2.0.0 | `tests/api/test_declarative_profiles.py::test_generated_schema_artifacts_examples_and_discriminators` | P01/H01: verificação indireta pelo gerador --check (inclui resolved) |
| `docs/examples/profiles/monograph-2.0.0.resolved.json` | perfil declarativo | regressão | monograph-2.0.0.resolved | `tests/api/test_declarative_profiles.py::test_generated_schema_artifacts_examples_and_discriminators` | P01/H01: verificação indireta pelo gerador --check (inclui resolved) |
| `docs/examples/profiles/serial-2.0.0.json` | perfil declarativo | regressão | serial-2.0.0 | `tests/api/test_declarative_profiles.py::test_generated_schema_artifacts_examples_and_discriminators` | P01/H01: verificação indireta pelo gerador --check (inclui resolved) |
| `docs/examples/profiles/work-minimal-2.0.0.json` | perfil declarativo | regressão | work-minimal-2.0.0 | `tests/api/test_declarative_profiles.py::test_generated_schema_artifacts_examples_and_discriminators` | P01/H01: verificação indireta pelo gerador --check (inclui resolved) |

## docs/examples/serialization

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `docs/examples/serialization/README.md` | README | regressão | README | Documento explicativo; não é entrada de teste | R01: geração e limites dos exemplos |
| `docs/examples/serialization/agent.json` | agent | conforme | agent | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/agent.jsonld` | agent | conforme | agent | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/agent.ttl` | agent | conforme | agent | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/instance.json` | instance | conforme | instance | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/instance.jsonld` | instance | conforme | instance | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/instance.ttl` | instance | conforme | instance | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/item.json` | item | conforme | item | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/item.jsonld` | item | conforme | item | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/item.ttl` | item | conforme | item | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/organization.json` | Agent (Organization) | conforme | organization | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/organization.jsonld` | Agent (Organization) | conforme | organization | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/organization.ttl` | Agent (Organization) | conforme | organization | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/related.json` | composição de seis Read | conforme | related | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/related.jsonld` | composição de seis Read | conforme | related | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/related.ttl` | composição de seis Read | conforme | related | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/subject.json` | subject | conforme | subject | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/subject.jsonld` | subject | conforme | subject | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/subject.ttl` | subject | conforme | subject | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/work.json` | work | conforme | work | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/work.jsonld` | work | conforme | work | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |
| `docs/examples/serialization/work.ttl` | work | conforme | work | `tests/api/test_semantic_serialization.py::test_paired_examples_are_executable` | R01: exemplos pareados, isomorfismo de Graph e composição explícita |

## docs/examples/validation

| Caminho | Entidade/funcionalidade | Classe | Cenário | Consumidor | Requisito/expectativa |
| --- | --- | --- | --- | --- | --- |
| `docs/examples/validation/conformant.json` | diagnóstico / Problem Details | conforme | conformant | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |
| `docs/examples/validation/consume.ts` | diagnóstico / Problem Details | caso-limite | consume | Nenhum: exemplo de consumo TypeScript fora do tsconfig do frontend | G02: integração de cliente futura; não afirmar typecheck deste arquivo |
| `docs/examples/validation/failed-validation.json` | diagnóstico / Problem Details | inválido | failed-validation | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |
| `docs/examples/validation/operational-failure.json` | diagnóstico / Problem Details | inválido | operational-failure | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |
| `docs/examples/validation/schema-error.json` | diagnóstico / Problem Details | inválido | schema-error | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |
| `docs/examples/validation/stale-revision.json` | diagnóstico / Problem Details | inválido | stale-revision | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |
| `docs/examples/validation/unknown-profile.json` | diagnóstico / Problem Details | inválido | unknown-profile | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |
| `docs/examples/validation/violations.json` | diagnóstico / Problem Details | inválido | violations | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |
| `docs/examples/validation/warnings.json` | diagnóstico / Problem Details | caso-limite | warnings | `tests/api/test_catalogographic_conformance.py::test_public_diagnostic_examples_match_current_contracts` | D01: gerador --check deriva oito exemplos reais; códigos/severidades/correlação |

## Recursos locais de perfil, shape e contexto

Não são dados do corpus. São fontes de expectativa versionadas no pacote `apps/api/src/libris/modules/bibliographic/resources/`.
Veja [inventário SHACL por propriedade](shacl-inventory.md); não duplicamos seus constraints aqui.

| Família/artefatos | Consumidores e expectativa |
| --- | --- |
| monograph-v1.json/.ttl, monograph-v1.1.json/.ttl, monograph-v1.1-composed.ttl, authority-v1.json/.ttl, catalog-profile.schema.json | test_declarative_profiles.py::test_legacy_models_ids_files_and_schema_preserved; test_catalogographic_contract.py::test_profile_schema_and_shacl_cardinalities; hashes, cardinalidade e contexto corretos |
| contexts/bibframe-v1.jsonld | test_semantic_serialization.py::test_context_version_integrity_and_freshness; contexto local imutável e cópia isolada |
| profiles-v2/*.json (definições, schemas, registros, manifest e locks) | test_declarative_profiles.py::test_examples_roundtrip_and_resolve / test_generated_schema_artifacts_examples_and_discriminators / test_package_release_fingerprints_reject_mutation; test_semantic_extensions.py::test_semantic_release_tampering_rejected; versões, herança, hashes e registro autorizado |
| controlled-values-v1/*.schema.json | test_controlled_vocabularies.py::test_schema_openapi_and_checked_examples / test_resolution_and_registry_generated_schemas; schemas gerados correspondem aos contratos |

## Suítes e testes locais

Além de fixtures em arquivo, estas suítes usam parâmetros, grafos construídos no teste e doubles transacionais.
A lista abaixo inventaria funções; a matriz descreve o requisito e a força da evidência. Não confundir doubles com commit PostgreSQL.

### tests/api/test_audit_history.py

`test_taxonomy_and_immutable_events`, `test_invalid_combinations`, `test_invalid_editorial_combinations`, `test_invalid_restore`, `test_execution_context`, `test_technical_namespace_is_controlled`, `test_trusted_human_unknown_and_privacy`, `test_timestamp_normalized_to_utc`, `test_release_resolution_preserves_profile`, `test_editorial_adapter`, `test_history_permission_policy`, `test_history_denial_precedes_storage`, `test_service_rejects_payload_actor_before_storage`, `test_query_limit`, `test_isomorphic_blank_nodes_and_order`, `test_diff_preserves_term_details`, `test_add_remove_and_structurally_changed_blank_nodes`, `test_revision_invariants`, `test_governed_editorial_operations_are_explicit`, `test_supersession_requires_distinct_successor_and_reason`, `test_withdrawal_requires_reason_and_record_scope`, `test_semantic_comparison_cyclic_and_symmetric_blank_nodes`.

### tests/api/test_bibliographic.py

`test_create_resource_relationships`, `test_round_trip`, `test_profile_valid_and_invalid`, `test_profile_warning_and_inverse_consistency`, `test_stable_identity`, `test_reject_unsafe_contexts`, `test_local_context`, `test_invalid_input`, `test_size_limit`, `test_profile_is_declarative`, `test_invalid_uri_base`, `test_limits_from_environment`, `test_reject_keyword_aliases_and_nested_graphs`, `test_root_and_storage_constraints`, `test_refuse_conversion_that_changes_literal_terms`, `test_keywords_in_literals_are_data`, `test_identity_requires_http_semantic_uri`.

### tests/api/test_catalog_diagnostics.py

`test_real_validation_and_immutable_release`, `test_authority_and_institutional_fixtures`, `test_context_and_profile_policy`, `test_technical_failure_is_distinct`, `test_request_correlation_in_service_and_rejection`, `test_real_engine_severities`, `test_multiple_fields_and_global_diagnostics`, `test_component_codes_do_not_depend_on_messages`, `test_complex_paths`, `test_stable_serialization_under_blank_node_renaming_and_engine_order`, `test_schema_adapter_uses_pydantic_contract_and_omits_input`, `test_result_invariants`, `test_http_mapping_and_security`, `test_real_http_schema_errors_openapi_and_authentication`, `test_http_rejection_includes_real_diagnostics_and_single_request_id`, `test_http_preconditions`, `test_invalid_create_never_opens_transaction`, `test_unknown_and_incompatible_profiles_keep_typed_errors`, `test_value_policy_preserves_only_safe_iris`, `test_anonymous_identifier_does_not_hash_sensitive_lexical_values`, `test_database_error_classification`, `test_http_adaptation_reuses_request_id_for_precomputed_report`.

### tests/api/test_catalogographic_conformance.py

`test_contract_pipeline_preserves_identity_and_semantics`, `test_required_rdf_properties_have_release_specific_diagnostics`, `test_legacy_book_examples_remain_equivalent`, `test_public_diagnostic_examples_match_current_contracts`.

### tests/api/test_catalogographic_contract.py

`test_corpus_shacl`, `test_corpus_lossless_entity_snapshots`, `test_profile_schema_and_shacl_cardinalities`, `test_profile_rejects_inconsistent_form_contract`, `test_profile_rejects_invalid_resource_field`, `test_shared_authority_is_a_reference_not_a_copy`, `test_multiple_editions_items_and_translation_ownership`, `test_invalid_inverse_is_detected_without_rewriting_the_input`, `test_snapshot_rejects_foreign_description_inverse_and_type_changes`, `test_composition_relabels_blank_nodes_and_rejects_duplicate_roots`, `test_uri_and_write_token_contract`, `test_authority_and_concept_labels_have_distinct_rules`, `test_absent_instance_title_and_isbn_are_valid`.

### tests/api/test_catalogographic_schemas.py

`test_fixture_round_trip`, `test_required_properties`, `test_unknown_fields`, `test_immutable_or_private_fields_in_update`, `test_patch_presence_null_empty_and_replacement`, `test_optional_create_fields_and_default_isolation`, `test_iri_preserves_text`, `test_invalid_iri`, `test_invalid_persistent_uri`, `test_invalid_read_identity`, `test_reference_does_not_invent_identifier_alternatives`, `test_language_tags`, `test_invalid_language_tags`, `test_invalid_text`, `test_text_is_transcribed_without_normalization`, `test_unique_language_labels`, `test_work_primary_title_and_item_local_identifier`, `test_contribution_cardinality`, `test_subject_label_disjointness_and_partial_validation`, `test_supported_agent_types`, `test_auxiliary_structures`, `test_publication_dates_preserve_lexical_form`, `test_invalid_publication_dates`, `test_isbn_checksum_is_not_an_approved_constraint`, `test_fastapi_openapi_and_validation_without_services`, `test_contract_properties_match_versioned_profiles`, `test_invalid_percent_escapes`, `test_publication_date_years_and_timezones`, `test_invalid_publication_calendar_and_timezone`, `test_all_optional_collections_and_multivalues`, `test_documented_json_examples_are_valid`, `test_read_uri_is_not_rebuilt_or_normalized`, `test_invalid_http_port`.

### tests/api/test_controlled_vocabularies.py

`test_multilingual_json_identity_metadata_and_no_network`, `test_invalid_uri`, `test_inconsistent_concepts`, `test_alternatives_allow_multiple_labels_per_language`, `test_discrimination`, `test_ambiguous_payloads`, `test_local_stored_identity_never_derived_from_label`, `test_known_states_use_existing_diagnostics`, `test_membership_exact_uri_not_labels_prefix_or_payload_vocabulary`, `test_wrong_type_and_explicit_profile_enum`, `test_provider_failures_preserve_accepted_value_and_known_evidence`, `test_success_deprecation_replacement_is_enrichment_not_identity_change`, `test_cache_policy_clock_ttls_and_failure_invariants`, `test_external_rdf_preserves_uri_without_publishing_enrichment`, `test_local_rdf_description_preserves_labels_notation_identity`, `test_typed_literal_round_trips`, `test_entity_resolution_reuses_stored_identity_and_rejects_pending`, `test_historical_work_schema_and_shacl_stay_compatible`, `test_schema_openapi_and_checked_examples`, `test_provider_definitive_evidence_does_not_rewrite_original`, `test_membership_configuration_is_versioned_and_rejects_duplicate_evidence`, `test_resolution_and_registry_generated_schemas`.

### tests/api/test_declarative_profiles.py

`test_examples_roundtrip_and_resolve`, `test_five_entities_selection_and_no_python_subclasses`, `test_sections_and_canonical_auxiliaries`, `test_new_form_required_does_not_change_semantic_cardinality`, `test_invalid_iris`, `test_invalid_field_structure`, `test_invalid_cardinalities`, `test_duplicate_identifiers`, `test_invalid_semantic_configuration`, `test_condition_validation_and_cycle`, `test_invalid_condition_operand_type`, `test_composition_rejects_missing_base_cycles_duplicate_releases_and_shape_conflicts`, `test_conflicting_overrides`, `test_authorized_specialization_and_reorganization`, `test_typed_defaults_and_roundtrip`, `test_bad_calendar_defaults`, `test_language_defaults_enums_and_structured_values_are_not_strings`, `test_external_namespace_registry_and_deprecated_properties`, `test_registry_rejects_namespace_overlap_and_duplicate_shapes`, `test_selection_precedence_is_deterministic_and_explicit_release_never_replaced`, `test_published_used_and_composed_releases_immutable_and_copy_isolated`, `test_evolution_classification`, `test_legacy_models_ids_files_and_schema_preserved`, `test_generated_schema_artifacts_examples_and_discriminators`, `test_openapi_contracts_in_isolated_fastapi_without_registering_production_routes`, `test_versioned_shapes_context_and_result_path_mapping`, `test_snapshot_context_preserves_uris_revisions_and_release`, `test_explicit_lifecycle_preserves_content_and_never_follows_replacement`, `test_composed_validation_reuses_engine_and_auxiliary_mapping`, `test_invalid_fixture_corpus`, `test_shared_predicate_cannot_mix_source_specific_targets`, `test_bibframe_terms_are_from_reviewed_official_v2_inventory`, `test_authority_and_relationship_configuration_uses_iris_not_embedded_entities`, `test_structured_form_cycles_and_missing_shape_coverage_are_rejected`, `test_shape_file_resolver_is_not_a_network_loader`, `test_package_release_fingerprints_reject_mutation`, `test_artifact_generator_never_overwrites_existing_release_fingerprints`.

### tests/api/test_editorial.py

`test_entire_matrix`, `test_initial_draft_and_unknown_states`, `test_justification_required`, `test_approval_and_validation_are_required`, `test_content_and_editorial_revisions_are_independent`, `test_withdraw_republish_pending_and_archive`, `test_content_edits_require_editable_cycle`, `test_stale_editorial_and_content_expectations`, `test_permissions_reject_without_mutation`, `test_authorized_submit_approve_publish_and_republish`, `test_real_validation_bibliographic_and_authority`, `test_invalid_catalog_blocks_publication`, `test_publication_dependencies_fail_closed`, `test_two_concurrent_operations_have_one_winner`, `test_content_race_cannot_publish_obsolete_candidate`, `test_retirement_preserves_identity_and_history`, `test_invalid_identity_decisions`, `test_shacl_unavailable_never_produces_publication`, `test_required_local_reference_integrity`, `test_required_local_reference_can_be_published`, `test_content_cas_is_checked_even_when_editorial_version_matches`, `test_authority_manager_needs_explicit_editorial_capability`.

### tests/api/test_persistent_identifiers.py

`test_domain_accepts_absolute_identity_without_rewriting`, `test_domain_rejects_invalid_identity_and_base`, `test_uuid_type_and_immutable_identity`, `test_configuration_change_only_affects_new_identities`, `test_read_fixtures_and_metadata_updates_preserve_identity`, `test_reference_examples_are_executable`, `test_local_resolution_uses_stored_identity`, `test_nonexistent_wrong_type_or_inconsistent_stored_identity`, `test_invalid_reference_contracts`, `test_pending_references_do_not_resolve_over_http`, `test_shared_external_identifier_is_not_local_identity`, `test_jsonld_and_turtle_examples_are_isomorphic_and_profile_valid`, `test_fastapi_schema_exposes_discriminated_references_without_endpoints`.

### tests/api/test_relationships.py

`test_versioned_examples`, `test_reference_roundtrip`, `test_invalid_local_reference`, `test_required_reference_attributes`, `test_registered_relationships`, `test_incompatible_targets`, `test_extension_is_explicit_and_does_not_redefine_canonical_semantics`, `test_profile_minimum_is_not_an_ontology_axiom`, `test_collection_operations_are_atomic_and_distinguish_omission`, `test_invalid_operations`, `test_remove_mandatory_link_and_unknown_replace_rejected`, `test_referential_resolution_and_legitimate_shared_authorities`, `test_unreconciled_requires_draft_and_external_is_reported_without_network`, `test_alias_duplicates_and_identity_mismatch_after_resolution`, `test_real_target_type_and_role_policy`, `test_cycles_require_complete_supplied_closure`, `test_existing_dtos_accept_typed_and_legacy_references_without_recursion`, `test_json_schema_and_semantic_paths`, `test_application_update_resolves_local_aliases_and_preserves_stored_uri`, `test_operation_cannot_hide_wrong_origin_or_derived_link`, `test_held_by_candidate_requires_organization`, `test_publication_groups_remain_distinct_and_roles_are_preserved`, `test_metadata_inverses_match_verified_vocabulary`, `test_matrix_covers_the_executable_registry`, `test_resolved_local_and_external_uri_do_not_duplicate`, `test_registered_profile_cardinality_minimum_and_maximum`, `test_self_alias_rejected_after_resolution`.

### tests/api/test_semantic_extensions.py

`test_namespace_conflicts`, `test_governed_namespace_requires_traceability`, `test_registered_terms_and_origin_without_new_entities`, `test_known_but_unauthorized`, `test_external_field_contract_rejections`, `test_invalid_term_metadata`, `test_historical_registry_and_profile_are_not_reinterpreted`, `test_unknown_releases_and_pure_bibframe`, `test_semantic_release_tampering_rejected`, `test_semantic_redefinition_rejected`, `test_deprecated_term_cannot_be_new_editable_field`, `test_required_extension_inherits_and_composes_without_ontology_cardinality`, `test_shacl_external_policy_rejections`, `test_extension_warning_and_info_nonblocking`, `test_examples_roundtrip_preserve_all_terms`, `test_untrusted_context_rejected`, `test_data_preservation_does_not_authorize_editing`, `test_owned_snapshot_and_revision_preserve_extension`, `test_registry_association_survives_lifecycle_and_inheritance`, `test_invalid_semantic_association_rejected`, `test_standalone_bibframe_override_rejected`, `test_unknown_and_unapproved_classes_are_not_profile_resources`.

### tests/api/test_semantic_serialization.py

`test_five_resources_owned_equivalence_and_no_mutation`, `test_work_structure_and_all_fields`, `test_instance_structure_identifiers_publication_extent`, `test_item_structure_and_shelfmark_contract`, `test_agent_types_labels_and_external_links`, `test_subject_skos_hierarchy`, `test_absence_and_rdf_set_semantics`, `test_direct_canonical_graph_preserves_extension_and_namespaces`, `test_explicit_composition_blank_nodes_and_inverses`, `test_local_references_resolve_exact_stored_identity`, `test_inconsistent_reference_mapping`, `test_invalid_fixtures`, `test_revalidation_rejects_mutated_dto_and_self_reference`, `test_invalid_graphs_and_output_limits`, `test_document_bytes_depth_and_keyword_safety`, `test_untrusted_jsonld_policy`, `test_context_version_integrity_and_freshness`, `test_paired_examples_are_executable`, `test_negotiation`, `test_negotiation_not_acceptable`, `test_negotiation_available_formats_and_configured_default`, `test_canonical_rdf_collection_and_cycle`, `test_collection_order_is_not_semantic`, `test_unrepresentable_lexical_form_is_explicit_error`, `test_unicode_iris_preserved`, `test_orphan_blank_cycle_refuses_lossy_jsonld`, `test_invalid_jsonld_structure_is_not_silently_dropped`, `test_publication_self_reference_rejected`.

### tests/api/test_shacl_validation.py

`test_entities_and_auxiliaries`, `test_references_never_download_or_supply_rules`, `test_severities_and_exact_diagnostics`, `test_blank_node_iri_collision_and_complex_path_do_not_correlate`, `test_infrastructure_failures_are_not_nonconformance`, `test_invalid_resolution`, `test_empty_graph_conformance_does_not_authorize_persistence`, `test_all_configurable_releases_execute`, `test_specialized_minimum_enum_datatype_and_optional_extension`, `test_language_policy_and_deterministic_isolated_supplement`, `test_contradictory_descriptor_rejected_before_engine`, `test_violation_prevents_transaction_and_validator_failure_prevents_write`, `test_shape_cache_isolation_content_invalidation_and_local_flags`, `test_complex_inverse_path_preserved_in_report`, `test_contradictory_datatypes_and_target_classes`, `test_engine_failure_cannot_open_create_transaction`, `test_revise_violation_exits_transaction_without_saving`, `test_shape_registry_metadata_and_execution_registry_agree`, `test_multiple_violations_remain_distinct_and_unmapped_results_survive`, `test_supplied_shapes_path_is_never_opened`, `test_optional_language_allowlist_does_not_require_language`, `test_core_supplement_does_not_duplicate_existing_constraints`, `test_nonblocking_severity_allows_document_preparation`.

## Integração PostgreSQL

Todas são opt-in, marcadas integration e fora de testpaths padrão. Pré-requisitos e isolamento na [reprodução](catalogographic-v1-testing.md).

### tests/integration/test_audit_migrations_postgres.py

`test_incremental_migration_preserves_legacy_and_downgrade`.

### tests/integration/test_audit_postgres.py

`test_content_history_restore_and_authorization`, `test_audit_failure_rolls_back_resource_revision_and_cas`, `test_real_concurrent_transactions_leave_one_revision_and_event`, `test_postgres_blocks_audit_mutation`, `test_deterministic_order_and_events_without_content_revision`, `test_direct_sql_constraints_and_referential_integrity`, `test_technical_actor_persistence`.

### tests/integration/test_diagnostic_transactions_postgres.py

`test_public_rejections_rollback_postgres`.

### tests/integration/test_editorial_migrations_postgres.py

`test_editorial_upgrade_from_previous_head_and_safe_downgrade`.

### tests/integration/test_editorial_postgres.py

`test_persistent_workflow_candidate_return_restore_and_archive`, `test_transition_failures_roll_back_in_fresh_session`, `test_state_and_revision_constraints_and_conditional_zero_row_conflict`, `test_legacy_initialization_and_denied_attempt_do_not_fabricate_history`, `test_publication_all_supported_types_with_local_reference_integrity`, `test_unclassified_required_reference_blocks_publication_atomically`, `test_invalid_legacy_shacl_publication_preserves_diagnostics_and_state`, `test_concurrent_sessions_reject_stale_decisions`, `test_local_cycle_rejected_and_external_classification_explicit`, `test_local_dependency_cannot_change_between_validation_and_commit`, `test_content_audit_failure_rolls_back_editorial_and_snapshot`, `test_publication_structured_links_and_agent_kind`.

### tests/integration/test_entity_revisions_postgres.py

`test_entity_revisions_postgres`.

### tests/integration/test_persistent_identifiers_postgres.py

`test_identity_uniqueness_postgres`.

### tests/integration/test_revision_actor_postgres.py

`test_revision_actor_postgres`.

### tests/integration/test_semantic_postgres.py

`test_postgres_revisions_roundtrip_and_concurrency`.

## Consumidores adicionais e uso compartilhado

As linhas por fixture acima indicam a evidência principal. Este índice acrescenta consumidores de mutações e helpers, que também reutilizam os arquivos originais. As rejeições derivadas em memória não são fixtures inválidas independentes.

| Fixture ou conjunto | Consumidores adicionais |
| --- | --- |
| tests/fixtures/bibliographic/contracts/work-create.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_patch_presence_null_empty_and_replacement`; `tests/api/test_catalogographic_schemas.py::test_optional_create_fields_and_default_isolation`; `tests/api/test_catalogographic_schemas.py::test_work_primary_title_and_item_local_identifier` |
| tests/fixtures/bibliographic/contracts/work-read.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_invalid_read_identity`; `tests/api/test_catalogographic_schemas.py::test_work_primary_title_and_item_local_identifier`; `tests/api/test_catalogographic_schemas.py::test_read_uri_is_not_rebuilt_or_normalized`; `tests/api/test_catalogographic_conformance.py::test_required_rdf_properties_have_release_specific_diagnostics` |
| tests/fixtures/bibliographic/contracts/work-update.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_work_primary_title_and_item_local_identifier` |
| tests/fixtures/bibliographic/contracts/instance-create.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_patch_presence_null_empty_and_replacement`; `tests/api/test_catalogographic_schemas.py::test_optional_create_fields_and_default_isolation` |
| tests/fixtures/bibliographic/contracts/instance-read.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_invalid_read_identity`; `tests/api/test_catalogographic_conformance.py::test_required_rdf_properties_have_release_specific_diagnostics` |
| tests/fixtures/bibliographic/contracts/instance-update.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields` |
| tests/fixtures/bibliographic/contracts/item-create.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_patch_presence_null_empty_and_replacement`; `tests/api/test_catalogographic_schemas.py::test_optional_create_fields_and_default_isolation`; `tests/api/test_catalogographic_schemas.py::test_work_primary_title_and_item_local_identifier` |
| tests/fixtures/bibliographic/contracts/item-read.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_invalid_read_identity`; `tests/api/test_catalogographic_schemas.py::test_work_primary_title_and_item_local_identifier`; `tests/api/test_catalogographic_conformance.py::test_required_rdf_properties_have_release_specific_diagnostics` |
| tests/fixtures/bibliographic/contracts/item-update.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_work_primary_title_and_item_local_identifier` |
| tests/fixtures/bibliographic/contracts/agent-create.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_patch_presence_null_empty_and_replacement`; `tests/api/test_catalogographic_schemas.py::test_optional_create_fields_and_default_isolation`; `tests/api/test_catalogographic_schemas.py::test_supported_agent_types` |
| tests/fixtures/bibliographic/contracts/agent-read.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_invalid_read_identity`; `tests/api/test_catalogographic_conformance.py::test_required_rdf_properties_have_release_specific_diagnostics` |
| tests/fixtures/bibliographic/contracts/agent-update.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields` |
| tests/fixtures/bibliographic/contracts/subject-create.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_patch_presence_null_empty_and_replacement`; `tests/api/test_catalogographic_schemas.py::test_optional_create_fields_and_default_isolation`; `tests/api/test_catalogographic_schemas.py::test_subject_label_disjointness_and_partial_validation` |
| tests/fixtures/bibliographic/contracts/subject-read.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_required_properties`; `tests/api/test_catalogographic_schemas.py::test_all_optional_collections_and_multivalues`; `tests/api/test_catalogographic_schemas.py::test_invalid_read_identity`; `tests/api/test_catalogographic_schemas.py::test_subject_label_disjointness_and_partial_validation`; `tests/api/test_catalogographic_conformance.py::test_required_rdf_properties_have_release_specific_diagnostics` |
| tests/fixtures/bibliographic/contracts/subject-update.json | `tests/api/test_catalogographic_schemas.py::test_unknown_fields`; `tests/api/test_catalogographic_schemas.py::test_subject_label_disjointness_and_partial_validation` |
| tests/fixtures/bibliographic/institutional/controlled-subjects.ttl | `tests/api/test_catalogographic_contract.py::test_authority_and_concept_labels_have_distinct_rules` |
| tests/fixtures/bibliographic/institutional/external-identifiers.ttl | `tests/api/test_catalogographic_contract.py::test_authority_and_concept_labels_have_distinct_rules` |
| tests/fixtures/bibliographic/institutional/multiple-items.ttl | `tests/api/test_catalogographic_contract.py::test_invalid_inverse_is_detected_without_rewriting_the_input`; `tests/api/test_catalogographic_contract.py::test_multiple_editions_items_and_translation_ownership` |
| tests/fixtures/bibliographic/institutional/shared-authority.ttl | `tests/api/test_catalogographic_contract.py::test_shared_authority_is_a_reference_not_a_copy` |
| tests/fixtures/bibliographic/institutional/single-author.ttl | `tests/api/test_catalogographic_contract.py::test_snapshot_rejects_foreign_description_inverse_and_type_changes` |
| tests/fixtures/bibliographic/institutional/translated-monograph.ttl | `tests/api/test_catalogographic_contract.py::test_multiple_editions_items_and_translation_ownership` |
| tests/fixtures/bibliographic/institutional/two-editions.ttl | `tests/api/test_catalogographic_contract.py::test_multiple_editions_items_and_translation_ownership` |
| tests/fixtures/bibliographic/institutional/without-isbn.ttl | `tests/api/test_catalogographic_contract.py::test_absent_instance_title_and_isbn_are_valid` |
| tests/fixtures/bibliographic/serialization/valid/agent.json | `tests/api/test_semantic_serialization.py::test_agent_types_labels_and_external_links` |
| tests/fixtures/bibliographic/serialization/valid/instance.json | `tests/api/test_semantic_serialization.py::test_instance_structure_identifiers_publication_extent`; `tests/api/test_semantic_serialization.py::test_publication_self_reference_rejected` |
| tests/fixtures/bibliographic/serialization/valid/item.json | `tests/api/test_semantic_serialization.py::test_item_structure_and_shelfmark_contract` |
| tests/fixtures/bibliographic/serialization/valid/minimal-work.json | `tests/api/test_semantic_serialization.py::test_absence_and_rdf_set_semantics`; `tests/api/test_semantic_serialization.py::test_direct_canonical_graph_preserves_extension_and_namespaces`; `tests/api/test_semantic_serialization.py::test_inconsistent_reference_mapping`; `tests/api/test_semantic_serialization.py::test_invalid_graphs_and_output_limits`; `tests/api/test_semantic_serialization.py::test_local_references_resolve_exact_stored_identity`; `tests/api/test_semantic_serialization.py::test_revalidation_rejects_mutated_dto_and_self_reference`; `tests/api/test_semantic_serialization.py::test_unicode_iris_preserved` |
| tests/fixtures/bibliographic/serialization/valid/subject.json | `tests/api/test_semantic_serialization.py::test_inconsistent_reference_mapping`; `tests/api/test_semantic_serialization.py::test_local_references_resolve_exact_stored_identity`; `tests/api/test_semantic_serialization.py::test_subject_skos_hierarchy` |
| tests/fixtures/bibliographic/serialization/valid/work.json | `tests/api/test_semantic_serialization.py::test_collection_order_is_not_semantic`; `tests/api/test_semantic_serialization.py::test_work_structure_and_all_fields` |
| tests/fixtures/bibliographic/institutional/invalid-numeric-title.ttl | `tests/api/test_declarative_profiles.py::test_composed_validation_reuses_engine_and_auxiliary_mapping` |
| tests/fixtures/bibliographic/institutional/multiple-items.ttl | `tests/api/test_declarative_profiles.py::test_composed_validation_reuses_engine_and_auxiliary_mapping` |
| tests/fixtures/bibliographic/institutional/single-author.ttl e invalid-missing-title.ttl | `tests/api/test_catalog_diagnostics.py::test_authority_and_institutional_fixtures` |
| tests/fixtures/bibliographic/institutional/invalid-literal-work-reference.ttl | `tests/api/test_declarative_profiles.py::test_versioned_shapes_context_and_result_path_mapping` |
| tests/fixtures/bibliographic/institutional/single-author.ttl | `tests/api/test_declarative_profiles.py::test_shape_file_resolver_is_not_a_network_loader` |
| tests/fixtures/bibliographic/identifiers/instance-read.json | `tests/api/test_persistent_identifiers.py::test_shared_external_identifier_is_not_local_identity` |
| tests/fixtures/bibliographic/serialization/valid/{work,instance,item,agent,organization,subject}.json | `tests/api/test_semantic_serialization.py::test_explicit_composition_blank_nodes_and_inverses` |
| tests/fixtures/bibliographic/serialization/valid/subject.json | `tests/api/test_semantic_serialization.py::test_local_references_resolve_exact_stored_identity` / `test_inconsistent_reference_mapping`, inclusive via helper subject_resolution |
| tests/fixtures/bibliographic/book.ttl | `tests/api/test_bibliographic.py::test_profile_valid_and_invalid` / `test_profile_warning_and_inverse_consistency` / `test_stable_identity` / `test_root_and_storage_constraints`; gerador `scripts/generate_diagnostic_examples.py --check` chamado pela suíte nova |
| docs/examples/serialization/work.json | `tests/api/test_controlled_vocabularies.py::test_historical_work_schema_and_shacl_stay_compatible` |
| tests/fixtures/bibliographic/extensions/work.ttl | `tests/api/test_semantic_extensions.py::test_owned_snapshot_and_revision_preserve_extension` / `test_shacl_external_policy_rejections` / `test_extension_warning_and_info_nonblocking` / `test_data_preservation_does_not_authorize_editing`, via helper graph |
