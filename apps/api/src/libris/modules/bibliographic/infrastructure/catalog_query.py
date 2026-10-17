"""One bounded statement over the selected heads; no per-resource lookups."""

from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from libris.modules.bibliographic.domain.editorial import EditorialState
from libris.modules.bibliographic.domain.models import ResourceIdentity
from libris.modules.bibliographic.domain.relationships import EntityType
from libris.modules.bibliographic.infrastructure.editorial import SemanticEditorialState as State
from libris.modules.bibliographic.infrastructure.persistence import SemanticResource as Resource
from libris.modules.bibliographic.infrastructure.persistence import SemanticRevision as Revision
from libris.modules.bibliographic.infrastructure.rdf import BF


def catalog_statement(
    entity: EntityType,
    *,
    public: bool,
    limit: int,
    after: UUID | None = None,
    internal_id: UUID | None = None,
    uri: str | None = None,
    profile: str | None = None,
    editorial_state: EditorialState | None = None,
) -> Select[tuple[UUID, str, int, list[dict[str, object]]]]:
    selected = State.published_revision if public else Resource.current_revision
    statement = (
        select(Resource.id, Resource.uri, Revision.number, Revision.document)
        .outerjoin(State, State.resource_id == Resource.id)
        .join(Revision, (Revision.resource_id == Resource.id) & (Revision.number == selected))
    )
    if public:
        statement = statement.where(State.editorial_state == EditorialState.PUBLISHED)
    elif editorial_state is not None:
        statement = statement.where(State.editorial_state == editorial_state)
    kinds = (
        [str(BF.Agent), str(BF.Person), str(BF.Organization)]
        if entity == EntityType.AGENT
        else ["http://www.w3.org/2004/02/skos/core#Concept"]
        if entity == EntityType.SUBJECT
        else [str(BF[entity.value])]
    )
    # Correlate @id AND @type on the same root object. Never parse every RDF row
    # in Python, or mistake a referenced/auxiliary node for collection membership.
    statement = statement.where(
        or_(
            *(
                Revision.document.contains(
                    func.jsonb_build_array(
                        func.jsonb_build_object(
                            "@id", Resource.uri, "@type", func.jsonb_build_array(kind)
                        )
                    )
                )
                for kind in kinds
            )
        )
    )
    if after is not None:
        statement = statement.where(Resource.id > after)
    if internal_id is not None:
        statement = statement.where(Resource.id == internal_id)
    if uri is not None:
        statement = statement.where(Resource.uri == uri)
    if profile is not None:
        statement = statement.where(Revision.profile == profile)
    return statement.order_by(Resource.id).limit(limit)


async def catalog_rows(
    session: AsyncSession, statement: Select[tuple[UUID, str, int, list[dict[str, object]]]]
) -> list[tuple[ResourceIdentity, int, list[dict[str, object]]]]:
    return [
        (ResourceIdentity(identifier, uri), number, document)
        for identifier, uri, number, document in (await session.execute(statement)).all()
    ]
