from indexer.documents.identifier import IdentifierSearch
from indexer.documents.subject import SubjectSearch
from indexer.documents.agent import AgentSearch
from indexer.documents.workTitle import WorkTitleSearch
from schemas.agent import AgentRead
from schemas.work import WorkAgentRead, WorkIdentifierRead, WorkRead, WorkSubjectRead, WorkTitleRead
from models.work_metadata.work import Work

from indexer.documents.work import (
    InstanceSummary,
    WorkSearchDocument,
)


class WorkMapper:

    @staticmethod
    def from_work(work: Work) -> WorkSearchDocument:
        return WorkSearchDocument(
            id=work.id,
            title=work.title,
            subtitle=getattr(work, "subtitle", None),
            summary=getattr(work, "summary", None),

            authors=[
                agent.name
                for agent in getattr(work, "agents", [])
                if getattr(agent, "name", None)
            ],

            subjects=[
                subject.name
                for subject in getattr(work, "subjects", [])
                if getattr(subject, "name", None)
            ],

            languages=[
                language.code
                for language in getattr(work, "languages", [])
                if getattr(language, "code", None)
            ],

            identifiers=[
                identifier.value
                for identifier in getattr(work, "identifiers", [])
                if getattr(identifier, "value", None)
            ],

            instances=[
                InstanceSummary(
                    id=instance.id,
                    edition=getattr(instance, "edition", None),
                    publisher=getattr(instance, "publisher", None),
                    publication_date=getattr(
                        instance,
                        "publication_date",
                        None,
                    ),
                    isbn=getattr(instance, "isbn", None),
                )
                for instance in getattr(work, "instances", [])
            ],

            instance_count=len(getattr(work, "instances", [])),

            available_item_count=sum(
                len(getattr(instance, "items", []))
                for instance in getattr(work, "instances", [])
            ),
        )
        
    @staticmethod
    def to_response(work: Work) -> WorkRead:
        return WorkRead(
                id=work.id,
                title=work.title,
    
                titles=[
                    WorkTitleRead(
                        id=title.id,
                        value=title.value,
                        language=title.language,
                        title_type=title.title_type,
                        is_preferred=title.is_preferred
                    )
                    for title in work.titles
                ],
    
                types=[
                    type_assignment.type
                    for type_assignment in work.types
                ],
    
                languages=[
                    language.language
                    for language in work.languages
                ],
    
                agents=[
                    WorkAgentRead(
                        agent_id=assignment.agent_id,
                        role=assignment.role,
                        primary=assignment.primary,
                        sequence=assignment.sequence
                    )
                    for assignment in work.agents
                ],
    
                subjects=[
                    WorkSubjectRead(
                        subject_id=assignment.subject_id,
                        sequence=assignment.sequence
                    )
                    for assignment in work.subjects
                ],
    
                genres=[
                    genre.value
                    for genre in work.genres
                ],
    
                summary=work.summary,
    
                notes=[
                    note.value
                    for note in work.notes
                ],
    
                identifiers=[
                    WorkIdentifierRead(
                        id=identifier.id,
                        type=identifier.type,
                        value=identifier.value,
                        uri=identifier.uri,
                        source=identifier.source
                    )
                    for identifier in work.identifiers
                ],
    
                uri=work.uri
            )
        

    @staticmethod
    def to_search_document(work: Work) -> WorkSearchDocument:
        return WorkSearchDocument(
            id=work.id,
            uri=work.uri,
            title=work.title,

            titles=[
                WorkTitleSearch(
                    value=title.value,
                    language=title.language,
                    title_type=title.title_type,
                    is_preferred=title.is_preferred,
                )
                for title in work.titles
            ],

            types=[
                type_assignment.type
                for type_assignment in work.types
            ],

            languages=[
                language.language
                for language in work.languages
            ],

            genres=[
                genre.value
                for genre in work.genres
            ],

            agents=[
                AgentSearch(
                    id=assignment.agent.id,
                    name=assignment.agent.name,
                    role=assignment.role,
                    primary=assignment.primary,
                    sequence=assignment.sequence,
                )
                for assignment in work.agents
                if assignment.agent is not None
            ],

            subjects=[
                SubjectSearch(
                    id=assignment.subject.id,
                    label=assignment.subject.preferred_label,
                    sequence=assignment.sequence,
                )
                for assignment in work.subjects
                if assignment.subject is not None
            ],

            summary=work.summary,

            notes=[
                note.value
                for note in work.notes
            ],

            identifiers=[
                IdentifierSearch(
                    type=identifier.type,
                    value=identifier.value,
                    uri=identifier.uri,
                    source=identifier.source,
                )
                for identifier in work.identifiers
            ],

            instances=[
                InstanceSummary(
                    id=instance.id,
                    isbn=instance.isbn,
                    publication_year=instance.publication_year,
                    formato=instance.formato,
                    publisher_id=instance.publisher_id,
                )
                for instance in work.instances
            ],

            instance_count=len(work.instances),

            available_item_count=sum(
                len(instance.items)
                for instance in work.instances
            ),
        )
            
