"""RFC 9457 adapters; known rejections only, unexpected failures remain HTTP 500."""

import logging
import re
import traceback
from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import Field, ValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from libris.core.correlation import request_id_context
from libris.modules.bibliographic.application.diagnostics import (
    CatalogValidationRejected,
    CatalogValidationResult,
    Diagnostic,
    PublicContract,
    ordered,
)
from libris.modules.bibliographic.application.editorial import CatalogPublicationRejected
from libris.modules.bibliographic.domain.errors import (
    CatalogCode,
    CatalogError,
    ResourceNotFoundError,
)
from libris.modules.bibliographic.domain.models import StaleRevisionError
from libris.modules.bibliographic.domain.profile_registry import ProfileError
from libris.modules.bibliographic.infrastructure.rdf import RdfDocumentError
from libris.modules.bibliographic.infrastructure.validation import ShaclValidationError
from libris.modules.identity.domain.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class ProblemDetails(PublicContract):
    contract_version: Literal["1.0"] = "1.0"
    type: str
    title: str
    status: int = Field(ge=400, le=599)
    detail: str | None = None
    instance: str | None = None
    code: str
    request_id: str
    issues: tuple[Diagnostic, ...] = ()
    validation: CatalogValidationResult | None = None


CODE_STATUS = {
    CatalogCode.MALFORMED_REQUEST: 400,
    CatalogCode.PROFILE_UNKNOWN: 404,
    CatalogCode.RESOURCE_UNKNOWN: 404,
    CatalogCode.CONFLICT: 409,
    CatalogCode.EDITORIAL_VERSION_STALE: 412,
    CatalogCode.TRANSITION_FORBIDDEN: 409,
    CatalogCode.EDITORIAL_STATE_INVALID: 409,
    CatalogCode.REVISION_STALE: 412,
    CatalogCode.PRECONDITION_REQUIRED: 428,
    CatalogCode.VALIDATOR_FAILURE: 500,
    CatalogCode.INTERNAL: 500,
    CatalogCode.INFRASTRUCTURE_UNAVAILABLE: 503,
    CatalogCode.PROFILE_UNAVAILABLE: 503,
}
PROFILE_CODES = {
    "unknown_profile": CatalogCode.PROFILE_UNKNOWN,
    "unknown_release": CatalogCode.PROFILE_UNKNOWN,
    "no_profile": CatalogCode.PROFILE_UNAVAILABLE,
    "profile_unavailable": CatalogCode.PROFILE_UNAVAILABLE,
    "inapplicable_profile": CatalogCode.PROFILE_INCOMPATIBLE,
    "validation_release_mismatch": CatalogCode.PROFILE_INCOMPATIBLE,
    "incompatible_shapes": CatalogCode.PROFILE_INCOMPATIBLE,
    "contradictory_shapes": CatalogCode.PROFILE_INCOMPATIBLE,
    "unknown_shapes": CatalogCode.VALIDATOR_FAILURE,
    "missing_shapes": CatalogCode.VALIDATOR_FAILURE,
    "missing_release": CatalogCode.VALIDATOR_FAILURE,
    "immutable_release": CatalogCode.CONFLICT,
    "immutable_dependency": CatalogCode.CONFLICT,
    "identity_change": CatalogCode.CONFLICT,
    "duplicate_release": CatalogCode.CONFLICT,
}
SAFE_DETAILS: dict[str, str] = {
    CatalogCode.MALFORMED_REQUEST: "Solicitação malformada.",
    CatalogCode.SCHEMA_INVALID: "Dados estruturalmente inválidos.",
    CatalogCode.PROFILE_UNKNOWN: "Perfil ou release inexistente.",
    CatalogCode.PROFILE_INCOMPATIBLE: "Perfil incompatível com a solicitação.",
    CatalogCode.PROFILE_UNAVAILABLE: "Perfil indisponível para esta operação.",
    CatalogCode.RESOURCE_UNKNOWN: "Recurso ou revisão inexistente.",
    CatalogCode.CONFLICT: "Conflito de estado ou integridade.",
    CatalogCode.REVISION_STALE: "Precondição obsoleta; recarregue a representação.",
    CatalogCode.PRECONDITION_REQUIRED: "If-Match é obrigatório para esta operação.",
    CatalogCode.VALIDATION_REJECTED: "Dados não conformes ao perfil catalográfico.",
    CatalogCode.VALIDATOR_FAILURE: "Falha técnica na validação.",
    CatalogCode.INFRASTRUCTURE_UNAVAILABLE: "Dependência temporariamente indisponível.",
    CatalogCode.INTERNAL: "Falha interna inesperada.",
}


class RequestCorrelationMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        identifiers = [
            value for key, value in scope.get("headers", []) if key.lower() == b"x-request-id"
        ]
        supplied = identifiers[0] if len(identifiers) == 1 else b""
        try:
            if len(supplied) != 36:
                raise ValueError("Noncanonical correlation")
            decoded = supplied.decode("ascii")
            identifier = str(UUID(decoded))
            if identifier != decoded:
                raise ValueError("Noncanonical correlation")
        except (ValueError, UnicodeDecodeError):
            identifier = str(uuid4())
        scope.setdefault("state", {})["request_id"] = identifier
        token = request_id_context.set(identifier)

        async def correlated_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != b"x-request-id"
                ]
                message["headers"] = [*headers, (b"x-request-id", identifier.encode("ascii"))]
            await send(message)

        try:
            await self.app(scope, receive, correlated_send)
        finally:
            request_id_context.reset(token)


def validate_if_match(value: str | None) -> str:
    """Accept exactly one strong validator; lists, weak tags and wildcard are invalid."""
    if value is None:
        raise CatalogError(CatalogCode.PRECONDITION_REQUIRED, "If-Match obrigatório.")
    if re.fullmatch(r'"[\x21\x23-\x7e\x80-\xff]*"', value) is None:
        raise CatalogError(CatalogCode.MALFORMED_REQUEST, "If-Match incompatível.")
    return value


def require_if_match(value: str | None, *, current_etag: str) -> None:
    """Compare the editing representation validator; persistent CAS decides the write."""
    try:
        validate_if_match(current_etag)
    except CatalogError as error:
        raise RuntimeError("A representação deve fornecer um ETag forte válido.") from error
    if validate_if_match(value) != current_etag:
        raise StaleRevisionError("Precondição obsoleta.")


def schema_diagnostics(errors: Sequence[Mapping[str, object]]) -> tuple[Diagnostic, ...]:
    result: list[Diagnostic] = []
    for error in errors:
        kind = error.get("type")
        code = {
            "missing": CatalogCode.REQUIRED,
            "too_short": CatalogCode.CARDINALITY,
            "too_long": CatalogCode.CARDINALITY,
            "string_type": CatalogCode.VALUE,
            "int_type": CatalogCode.VALUE,
            "literal_error": CatalogCode.VALUE,
            "enum": CatalogCode.VALUE,
        }.get(str(kind), CatalogCode.SCHEMA_INVALID)
        location = error.get("loc")
        parts = list(location) if isinstance(location, (tuple, list)) else []
        if parts and parts[0] in {"body", "query", "path", "header"}:
            parts.pop(0)
        # Extras and mapping keys can be submitted secrets; never echo their locations.
        fields: tuple[str, ...] = ()
        if (
            kind != "extra_forbidden"
            and parts
            and all(
                isinstance(part, int)
                or (isinstance(part, str) and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]{0,63}", part))
                for part in parts
            )
        ):
            fields = ("/" + "/".join(str(part) for part in parts),)
        result.append(
            Diagnostic(
                code=code,
                message="Campo obrigatório ausente."
                if code == CatalogCode.REQUIRED
                else "Estrutura ou valor incompatível.",
                category="schema",
                field_ids=fields,
            )
        )
    return ordered(tuple(result))


def adapt_pydantic_error(error: ValidationError) -> tuple[Diagnostic, ...]:
    return schema_diagnostics(
        error.errors(include_input=False, include_context=False, include_url=False)
    )


def classify(error: Exception) -> tuple[int, str]:
    if isinstance(error, ValidationError):
        return 422, CatalogCode.SCHEMA_INVALID.value
    if isinstance(error, PermissionDenied):
        return 403, "authorization.denied"
    if isinstance(error, CatalogError):
        return CODE_STATUS.get(error.code, 422), error.code.value
    if isinstance(error, StaleRevisionError):
        return 412, CatalogCode.REVISION_STALE.value
    if isinstance(error, ResourceNotFoundError):
        return 404, CatalogCode.RESOURCE_UNKNOWN.value
    if isinstance(error, ProfileError):
        code = PROFILE_CODES.get(error.code, CatalogCode.PROFILE_POLICY)
        return CODE_STATUS.get(code, 422), code.value
    if isinstance(error, ShaclValidationError):
        code = (
            CatalogCode.INFRASTRUCTURE_UNAVAILABLE
            if error.code == "shapes_unavailable"
            else CatalogCode.VALIDATOR_FAILURE
        )
        return CODE_STATUS[code], code.value
    if isinstance(error, RdfDocumentError):
        return 400, CatalogCode.MALFORMED_REQUEST.value
    if isinstance(error, (ConnectionError, TimeoutError)):
        return 503, CatalogCode.INFRASTRUCTURE_UNAVAILABLE.value
    if isinstance(error, DBAPIError):
        sqlstate = getattr(error.orig, "sqlstate", None)
        if isinstance(error, IntegrityError) and sqlstate in {"23503", "23505"}:
            return 409, CatalogCode.CONFLICT.value
        if error.connection_invalidated or (
            isinstance(sqlstate, str)
            and (sqlstate.startswith("08") or sqlstate in {"57P01", "57P02", "57P03", "53300"})
        ):
            return 503, CatalogCode.INFRASTRUCTURE_UNAVAILABLE.value
    if isinstance(error, HTTPException):
        http_code = {
            400: "request.malformed",
            404: "resource.unknown",
            409: "state.conflict",
            412: "revision.stale",
            422: "schema.invalid",
            428: "revision.precondition_required",
            500: "internal.failure",
            503: "infrastructure.unavailable",
            401: "authentication.required",
            403: "authorization.denied",
        }.get(error.status_code, f"http.{error.status_code}")
        return error.status_code, http_code
    return 500, CatalogCode.INTERNAL.value


def log_failure(error: Exception, identifier: str) -> None:
    # Keep execution sites internally, without exception text, SQL, inputs or locals.
    sites = [
        (frame.filename, frame.lineno, frame.name)
        for frame in traceback.extract_tb(error.__traceback__)
    ]
    logger.error(
        "request_id=%s exception_type=%s sites=%s", identifier, type(error).__name__, sites
    )


def problem_response(
    request: Request,
    status: int,
    code: str,
    *,
    issues: tuple[Diagnostic, ...] = (),
    validation: CatalogValidationResult | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    identifier: str = request.state.request_id
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = "HTTP error"
    problem = ProblemDetails(
        type=f"urn:libris:problem:v1:{code}",
        title=title,
        status=status,
        detail=SAFE_DETAILS.get(code, "Operação rejeitada."),
        instance=f"urn:uuid:{identifier}",
        code=code,
        request_id=identifier,
        issues=issues,
        validation=validation,
    )
    return JSONResponse(
        status_code=status,
        content=problem.public_dict(),
        media_type="application/problem+json",
        headers={**(headers or {}), "X-Request-ID": identifier},
    )


async def handle_exception(request: Request, error: Exception) -> JSONResponse:
    status, code = classify(error)
    if status >= 500:
        log_failure(error, request.state.request_id)
    if isinstance(error, ValidationError):
        return problem_response(
            request, 422, CatalogCode.SCHEMA_INVALID, issues=adapt_pydantic_error(error)
        )
    result = (
        error.result
        if isinstance(error, (CatalogValidationRejected, CatalogPublicationRejected))
        else None
    )
    if result is not None:
        result = result.model_copy(update={"request_id": request.state.request_id})
    return problem_response(
        request,
        status,
        code,
        validation=result,
        issues=result.issues if result else (),
        headers=error.headers if isinstance(error, HTTPException) else None,
    )


async def handle_request_validation(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    errors = error.errors()
    malformed = any(item["type"] == "json_invalid" for item in errors)
    return problem_response(
        request,
        400 if malformed else 422,
        CatalogCode.MALFORMED_REQUEST if malformed else CatalogCode.SCHEMA_INVALID,
        issues=schema_diagnostics(errors),
    )


def install_problem_handlers(app: FastAPI, *, correlation: bool = True) -> None:
    if correlation:
        app.add_middleware(RequestCorrelationMiddleware)
    for exception in (
        CatalogError,
        ValidationError,
        PermissionDenied,
        StaleRevisionError,
        ResourceNotFoundError,
        ProfileError,
        ShaclValidationError,
        RdfDocumentError,
        DBAPIError,
        ConnectionError,
        TimeoutError,
        HTTPException,
        Exception,
    ):
        app.add_exception_handler(exception, handle_exception)
    app.add_exception_handler(RequestValidationError, handle_request_validation)

    def openapi() -> dict[str, object]:
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        for model in (ProblemDetails, CatalogValidationResult):
            definition = model.model_json_schema(ref_template="#/components/schemas/{model}")
            components.update(definition.pop("$defs", {}))
            components[model.__name__] = definition
        # Global handlers apply to every route, including authentication and body parsing.
        for path_name, path in schema["paths"].items():
            for method, operation in path.items():
                if not isinstance(operation, dict) or "responses" not in operation:
                    continue
                for status in (400, 404, 409, 412, 422, 428, 500, 503):
                    operation["responses"][str(status)] = {
                        "description": HTTPStatus(status).phrase,
                        "content": {
                            "application/problem+json": {
                                "schema": {"$ref": "#/components/schemas/ProblemDetails"}
                            }
                        },
                    }
                for parameter in operation.get("parameters", []):
                    if parameter.get("in") == "header" and parameter["name"] == "if-match":
                        parameter["required"] = True
                        parameter["description"] = (
                            "Um único ETag forte da representação editorial correspondente. "
                            "Ausência: 428; sintaxe inválida: 400; obsoleto: 412."
                        )
                        parameter["schema"] = {"type": "string", "title": "If-Match"}
                for response_status, response in operation["responses"].items():
                    headers = response.setdefault("headers", {})
                    headers["X-Request-ID"] = {
                        "description": "Identificador de correlação da requisição.",
                        "schema": {"type": "string", "format": "uuid"},
                    }
                    if response_status == "401":
                        headers["WWW-Authenticate"] = {
                            "schema": {"type": "string", "const": "Bearer"}
                        }
                    success = response_status.isdigit() and int(response_status) < 300
                    negotiated = "406" in operation["responses"]
                    catalog = path_name.startswith("/api/v1/catalog/")
                    resource_write = catalog and (
                        method == "patch" or (
                            method == "post" and path_name.rsplit("/", 1)[-1]
                            in {"works", "instances", "items", "agents", "subjects"}
                        )
                    )
                    state = path_name.endswith("/editorial") or "/editorial/" in path_name
                    relations = path_name.endswith("/relationships")
                    if success and (negotiated or resource_write or state or relations):
                        headers["ETag"] = {
                            "description": (
                                "Validador forte; somente JSON editorial autoriza edição. "
                                "Relações usam seu próprio ETag; público/RDF são exportações."
                            ),
                            "schema": {"type": "string"},
                        }
                    if negotiated and (success or response_status == "406"):
                        headers["Vary"] = {
                            "description": "Inclui Accept; CORS pode acrescentar Origin.",
                            "schema": {"type": "string"},
                        }
                    if success and resource_write and method == "post":
                        headers["Location"] = {
                            "description": "Caminho relativo do recurso criado.",
                            "schema": {"type": "string"},
                        }
                    if response_status.isdigit() and int(response_status) >= 400:
                        response["content"] = {
                            "application/problem+json": {
                                "schema": {"$ref": "#/components/schemas/ProblemDetails"}
                            }
                        }
        app.openapi_schema = schema
        return schema

    app.openapi = openapi  # type: ignore[method-assign]  # FastAPI custom OpenAPI hook.
