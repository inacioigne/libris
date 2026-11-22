from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.modules.bibliograph.application.cataloging_profiles import (
    get_default_work_profile_document,
)
from app.modules.bibliograph.application.drafts import DraftCreate, DraftReceived
from app.modules.bibliograph.application.vocabularies import (
    Vocabulary,
    VocabularyNotFoundError,
    get_vocabulary,
)
from app.modules.identity.api.dependencies import require_permissions
from app.modules.identity.domain.models import AuthenticatedActor
from app.modules.identity.domain.permissions import Permission


router = APIRouter(prefix="/api/v1/bibliographic", tags=["bibliographic"])


@router.get(
    "/vocabularies/{vocabulary}",
    operation_id="getBibliographicVocabulary",
    response_model=Vocabulary,
)
async def read_vocabulary(vocabulary: str) -> Vocabulary:
    """Return a complete, versioned controlled-vocabulary snapshot."""
    try:
        return get_vocabulary(vocabulary)
    except VocabularyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vocabulary '{vocabulary}' is not available",
        ) from exc


@router.get(
    "/profile/work-default.v1.json",
    operation_id="getDefaultWorkSchema",
    response_class=JSONResponse,
)
async def get_default_work_schema() -> JSONResponse:
    """Return the provisional default Work cataloging schema for the frontend."""
    return JSONResponse(content=get_default_work_profile_document())


@router.post(
    "/drafts",
    operation_id="createBibliographicDraft",
    response_model=DraftReceived,
    status_code=status.HTTP_200_OK,
)
async def create_draft(
    payload: DraftCreate,
    actor: Annotated[
        AuthenticatedActor,
        Depends(require_permissions(Permission.BIBLIOGRAPHIC_CREATE)),
    ],
) -> DraftReceived:
    """Validate a partial Work description without persisting it."""
    del payload, actor
    return DraftReceived(message="Rascunho enviado com sucesso.")
