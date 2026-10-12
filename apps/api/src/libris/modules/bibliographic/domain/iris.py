"""Absolute IRI validation without normalization or network access."""

import re
from urllib.parse import urlsplit

from .profiles import absolute_iri


def validate_iri(value: str) -> str:
    absolute_iri(value)
    if re.search(r'[\x00-\x20<>"{}|\\^`\x7f]', value):
        raise ValueError("A IRI contém caracteres inválidos.")
    if re.search(r"%(?![0-9a-fA-F]{2})", value):
        raise ValueError("Escape percentual inválido na IRI.")
    parts = urlsplit(value)
    if parts.scheme in {"http", "https"}:
        if not parts.hostname:
            raise ValueError("A IRI HTTP(S) exige um host.")
        # Accessing port checks its numeric form and range without rewriting the IRI.
        _ = parts.port
    if not value.partition(":")[2]:
        raise ValueError("A IRI exige uma parte específica do esquema.")
    return value
