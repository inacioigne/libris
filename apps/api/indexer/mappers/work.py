from models.work import Work
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