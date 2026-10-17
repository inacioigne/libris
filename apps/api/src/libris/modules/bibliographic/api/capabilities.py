"""Transporte HTTP das capacidades catalográficas M05.04."""

import hashlib
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from libris.api.problems import require_if_match
from libris.modules.bibliographic.api.dependencies import (
    get_catalog_service,
    get_resource_base_uri,
)
from libris.modules.bibliographic.api.limits import BoundedCatalogRoute
from libris.modules.bibliographic.api.representations import editing_etag, get_if_match
from libris.modules.bibliographic.api.schemas import (
    AgentCreate,
    AgentRead,
    InstanceCreate,
    InstanceRead,
    ItemCreate,
    ItemRead,
    SubjectCreate,
    SubjectRead,
    WorkCreate,
    WorkRead,
)
from libris.modules.bibliographic.api.schemas.relationships import (
    RelationshipRead,
    RelationshipUpdate,
)
from libris.modules.bibliographic.api.schemas.validation import ValidationRequest
from libris.modules.bibliographic.application.catalog import CatalogService
from libris.modules.bibliographic.application.catalog_profiles import (
    ProfileReleaseRead,
    public_profile,
    public_profiles,
)
from libris.modules.bibliographic.application.catalog_relationships import (
    RelationshipService,
    RelationshipView,
)
from libris.modules.bibliographic.application.catalog_validation import (
    prevalidate,
    require_profile_read,
)
from libris.modules.bibliographic.application.diagnostics import CatalogValidationResult
from libris.modules.bibliographic.domain.relationships import EntityType
from libris.modules.bibliographic.infrastructure.serialization import ResourceCreate, ResourceRead
from libris.modules.bibliographic.infrastructure.validation import (
    AUTHORITY_PROFILE_ID,
    INSTITUTIONAL_PROFILE_ID,
)
from libris.modules.identity.api.dependencies import get_execution_context
from libris.modules.identity.application.authorization import HumanContext

router = APIRouter(route_class=BoundedCatalogRoute)
Context = Annotated[HumanContext, Depends(get_execution_context)]
Service = Annotated[CatalogService, Depends(get_catalog_service)]
Collection = Literal["works", "instances", "items", "agents", "subjects"]
COLLECTIONS: dict[str, tuple[EntityType, type[ResourceCreate], type[ResourceRead]]] = {
    "works": (EntityType.WORK, WorkCreate, WorkRead),
    "instances": (EntityType.INSTANCE, InstanceCreate, InstanceRead),
    "items": (EntityType.ITEM, ItemCreate, ItemRead),
    "agents": (EntityType.AGENT, AgentCreate, AgentRead),
    "subjects": (EntityType.SUBJECT, SubjectCreate, SubjectRead),
}


def profile_for(collection: Collection) -> str:
    return (
        AUTHORITY_PROFILE_ID if collection in {"agents", "subjects"} else INSTITUTIONAL_PROFILE_ID
    )


def get_relationship_service(service: Service) -> RelationshipService:
    return RelationshipService(service.sessions, authorization=service.authorization)


Relations = Annotated[RelationshipService, Depends(get_relationship_service)]


def relationship_etag(view: RelationshipView) -> str:
    material = editing_etag(view.catalog) + view.relationships.model_dump_json()
    return '"catalog-relationships-v1-' + hashlib.sha256(material.encode()).hexdigest() + '"'


@router.get("/profiles", response_model=list[ProfileReleaseRead])
def profiles(service: Service, context: Context) -> list[ProfileReleaseRead]:
    require_profile_read(service, context)
    return public_profiles()


@router.get("/profiles/release", response_model=ProfileReleaseRead)
def profile_release(
    service: Service,
    context: Context,
    release_id: Annotated[str, Query(min_length=1)],
) -> ProfileReleaseRead:
    require_profile_read(service, context)
    return public_profile(release_id)


@router.post(
    "/{collection}/validation",
    response_model=CatalogValidationResult,
    response_model_exclude_none=True,
)
async def validate_proposal(
    collection: Collection,
    payload: ValidationRequest,
    service: Service,
    context: Context,
    base_uri: Annotated[str, Depends(get_resource_base_uri)],
) -> CatalogValidationResult:
    entity, model, _ = COLLECTIONS[collection]
    return await prevalidate(service, payload, entity, model, context, base_uri)


@router.get("/{collection}/{id}/relationships", response_model=RelationshipRead)
async def read_relationships(
    collection: Collection,
    id: UUID,
    response: Response,
    service: Relations,
    context: Context,
    include_inverses: bool = False,
) -> RelationshipRead:
    view = await service.relationships(
        id, profile_for(collection), COLLECTIONS[collection][2], context, inverses=include_inverses
    )
    response.headers["ETag"] = relationship_etag(view)
    return view.relationships


@router.patch("/{collection}/{id}/relationships", response_model=RelationshipRead)
async def update_relationships(
    collection: Collection,
    id: UUID,
    payload: RelationshipUpdate,
    response: Response,
    service: Relations,
    context: Context,
    if_match: Annotated[str, Depends(get_if_match)],
) -> RelationshipRead:
    current = await service.relationships(
        id, profile_for(collection), COLLECTIONS[collection][2], context, editing=True
    )
    require_if_match(if_match, current_etag=relationship_etag(current))
    view = await service.update_relationships(id, payload, current.catalog, context)
    response.headers["ETag"] = relationship_etag(view)
    return view.relationships
