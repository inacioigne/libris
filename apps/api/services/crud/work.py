from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.subject import Subject
from models.agent import Agent
from services.repositories.work_repository import WorkRepository
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
    agent_ids = [agent.agent_id for agent in work_data.agents]
    result = await db.execute(
        select(Agent).where(Agent.id.in_(agent_ids))
        )
    agents_by_id = {
            agent.id: agent
            for agent in result.scalars().all()
        }
    
    for sequence, agent_data in enumerate(work_data.agents, start=1):

        agent = agents_by_id.get(agent_data.agent_id)

        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_data.agent_id} not found"
            )

        work.agents.append(
            WorkAgent(
                agent=agent,
                role=agent_data.role.value,
                primary=agent_data.primary,
                sequence=agent_data.sequence or sequence,
            )
        )


    # 9. Subjects
    subject_ids = [s.subject_id for s in work_data.subjects]
    result = await db.execute(
        select(Subject).where(Subject.id.in_(subject_ids))
    )
    subjects_by_id = {
        subject.id: subject
        for subject in result.scalars().all()
    }
    work_subjects = []
    for sequence, subject_data in enumerate(work_data.subjects, start=1):

        subject = subjects_by_id.get(subject_data.subject_id)
        if not subject:
            raise HTTPException(
                status_code=404,
                detail=f"Subject {subject_data.subject_id} not found"
            )

        work_subjects.append(
            WorkSubject(
                subject=subject,
                sequence=subject_data.sequence or sequence,
            )
        )
    work.subjects = work_subjects
    
    # for sequence, subject in enumerate(work_data.subjects, start=1):
    #     work.subjects.append(
    #         WorkSubject(
    #             subject_id=subject.subject_id,
    #             sequence=subject.sequence or sequence,
    #         )
    #     )

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
    # await db.refresh(work)

    return await WorkRepository.get_complete(db, work.id)

async def list_works(db: AsyncSession, offset: int = 0, limit: int = 20):
    result = await db.execute(
        select(Work).options(selectinload(Work.agents)).offset(offset).limit(limit)
    )
    return result.scalars().all()