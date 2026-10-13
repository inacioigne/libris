"""Gera o inventário documental v1; --check não escreve arquivos ou releases."""

import argparse
import json
from pathlib import Path

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from libris.api.problems import ProblemDetails
from libris.modules.bibliographic.api import schemas
from libris.modules.bibliographic.application.controlled_values import CatalogValueDocument
from libris.modules.bibliographic.application.diagnostics import CatalogValidationResult

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/architecture"
CONTRACT_ID = "urn:libris:contract:catalogographic:v1"
SPECIFICATION_VERSION = "1.0.0"


def public_models() -> tuple[type[BaseModel], ...]:
    return tuple(getattr(schemas, name) for name in schemas.__all__) + (
        CatalogValidationResult,
        CatalogValueDocument,
        ProblemDetails,
    )


def schema_artifact() -> dict[str, object]:
    roots, bundle = models_json_schema([(model, "validation") for model in public_models()])
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": CONTRACT_ID + ":" + SPECIFICATION_VERSION,
        **bundle,
        "x-libris-contract": CONTRACT_ID,
        "x-libris-specification-version": SPECIFICATION_VERSION,
        "x-libris-publication": "documental; sem endpoints catalográficos",
        "x-libris-roots": {model.__name__: roots[model, "validation"] for model in public_models()},
    }


def object_schema(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("Schema esperado como objeto.")
    return value


def alternatives(schema: dict[str, object]) -> list[dict[str, object]]:
    branches = schema.get("anyOf", schema.get("oneOf"))
    return (
        [object_schema(branch) for branch in branches] if isinstance(branches, list) else [schema]
    )


def type_label(schema: dict[str, object]) -> str:
    branches = alternatives(schema)
    if branches != [schema]:
        return " / ".join(type_label(branch) for branch in branches)
    if "$ref" in schema:
        return str(schema["$ref"]).rsplit("/", 1)[-1]
    if schema.get("type") == "array":
        return "lista de " + type_label(object_schema(schema["items"]))
    if "const" in schema:
        return json.dumps(schema["const"], ensure_ascii=False)
    if "enum" in schema:
        return json.dumps(schema["enum"], ensure_ascii=False)
    return str(schema.get("type", "objeto")) + (
        f" ({schema['format']})" if "format" in schema else ""
    )


def inventory(artifact: dict[str, object]) -> str:
    definitions = object_schema(artifact["$defs"])
    lines = [
        "# Inventário de campos do contrato catalográfico v1",
        "",
        f"Identificador `{CONTRACT_ID}`; especificação documental **{SPECIFICATION_VERSION}**.",
        "Gerado por `scripts/generate_catalogographic_contract.py`; não editar as tabelas.",
        "[Referência canônica](catalogographic-contract.md) e "
        "[JSON Schema completo](catalogographic-contract-v1.schema.json).",
        "",
        "As 22 raízes são os quinze DTOs de entidades, quatro de relacionamentos,",
        "CatalogValidationResult, CatalogValueDocument e ProblemDetails. As demais",
        "definições são estruturas alcançáveis, não novos recursos ou endpoints.",
        "Perfis/configurações têm inventário e schemas próprios em "
        "[perfis](catalog-profiles.md), [SHACL](shacl-inventory.md) e "
        "[vocabulários](controlled-vocabularies.md).",
        "",
        "Obrigatório significa presença no JSON de entrada. Cardinalidade conta elementos",
        "de uma lista **quando fornecida**, ou um valor escalar; não soma triplas RDF.",
        "Update permite omissão mesmo de propriedades obrigatórias do estado final.",
        "`—` significa ausência de default anunciado pelo schema; listas com factory",
        "têm default runtime `[]`, mesmo quando o schema não o anuncia. Em Update,",
        "`None` interno é sentinela de omissão: campos obrigatórios não aceitam null.",
        "Null permitido no schema não implica presença de tripla ou remoção em todo contrato.",
        "",
        "Este schema é de **validação**. JSON Schema não expressa todos os validadores",
        "Pydantic (IRI, coerência UUID/URI, mínimo Title/Local, idioma único, disjunção,",
        "datas e estado do relatório). Ver "
        "[invariantes e serialização](catalogographic-schemas.md).",
        "Valores de enum por referência constam na definição correspondente.",
    ]
    for name, raw in sorted(definitions.items()):
        schema = object_schema(raw)
        lines.extend(["", f"## {name}", ""])
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            lines.append("Valores: `" + type_label(schema) + "`.")
            continue
        lines.extend(
            [
                "Campos extras: "
                + (
                    "rejeitados."
                    if schema.get("additionalProperties") is False
                    else "conforme schema."
                ),
                "",
                "| Campo | Tipo / estrutura | Obrigatório | Null | Cardinalidade fornecida | "
                "Default no schema | Restrições locais do schema |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise TypeError("required esperado como lista.")
        for field, raw_property in properties.items():
            prop = object_schema(raw_property)
            branches = alternatives(prop)
            nullable = any(branch.get("type") == "null" for branch in branches)
            concrete = [branch for branch in branches if branch.get("type") != "null"]
            cardinality = "; ".join(
                f"{branch.get('minItems', 0)}..{branch.get('maxItems', '*')}"
                if branch.get("type") == "array"
                else "1"
                for branch in concrete
            )
            constraints = {
                key: value
                for branch in concrete
                for key, value in branch.items()
                if key
                in {"minLength", "maxLength", "pattern", "minimum", "maximum", "discriminator"}
            }
            default = json.dumps(prop["default"], ensure_ascii=False) if "default" in prop else "—"
            cells = [
                field,
                type_label(prop),
                "sim" if field in required else "não",
                "sim" if nullable else "não",
                cardinality,
                default,
                json.dumps(constraints, ensure_ascii=False) if constraints else "—",
            ]
            lines.append(
                "| " + " | ".join("`" + cell.replace("|", "&#124;") + "`" for cell in cells) + " |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    schema = schema_artifact()
    artifacts = {
        OUTPUT / "catalogographic-contract-v1.schema.json": json.dumps(
            schema, ensure_ascii=False, sort_keys=True, indent=2
        )
        + "\n",
        OUTPUT / "catalogographic-contract-field-inventory.md": inventory(schema),
    }
    for path, content in artifacts.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Inventário divergente: {path.relative_to(ROOT)}")
        else:
            if path.exists() and path.read_text(encoding="utf-8") != content:
                raise SystemExit("Baseline existente divergente: criar nova versão após revisão.")
            path.write_text(content, encoding="utf-8")
    print(f"{len(artifacts)} artefatos {'verificados' if args.check else 'gerados'}.")


if __name__ == "__main__":
    main()
