"""Editing JSON validators, independent of the domain revision token."""

import hashlib
import json
from typing import Annotated

from fastapi import Header, HTTPException, Request, Response

from libris.api.problems import validate_if_match
from libris.modules.bibliographic.application.catalog import CatalogView
from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError
from libris.modules.bibliographic.infrastructure.serialization.negotiation import (
    MEDIA_TYPES,
    NotAcceptable,
    RepresentationFormat,
    negotiate_format,
)
from libris.modules.bibliographic.infrastructure.serialization.representation import serialize_graph


def editing_etag(view: CatalogView) -> str:
    # Includes the exact typed projection and independent editorial generation.
    # A versioned namespace separates this validator from future exports/compositions.
    material = json.dumps(
        [
            "catalog-edit-json-v1",
            str(view.revision.identity.internal_id),
            view.revision.identity.uri,
            view.revision.profile,
            view.revision.number,
            view.editorial_version,
            view.resource.model_dump(mode="json"),
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return '"catalog-v1-' + hashlib.sha256(material).hexdigest() + '"'


def get_if_match(request: Request, if_match: Annotated[str | None, Header()] = None) -> str:
    if len(request.headers.getlist("if-match")) > 1:
        raise CatalogError(CatalogCode.MALFORMED_REQUEST, "If-Match duplicado.")
    return validate_if_match(if_match)


def set_representation_headers(response: Response, view: CatalogView) -> None:
    response.headers["ETag"] = editing_etag(view)


# Additional response media are declared on each negotiated GET in OpenAPI.
SEMANTIC_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {"content": {"application/ld+json": {}, "text/turtle": {}}},
    406: {"description": "No acceptable representation"},
}


def read_representation(
    request: Request, response: Response, view: CatalogView, *, public: bool = False
) -> Response:
    try:
        selected = negotiate_format(
            ",".join(request.headers.getlist("accept")) if "accept" in request.headers else None
        )
    except NotAcceptable as error:
        raise HTTPException(
            406, "Representação indisponível.", headers={"Vary": "Accept"}
        ) from error
    if selected == RepresentationFormat.JSON:
        content = view.resource.model_dump_json().encode("utf-8")
    else:
        if view.graph is None:
            raise RuntimeError("Authorized snapshot required for semantic representation")
        content = serialize_graph(
            view.graph,
            format="json-ld" if selected == RepresentationFormat.JSON_LD else "turtle",
            root=view.resource.uri,
        ).encode("utf-8")
    # Preserve the editing validator only for editorial JSON. Export validators
    # describe actual bytes/format; they cannot authorize PATCH with If-Match.
    etag = (
        editing_etag(view)
        if selected == RepresentationFormat.JSON and not public
        else (
            '"catalog-export-v1-'
            + hashlib.sha256(MEDIA_TYPES[selected].encode() + b"\x00" + content).hexdigest()
            + '"'
        )
    )
    headers = dict(response.headers)
    headers.pop("content-length", None)
    headers.pop("content-type", None)
    headers["etag"] = etag
    vary = [value.strip() for value in headers.get("vary", "").split(",") if value.strip()]
    if not any(value.lower() == "accept" for value in vary):
        vary.append("Accept")
    headers["vary"] = ", ".join(vary)
    return Response(content, media_type=MEDIA_TYPES[selected], headers=headers)
