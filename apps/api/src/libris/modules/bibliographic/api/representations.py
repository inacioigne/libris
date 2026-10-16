"""Editing JSON validators, independent of the domain revision token."""

import hashlib
import json
from typing import Annotated

from fastapi import Header, Request, Response

from libris.api.problems import validate_if_match
from libris.modules.bibliographic.application.catalog import CatalogView
from libris.modules.bibliographic.domain.errors import CatalogCode, CatalogError


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


def get_if_match(
    request: Request, if_match: Annotated[str | None, Header()] = None
) -> str:
    if len(request.headers.getlist("if-match")) > 1:
        raise CatalogError(CatalogCode.MALFORMED_REQUEST, "If-Match duplicado.")
    return validate_if_match(if_match)


def set_representation_headers(response: Response, view: CatalogView) -> None:
    response.headers["ETag"] = editing_etag(view)
