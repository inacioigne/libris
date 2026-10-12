"""Transport-neutral public contracts. No RDF, ORM or HTTP objects in payloads."""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError

Category = Literal["schema", "semantic", "profile", "identity", "reference", "state", "technical"]
Severity = Literal["Violation", "Warning", "Info"]


class PublicContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    def public_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json", exclude_none=True)

    def public_json(self) -> str:
        return json.dumps(
            self.public_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )


class RdfPath(PublicContract):
    kind: Literal[
        "iri",
        "sequence",
        "alternative",
        "inverse",
        "zero_or_more",
        "one_or_more",
        "zero_or_one",
        "opaque",
    ]
    iri: str | None = None
    identifier: str | None = None
    items: tuple["RdfPath", ...] = ()


class Diagnostic(PublicContract):
    code: CatalogCode
    message: str
    category: Category
    severity: Severity = "Violation"
    field_ids: tuple[str, ...] = ()
    path: RdfPath | None = None
    focus_node: str | None = None
    value: str | None = None
    constraint: str | None = None
    source_shape: str | None = None
    messages: tuple[str, ...] = ()
    # Only curated identifiers/counts; never exception contexts or submitted values.
    parameters: dict[str, str | int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def canonical_fields(self) -> "Diagnostic":
        object.__setattr__(self, "field_ids", tuple(sorted(set(self.field_ids))))
        object.__setattr__(self, "messages", tuple(sorted(set(self.messages))))
        return self


def ordered(issues: tuple[Diagnostic, ...]) -> tuple[Diagnostic, ...]:
    ranks = {"Violation": 0, "Warning": 1, "Info": 2}
    return tuple(sorted(issues, key=lambda issue: (ranks[issue.severity], issue.public_json())))


class CatalogValidationResult(PublicContract):
    contract_version: Literal["1.0"] = "1.0"
    state: Literal["completed", "failed"]
    conforms: bool | None = None
    profile_id: str
    profile_release: str
    profile_version: str
    context: Literal["snapshot", "composed"]
    request_id: str | None = None
    issues: tuple[Diagnostic, ...] = ()

    @model_validator(mode="after")
    def consistency(self) -> "CatalogValidationResult":
        if self.state == "failed":
            if self.conforms is not None:
                raise ValueError("Falha técnica não pode afirmar conformidade.")
            if not self.issues or any(issue.category != "technical" for issue in self.issues):
                raise ValueError("Falha técnica exige diagnóstico técnico.")
        else:
            if self.conforms is None:
                raise ValueError("Validação executada exige conformidade explícita.")
            if any(issue.category == "technical" for issue in self.issues):
                raise ValueError("Falha técnica não é resultado de conformidade.")
            if self.conforms and any(issue.severity == "Violation" for issue in self.issues):
                raise ValueError("Violation bloqueia conformidade.")
        object.__setattr__(self, "issues", ordered(self.issues))
        return self


class CatalogValidationRejected(CatalogError):
    def __init__(self, result: CatalogValidationResult) -> None:
        if result.state != "completed" or result.conforms is not False:
            raise ValueError("Somente validação executada não conforme pode rejeitar dados.")
        super().__init__(CatalogCode.VALIDATION_REJECTED, "Grafo não conforme ao perfil.")
        self.result = result
