# Inventário de campos do contrato catalográfico v1

Identificador `urn:libris:contract:catalogographic:v1`; especificação documental **1.0.0**.
Gerado por `scripts/generate_catalogographic_contract.py`; não editar as tabelas.
[Referência canônica](catalogographic-contract.md) e [JSON Schema completo](catalogographic-contract-v1.schema.json).

As 22 raízes são os quinze DTOs de entidades, quatro de relacionamentos,
CatalogValidationResult, CatalogValueDocument e ProblemDetails. As demais
definições são estruturas alcançáveis, não novos recursos ou endpoints.
Perfis/configurações têm inventário e schemas próprios em [perfis](catalog-profiles.md), [SHACL](shacl-inventory.md) e [vocabulários](controlled-vocabularies.md).

Obrigatório significa presença no JSON de entrada. Cardinalidade conta elementos
de uma lista **quando fornecida**, ou um valor escalar; não soma triplas RDF.
Update permite omissão mesmo de propriedades obrigatórias do estado final.
`—` significa ausência de default anunciado pelo schema; listas com factory
têm default runtime `[]`, mesmo quando o schema não o anuncia. Em Update,
`None` interno é sentinela de omissão: campos obrigatórios não aceitam null.
Null permitido no schema não implica presença de tripla ou remoção em todo contrato.

Este schema é de **validação**. JSON Schema não expressa todos os validadores
Pydantic (IRI, coerência UUID/URI, mínimo Title/Local, idioma único, disjunção,
datas e estado do relatório). Ver [invariantes e serialização](catalogographic-schemas.md).
Valores de enum por referência constam na definição correspondente.

## AddLinks

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `op` | `"add"` | `sim` | `não` | `1` | `—` | `—` |
| `links` | `lista de DirectLink / ContributionLink / PublicationLink` | `sim` | `não` | `1..*` | `—` | `—` |

## AgentCreate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `["Agent", "Person", "Organization"]` | `sim` | `não` | `1` | `—` | `—` |
| `authorized_name` | `lista de LocalizedText` | `sim` | `não` | `1..*` | `—` | `—` |
| `variant_name` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `identified_by` | `lista de Identifier` | `não` | `não` | `0..*` | `—` | `—` |
| `external_reference` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `provenance` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `related_authority` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |

## AgentRead

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `internal_id` | `string (uuid)` | `sim` | `não` | `1` | `—` | `—` |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `kind` | `["Agent", "Person", "Organization"]` | `sim` | `não` | `1` | `—` | `—` |
| `authorized_name` | `lista de LocalizedText` | `sim` | `não` | `1..*` | `—` | `—` |
| `variant_name` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `identified_by` | `lista de Identifier` | `não` | `não` | `0..*` | `—` | `—` |
| `external_reference` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `provenance` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `related_authority` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |

## AgentUpdate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `authorized_name` | `lista de LocalizedText` | `não` | `não` | `1..*` | `—` | `—` |
| `variant_name` | `lista de LocalizedText / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `identified_by` | `lista de Identifier / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `external_reference` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `provenance` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `related_authority` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference / null` | `não` | `sim` | `0..*` | `null` | `—` |

## CatalogCode

Valores: `["request.malformed", "schema.invalid", "schema.required", "schema.cardinality", "schema.value", "shacl.violation", "shacl.min_count", "shacl.max_count", "shacl.qualified_min_count", "shacl.qualified_max_count", "shacl.datatype", "shacl.node_kind", "shacl.class", "shacl.in", "profile.unknown", "profile.incompatible", "profile.unavailable", "profile.policy", "identity.invalid", "reference.invalid", "reference.unverified", "reference.deprecated", "reference.vocabulary_mismatch", "reference.vocabulary_unverified", "reference.resolver_unavailable", "resource.unknown", "state.conflict", "revision.stale", "revision.precondition_required", "validation.rejected", "validator.failure", "infrastructure.unavailable", "internal.failure", "editorial.state_invalid", "editorial.transition_forbidden", "editorial.permission_denied", "editorial.precondition_required", "editorial.content_not_publishable", "editorial.version_stale", "editorial.approval_stale", "identity.operation_invalid"]`.

## CatalogValidationResult

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `contract_version` | `"1.0"` | `não` | `não` | `1` | `"1.0"` | `—` |
| `state` | `["completed", "failed"]` | `sim` | `não` | `1` | `—` | `—` |
| `conforms` | `boolean / null` | `não` | `sim` | `1` | `null` | `—` |
| `profile_id` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `profile_release` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `profile_version` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `context` | `["snapshot", "composed"]` | `sim` | `não` | `1` | `—` | `—` |
| `request_id` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `issues` | `lista de Diagnostic` | `não` | `não` | `0..*` | `[]` | `—` |

## CatalogValueDocument

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `format` | `"libris.catalog-value"` | `não` | `não` | `1` | `"libris.catalog-value"` | `—` |
| `contract_version` | `"1.0"` | `não` | `não` | `1` | `"1.0"` | `—` |
| `value` | `LiteralValue / ControlledConcept / LocalConcept / EntityValue` | `sim` | `não` | `1; 1; 1; 1` | `—` | `—` |

## Classification

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `classification_portion` | `lista de string` | `sim` | `não` | `1..*` | `—` | `—` |
| `source` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |

## Contribution

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `agent` | `ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1` | `—` | `{"discriminator": {"mapping": {"external": "#/$defs/ExternalReference", "local": "#/$defs/LocalReference", "unreconciled": "#/$defs/UnreconciledReference"}, "propertyName": "kind"}}` |
| `role` | `lista de ResourceReference` | `sim` | `não` | `1..*` | `—` | `—` |

## ContributionLink

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"contribution"` | `não` | `não` | `1` | `"contribution"` | `—` |
| `source` | `LocalReference` | `sim` | `não` | `1` | `—` | `—` |
| `target` | `LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1; 1` | `—` | `—` |
| `predicate` | `"http://id.loc.gov/ontologies/bibframe/contribution"` | `não` | `não` | `1` | `"http://id.loc.gov/ontologies/bibframe/contribution"` | `—` |
| `role` | `lista de string` | `sim` | `não` | `1..*` | `—` | `—` |

## ControlledConcept

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `vocabulary` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `label` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `alternative_labels` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `notation` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |
| `source` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |
| `status` | `["resolved", "unverified", "invalid", "deprecated", "unavailable"]` | `não` | `não` | `1` | `"unverified"` | `—` |
| `replacement` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |
| `kind` | `"controlled_concept"` | `sim` | `não` | `1` | `—` | `—` |

## Diagnostic

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `code` | `CatalogCode` | `sim` | `não` | `1` | `—` | `—` |
| `message` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `category` | `["schema", "semantic", "profile", "identity", "reference", "state", "technical"]` | `sim` | `não` | `1` | `—` | `—` |
| `severity` | `["Violation", "Warning", "Info"]` | `não` | `não` | `1` | `"Violation"` | `—` |
| `field_ids` | `lista de string` | `não` | `não` | `0..*` | `[]` | `—` |
| `path` | `RdfPath / null` | `não` | `sim` | `1` | `null` | `—` |
| `focus_node` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `value` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `constraint` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `source_shape` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `messages` | `lista de string` | `não` | `não` | `0..*` | `[]` | `—` |
| `parameters` | `object` | `não` | `não` | `1` | `—` | `—` |

## DirectLink

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"direct"` | `não` | `não` | `1` | `"direct"` | `—` |
| `source` | `LocalReference` | `sim` | `não` | `1` | `—` | `—` |
| `target` | `LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1; 1` | `—` | `—` |
| `predicate` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |

## EntityType

Valores: `["Work", "Instance", "Item", "Agent", "Subject"]`.

## EntityValue

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"entity_reference"` | `sim` | `não` | `1` | `—` | `—` |
| `reference` | `LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1; 1` | `—` | `—` |

## Extent

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `label` | `lista de LocalizedText` | `sim` | `não` | `1..*` | `—` | `—` |

## ExternalReference

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"external"` | `não` | `não` | `1` | `"external"` | `—` |
| `entity_type` | `EntityType` | `sim` | `não` | `1` | `—` | `—` |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `namespace` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |
| `external_id` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |

## Identifier

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `["Identifier", "Local", "Isbn"]` | `não` | `não` | `1` | `"Identifier"` | `—` |
| `value` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `source` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |

## InstanceCreate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `instance_of` | `ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1` | `—` | `{"discriminator": {"mapping": {"external": "#/$defs/ExternalReference", "local": "#/$defs/LocalReference", "unreconciled": "#/$defs/UnreconciledReference"}, "propertyName": "kind"}}` |
| `title` | `lista de Title` | `não` | `não` | `0..*` | `—` | `—` |
| `edition_statement` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `provision_activity` | `lista de Publication` | `não` | `não` | `0..*` | `—` | `—` |
| `identified_by` | `lista de Identifier` | `não` | `não` | `0..*` | `—` | `—` |
| `extent` | `lista de Extent` | `não` | `não` | `0..*` | `—` | `—` |
| `carrier` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `note` | `lista de Note` | `não` | `não` | `0..*` | `—` | `—` |

## InstanceRead

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `internal_id` | `string (uuid)` | `sim` | `não` | `1` | `—` | `—` |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `instance_of` | `ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1` | `—` | `{"discriminator": {"mapping": {"external": "#/$defs/ExternalReference", "local": "#/$defs/LocalReference", "unreconciled": "#/$defs/UnreconciledReference"}, "propertyName": "kind"}}` |
| `title` | `lista de Title` | `não` | `não` | `0..*` | `—` | `—` |
| `edition_statement` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `provision_activity` | `lista de Publication` | `não` | `não` | `0..*` | `—` | `—` |
| `identified_by` | `lista de Identifier` | `não` | `não` | `0..*` | `—` | `—` |
| `extent` | `lista de Extent` | `não` | `não` | `0..*` | `—` | `—` |
| `carrier` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `note` | `lista de Note` | `não` | `não` | `0..*` | `—` | `—` |

## InstanceUpdate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `instance_of` | `LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `1; 1; 1` | `—` | `—` |
| `title` | `lista de Title / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `edition_statement` | `lista de LocalizedText / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `provision_activity` | `lista de Publication / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `identified_by` | `lista de Identifier / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `extent` | `lista de Extent / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `carrier` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `note` | `lista de Note / null` | `não` | `sim` | `0..*` | `null` | `—` |

## ItemCreate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `item_of` | `ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1` | `—` | `{"discriminator": {"mapping": {"external": "#/$defs/ExternalReference", "local": "#/$defs/LocalReference", "unreconciled": "#/$defs/UnreconciledReference"}, "propertyName": "kind"}}` |
| `identified_by` | `lista de Identifier` | `sim` | `não` | `1..*` | `—` | `—` |
| `held_by` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `note` | `lista de Note` | `não` | `não` | `0..*` | `—` | `—` |
| `custodial_history` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `shelf_mark` | `lista de ShelfMark` | `não` | `não` | `0..*` | `—` | `—` |
| `provenance` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |

## ItemRead

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `internal_id` | `string (uuid)` | `sim` | `não` | `1` | `—` | `—` |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `item_of` | `ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1` | `—` | `{"discriminator": {"mapping": {"external": "#/$defs/ExternalReference", "local": "#/$defs/LocalReference", "unreconciled": "#/$defs/UnreconciledReference"}, "propertyName": "kind"}}` |
| `identified_by` | `lista de Identifier` | `sim` | `não` | `1..*` | `—` | `—` |
| `held_by` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `note` | `lista de Note` | `não` | `não` | `0..*` | `—` | `—` |
| `custodial_history` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `shelf_mark` | `lista de ShelfMark` | `não` | `não` | `0..*` | `—` | `—` |
| `provenance` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |

## ItemUpdate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `item_of` | `LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `1; 1; 1` | `—` | `—` |
| `identified_by` | `lista de Identifier` | `não` | `não` | `1..*` | `—` | `—` |
| `held_by` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `note` | `lista de Note / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `custodial_history` | `lista de LocalizedText / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `shelf_mark` | `lista de ShelfMark / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `provenance` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |

## LiteralValue

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"literal"` | `sim` | `não` | `1` | `—` | `—` |
| `value` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `language` | `string / null` | `não` | `sim` | `1` | `null` | `{"pattern": "^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$"}` |
| `datatype` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |

## LocalConcept

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `vocabulary` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `label` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `alternative_labels` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `notation` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |
| `source` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |
| `status` | `["resolved", "unverified", "invalid", "deprecated", "unavailable"]` | `não` | `não` | `1` | `"unverified"` | `—` |
| `replacement` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |
| `kind` | `"local_concept"` | `sim` | `não` | `1` | `—` | `—` |
| `internal_id` | `string (uuid)` | `sim` | `não` | `1` | `—` | `—` |

## LocalReference

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"local"` | `não` | `não` | `1` | `"local"` | `—` |
| `entity_type` | `EntityType` | `sim` | `não` | `1` | `—` | `—` |
| `internal_id` | `string (uuid) / null` | `não` | `sim` | `1` | `null` | `—` |
| `uri` | `string / null` | `não` | `sim` | `1` | `null` | `{"minLength": 1}` |

## LocalizedText

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `value` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `language` | `string / null` | `não` | `sim` | `1` | `null` | `{"pattern": "^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$"}` |

## Note

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `label` | `lista de LocalizedText` | `sim` | `não` | `1..*` | `—` | `—` |
| `note_type` | `lista de string` | `não` | `não` | `0..*` | `—` | `—` |

## ProblemDetails

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `contract_version` | `"1.0"` | `não` | `não` | `1` | `"1.0"` | `—` |
| `type` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `title` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `status` | `integer` | `sim` | `não` | `1` | `—` | `{"maximum": 599, "minimum": 400}` |
| `detail` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `instance` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `code` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `request_id` | `string` | `sim` | `não` | `1` | `—` | `—` |
| `issues` | `lista de Diagnostic` | `não` | `não` | `0..*` | `[]` | `—` |
| `validation` | `CatalogValidationResult / null` | `não` | `sim` | `1` | `null` | `—` |

## Publication

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `agent` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `place` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `date` | `lista de PublicationDate` | `não` | `não` | `0..*` | `—` | `—` |

## PublicationDate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `value` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `datatype` | `["http://www.w3.org/2001/XMLSchema#string", "http://www.w3.org/2001/XMLSchema#gYear", "http://www.w3.org/2001/XMLSchema#date"]` | `não` | `não` | `1` | `"http://www.w3.org/2001/XMLSchema#string"` | `—` |

## PublicationLink

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"publication"` | `não` | `não` | `1` | `"publication"` | `—` |
| `source` | `LocalReference` | `sim` | `não` | `1` | `—` | `—` |
| `target` | `LocalReference / ExternalReference / UnreconciledReference` | `sim` | `não` | `1; 1; 1` | `—` | `—` |
| `predicate` | `"http://id.loc.gov/ontologies/bibframe/provisionActivity"` | `não` | `não` | `1` | `"http://id.loc.gov/ontologies/bibframe/provisionActivity"` | `—` |
| `activity_type` | `"Publication"` | `não` | `não` | `1` | `"Publication"` | `—` |
| `activity_key` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |

## RdfPath

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `["iri", "sequence", "alternative", "inverse", "zero_or_more", "one_or_more", "zero_or_one", "opaque"]` | `sim` | `não` | `1` | `—` | `—` |
| `iri` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `identifier` | `string / null` | `não` | `sim` | `1` | `null` | `—` |
| `items` | `lista de RdfPath` | `não` | `não` | `0..*` | `[]` | `—` |

## RelationshipCreate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `source` | `LocalReference` | `sim` | `não` | `1` | `—` | `—` |
| `links` | `lista de DirectLink / ContributionLink / PublicationLink` | `não` | `não` | `0..*` | `—` | `—` |

## RelationshipRead

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `source` | `LocalReference` | `sim` | `não` | `1` | `—` | `—` |
| `links` | `lista de DirectLink / ContributionLink / PublicationLink` | `não` | `não` | `0..*` | `—` | `—` |

## RelationshipReplace

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `source` | `LocalReference` | `sim` | `não` | `1` | `—` | `—` |
| `links` | `lista de DirectLink / ContributionLink / PublicationLink` | `não` | `não` | `0..*` | `—` | `—` |

## RelationshipUpdate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `operations` | `lista de AddLinks / RemoveLinks / ReplaceLinks` | `não` | `não` | `0..*` | `—` | `—` |

## RemoveLinks

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `op` | `"remove"` | `sim` | `não` | `1` | `—` | `—` |
| `links` | `lista de DirectLink / ContributionLink / PublicationLink` | `sim` | `não` | `1..*` | `—` | `—` |

## ReplaceLinks

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `op` | `"replace"` | `sim` | `não` | `1` | `—` | `—` |
| `predicate` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `links` | `lista de DirectLink / ContributionLink / PublicationLink` | `sim` | `não` | `0..*` | `—` | `—` |

## ResourceReference

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |

## ShelfMark

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `value` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `source` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |

## SubjectCreate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `preferred_label` | `lista de LocalizedText` | `sim` | `não` | `1..*` | `—` | `—` |
| `alternative_label` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `scheme` | `lista de ResourceReference` | `sim` | `não` | `1..*` | `—` | `—` |
| `broader` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `related` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `external_reference` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `provenance` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |

## SubjectRead

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `internal_id` | `string (uuid)` | `sim` | `não` | `1` | `—` | `—` |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `preferred_label` | `lista de LocalizedText` | `sim` | `não` | `1..*` | `—` | `—` |
| `alternative_label` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |
| `scheme` | `lista de ResourceReference` | `sim` | `não` | `1..*` | `—` | `—` |
| `broader` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `related` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `external_reference` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `provenance` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |

## SubjectUpdate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `preferred_label` | `lista de LocalizedText` | `não` | `não` | `1..*` | `—` | `—` |
| `alternative_label` | `lista de LocalizedText / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `scheme` | `lista de ResourceReference` | `não` | `não` | `1..*` | `—` | `—` |
| `broader` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `related` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `external_reference` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `provenance` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |

## Title

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `["Title", "VariantTitle"]` | `não` | `não` | `1` | `"Title"` | `—` |
| `main_title` | `lista de LocalizedText` | `sim` | `não` | `1..*` | `—` | `—` |
| `subtitle` | `lista de LocalizedText` | `não` | `não` | `0..*` | `—` | `—` |

## UnreconciledReference

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `kind` | `"unreconciled"` | `não` | `não` | `1` | `"unreconciled"` | `—` |
| `entity_type` | `EntityType` | `sim` | `não` | `1` | `—` | `—` |
| `label` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `namespace` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `key` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |

## WorkCreate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `title` | `lista de Title` | `sim` | `não` | `1..*` | `—` | `—` |
| `language` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `content` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `contribution` | `lista de Contribution` | `não` | `não` | `0..*` | `—` | `—` |
| `subject` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `classification` | `lista de Classification` | `não` | `não` | `0..*` | `—` | `—` |
| `related_to` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `translation_of` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `note` | `lista de Note` | `não` | `não` | `0..*` | `—` | `—` |

## WorkRead

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `internal_id` | `string (uuid)` | `sim` | `não` | `1` | `—` | `—` |
| `uri` | `string` | `sim` | `não` | `1` | `—` | `{"minLength": 1}` |
| `title` | `lista de Title` | `sim` | `não` | `1..*` | `—` | `—` |
| `language` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `content` | `lista de ResourceReference` | `não` | `não` | `0..*` | `—` | `—` |
| `contribution` | `lista de Contribution` | `não` | `não` | `0..*` | `—` | `—` |
| `subject` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `classification` | `lista de Classification` | `não` | `não` | `0..*` | `—` | `—` |
| `related_to` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `translation_of` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference` | `não` | `não` | `0..*` | `—` | `—` |
| `note` | `lista de Note` | `não` | `não` | `0..*` | `—` | `—` |

## WorkUpdate

Campos extras: rejeitados.

| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | Default no schema | Restrições locais do schema |
| --- | --- | --- | --- | --- | --- | --- |
| `title` | `lista de Title` | `não` | `não` | `1..*` | `—` | `—` |
| `language` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `content` | `lista de ResourceReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `contribution` | `lista de Contribution / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `subject` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `classification` | `lista de Classification / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `related_to` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `translation_of` | `lista de ResourceReference / LocalReference / ExternalReference / UnreconciledReference / null` | `não` | `sim` | `0..*` | `null` | `—` |
| `note` | `lista de Note / null` | `não` | `sim` | `0..*` | `null` | `—` |
