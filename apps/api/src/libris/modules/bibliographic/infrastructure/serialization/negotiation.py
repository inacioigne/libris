"""Deterministic Accept negotiation without an HTTP framework dependency."""

import re
from dataclasses import dataclass
from enum import StrEnum


class RepresentationFormat(StrEnum):
    JSON = "json"
    JSON_LD = "json-ld"
    TURTLE = "turtle"


MEDIA_TYPES = {
    RepresentationFormat.JSON: "application/json",
    RepresentationFormat.JSON_LD: "application/ld+json",
    RepresentationFormat.TURTLE: "text/turtle",
}


class NotAcceptable(ValueError):
    """The future HTTP adapter must return 406, including for malformed Accept."""


@dataclass(frozen=True)
class _Range:
    major: str
    minor: str
    quality: int
    parameters: tuple[tuple[str, str], ...]

    def matches(self, media_type: str) -> bool:
        major, minor = media_type.split("/")
        # No media parameters are offered by this contract's representations.
        return not self.parameters and self.major in ("*", major) and self.minor in ("*", minor)

    @property
    def specificity(self) -> int:
        return int(self.major != "*") + int(self.minor != "*")


_TOKEN = r"[!#$%&'*+.^_`|~0-9a-z-]+"
_MEDIA = re.compile(rf"({_TOKEN})/({_TOKEN})", re.IGNORECASE)
_PARAMETER = re.compile(rf'({_TOKEN})=({_TOKEN}|"[^"\\\r\n]*")', re.IGNORECASE)
_QUALITY = re.compile(r"(?:0(?:\.[0-9]{0,3})?|1(?:\.0{0,3})?)")


def _split(value: str, delimiter: str) -> list[str]:
    """Honor quoted delimiters; reject escapes/control characters in this subset."""
    if re.search(r"[\x00-\x08\x0a-\x1f\x7f\\]", value):
        raise NotAcceptable("Accept contém caracteres inválidos.")
    parts: list[str] = []
    start, quoted = 0, False
    for index, character in enumerate(value):
        if character == '"':
            quoted = not quoted
        elif character == delimiter and not quoted:
            parts.append(value[start:index].strip())
            start = index + 1
    if quoted:
        raise NotAcceptable("Parâmetro Accept sem fechamento.")
    parts.append(value[start:].strip())
    return parts


def negotiate_format(
    accept: str | None,
    *,
    available: tuple[RepresentationFormat, ...] = tuple(RepresentationFormat),
    default: RepresentationFormat = RepresentationFormat.JSON,
) -> RepresentationFormat:
    """Specific q=0 overrides wildcards; ties follow server order in available."""
    if not available or len(set(available)) != len(available) or default not in available:
        raise ValueError("Representações/default incompatíveis.")
    if accept is None:
        return default
    available = (default, *(format for format in available if format != default))
    ranges: list[_Range] = []
    for part in _split(accept, ","):
        if not part:  # RFC list syntax permits empty members, but an empty list rejects all.
            continue
        media, *parameters = _split(part, ";")
        match = _MEDIA.fullmatch(media)
        if match is None:
            raise NotAcceptable("Tipo de mídia Accept inválido.")
        major, minor = (value.lower() for value in match.groups())
        if major == "*" and minor != "*":
            raise NotAcceptable("Curinga Accept inválido.")
        quality = 1000
        media_parameters: list[tuple[str, str]] = []
        names: set[str] = set()
        for parameter in parameters:
            parsed = _PARAMETER.fullmatch(parameter)
            if parsed is None:
                raise NotAcceptable("Parâmetro Accept inválido.")
            name, value = parsed.groups()
            name = name.lower()
            if name in names:
                raise NotAcceptable("Parâmetro Accept duplicado.")
            names.add(name)
            if name == "q":
                if _QUALITY.fullmatch(value) is None:
                    raise NotAcceptable("Qualidade Accept inválida.")
                quality = round(float(value) * 1000)
            else:
                media_parameters.append((name, value.strip('"')))
        ranges.append(_Range(major, minor, quality, tuple(media_parameters)))
    candidates: list[tuple[int, int, int, RepresentationFormat]] = []
    for index, format in enumerate(available):
        matching = [entry for entry in ranges if entry.matches(MEDIA_TYPES[format])]
        if matching:
            specificity = max(entry.specificity for entry in matching)
            # Duplicate equally specific ranges: conservative q=0 wins.
            quality = min(entry.quality for entry in matching if entry.specificity == specificity)
            if quality:
                candidates.append((quality, specificity, -index, format))
    if not candidates:
        raise NotAcceptable("Nenhuma representação disponível é aceitável.")
    return max(candidates)[3]
