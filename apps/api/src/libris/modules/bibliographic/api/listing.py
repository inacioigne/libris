"""Explicit public/editorial collections, sharing one bounded query use case."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from libris.modules.bibliographic.api.dependencies import get_catalog_service
from libris.modules.bibliographic.api.schemas import (
    AgentRead,
    InstanceRead,
    ItemRead,
    SubjectRead,
    WorkRead,
)
from libris.modules.bibliographic.api.schemas.listing import (
    CatalogPage,
    EditorialCatalogQuery,
    PublicCatalogQuery,
)
from libris.modules.bibliographic.application.catalog import CatalogService
from libris.modules.bibliographic.application.catalog_listing import list_catalog
from libris.modules.bibliographic.domain.relationships import EntityType
from libris.modules.identity.api.dependencies import get_execution_context
from libris.modules.identity.application.authorization import HumanContext

router = APIRouter()
Service = Annotated[CatalogService, Depends(get_catalog_service)]
Context = Annotated[HumanContext, Depends(get_execution_context)]


@router.get("/works", response_model=CatalogPage[WorkRead])
async def list_works(
    query: Annotated[EditorialCatalogQuery, Query()],
    service: Service,
    context: Context,
) -> CatalogPage[WorkRead]:
    page = await list_catalog(service, EntityType.WORK, query, public=False, context=context)
    return CatalogPage[WorkRead].model_validate(page.model_dump())


@router.get("/public/works", response_model=CatalogPage[WorkRead])
async def list_public_works(
    query: Annotated[PublicCatalogQuery, Query()],
    service: Service,
) -> CatalogPage[WorkRead]:
    page = await list_catalog(service, EntityType.WORK, query, public=True)
    return CatalogPage[WorkRead].model_validate(page.model_dump())


@router.get("/instances", response_model=CatalogPage[InstanceRead])
async def list_instances(
    query: Annotated[EditorialCatalogQuery, Query()],
    service: Service,
    context: Context,
) -> CatalogPage[InstanceRead]:
    page = await list_catalog(service, EntityType.INSTANCE, query, public=False, context=context)
    return CatalogPage[InstanceRead].model_validate(page.model_dump())


@router.get("/public/instances", response_model=CatalogPage[InstanceRead])
async def list_public_instances(
    query: Annotated[PublicCatalogQuery, Query()],
    service: Service,
) -> CatalogPage[InstanceRead]:
    page = await list_catalog(service, EntityType.INSTANCE, query, public=True)
    return CatalogPage[InstanceRead].model_validate(page.model_dump())


@router.get("/items", response_model=CatalogPage[ItemRead])
async def list_items(
    query: Annotated[EditorialCatalogQuery, Query()],
    service: Service,
    context: Context,
) -> CatalogPage[ItemRead]:
    page = await list_catalog(service, EntityType.ITEM, query, public=False, context=context)
    return CatalogPage[ItemRead].model_validate(page.model_dump())


@router.get("/public/items", response_model=CatalogPage[ItemRead])
async def list_public_items(
    query: Annotated[PublicCatalogQuery, Query()],
    service: Service,
) -> CatalogPage[ItemRead]:
    page = await list_catalog(service, EntityType.ITEM, query, public=True)
    return CatalogPage[ItemRead].model_validate(page.model_dump())


@router.get("/agents", response_model=CatalogPage[AgentRead])
async def list_agents(
    query: Annotated[EditorialCatalogQuery, Query()],
    service: Service,
    context: Context,
) -> CatalogPage[AgentRead]:
    page = await list_catalog(service, EntityType.AGENT, query, public=False, context=context)
    return CatalogPage[AgentRead].model_validate(page.model_dump())


@router.get("/public/agents", response_model=CatalogPage[AgentRead])
async def list_public_agents(
    query: Annotated[PublicCatalogQuery, Query()],
    service: Service,
) -> CatalogPage[AgentRead]:
    page = await list_catalog(service, EntityType.AGENT, query, public=True)
    return CatalogPage[AgentRead].model_validate(page.model_dump())


@router.get("/subjects", response_model=CatalogPage[SubjectRead])
async def list_subjects(
    query: Annotated[EditorialCatalogQuery, Query()],
    service: Service,
    context: Context,
) -> CatalogPage[SubjectRead]:
    page = await list_catalog(service, EntityType.SUBJECT, query, public=False, context=context)
    return CatalogPage[SubjectRead].model_validate(page.model_dump())


@router.get("/public/subjects", response_model=CatalogPage[SubjectRead])
async def list_public_subjects(
    query: Annotated[PublicCatalogQuery, Query()],
    service: Service,
) -> CatalogPage[SubjectRead]:
    page = await list_catalog(service, EntityType.SUBJECT, query, public=True)
    return CatalogPage[SubjectRead].model_validate(page.model_dump())
