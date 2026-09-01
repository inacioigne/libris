from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.work_metadata.work import Work
from models.work_metadata.workTitle import WorkTitle
from models.work_metadata.workLanguage import WorkLanguage
from models.work_metadata.workGenre import WorkGenre
from models.work_metadata.workNote import WorkNote
from models.work_metadata.workIdentifier import WorkIdentifier
from models.work_metadata.workTypeAssignment import WorkTypeAssignment
from models.work_metadata.workAgent import WorkAgent
from models.work_metadata.workSubject import WorkSubject
from models.work_metadata.workRelation import WorkRelation

from schemas.work import WorkCreate


async def create_work(
    db: AsyncSession,
    work_data: WorkCreate,
) -> Work:

    # 1. Cria apenas os atributos pertencentes diretamente ao Work
    work = Work(
        title=work_data.title,
        summary=work_data.summary,
        uri=str(work_data.uri) if work_data.uri else None,
    )

    # 2. Titles
    for sequence, title in enumerate(work_data.titles, start=1):
        work.titles.append(
            WorkTitle(
                value=title.value,
                language=title.language,
                title_type=title.title_type,
                is_preferred=title.is_preferred,
                sequence=sequence,
            )
        )

    # 3. Types
    for work_type in work_data.types:
        work.types.append(
            WorkTypeAssignment(
                type=work_type.value,
            )
        )

    # 4. Languages
    for language in work_data.languages:
        work.languages.append(
            WorkLanguage(
                language=language,
            )
        )

    # 5. Genres
    for sequence, genre in enumerate(work_data.genres, start=1):
        work.genres.append(
            WorkGenre(
                value=genre,
                sequence=sequence,
            )
        )

    # 6. Notes
    for sequence, note in enumerate(work_data.notes, start=1):
        work.notes.append(
            WorkNote(
                value=note,
                sequence=sequence,
            )
        )

    # 7. Identifiers
    for identifier in work_data.identifiers:
        work.identifiers.append(
            WorkIdentifier(
                type=identifier.type.value,
                value=identifier.value,
                uri=str(identifier.uri) if identifier.uri else None,
                source=identifier.source,
            )
        )

    # 8. Agents
    for sequence, agent in enumerate(work_data.agents, start=1):
        work.agents.append(
            WorkAgent(
                agent_id=agent.agent_id,
                role=agent.role.value,
                primary=agent.primary,
                sequence=agent.sequence or sequence,
            )
        )

    # 9. Subjects
    for sequence, subject in enumerate(work_data.subjects, start=1):
        work.subjects.append(
            WorkSubject(
                subject_id=subject.subject_id,
                sequence=subject.sequence or sequence,
            )
        )

    # 10. Relations
    for relation in work_data.relations:
        work.outgoing_relations.append(
            WorkRelation(
                target_work_id=relation.work_id,
                relation_type=relation.relation_type.value,
            )
        )

    db.add(work)

    await db.commit()
    await db.refresh(work)

    return work

async def list_works(db: AsyncSession, offset: int = 0, limit: int = 20):
    result = await db.execute(
        select(Work).options(selectinload(Work.agents)).offset(offset).limit(limit)
    )
    return result.scalars().all()