from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, model_validator

from app.modules.bibliograph.application.cataloging_profiles import (
    get_default_work_profile,
)
from app.modules.bibliograph.application.vocabularies import get_vocabulary

DraftFieldValue: TypeAlias = str | list[str]


class DraftCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    profileId: str
    profileVersion: str
    values: dict[str, DraftFieldValue]

    @model_validator(mode="after")
    def validate_against_profile(self) -> "DraftCreate":
        profile = get_default_work_profile()
        if self.profileId != profile.id or self.profileVersion != profile.version:
            raise ValueError("Perfil de catalogação desconhecido ou com versão inválida.")

        fields = {
            field.id: field
            for section in profile.sections
            for field in section.fields
        }
        for field_id, value in self.values.items():
            field = fields.get(field_id)
            if field is None:
                raise ValueError(f"Campo de catalogação desconhecido: {field_id}.")
            if field.widget == "text":
                if not isinstance(value, str):
                    raise ValueError(f"O campo {field_id} deve ser textual.")
            elif field.widget == "vocabulary-select":
                if not isinstance(value, list) or not all(
                    isinstance(item, str) for item in value
                ):
                    raise ValueError(f"O campo {field_id} deve ser uma lista de URIs.")
                if not field.repeatable and len(value) > 1:
                    raise ValueError(f"O campo {field_id} aceita somente um valor.")
                allowed = {
                    str(term.uri)
                    for term in get_vocabulary(field.vocabulary or "").terms
                }
                if any(uri not in allowed for uri in value):
                    raise ValueError(
                        f"O campo {field_id} contém uma URI fora do vocabulário."
                    )
            else:
                raise ValueError(f"Widget não suportado para o campo {field_id}.")
        return self


class DraftReceived(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
