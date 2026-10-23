from fastapi import FastAPI

from app.api.health_router import health_router
from app.modules.bibliograph.api.router import router as bibliograph_router
from app.modules.identity.api.router import router as identity_router
from app.modules.identity.application.service import IdentityService
from app.modules.identity.infrastructure.oidc import OidcSettings, OidcTokenValidator


app = FastAPI(
    title="Libris API",
    version="0.3.0",
)
oidc_settings = OidcSettings.from_environment()
app.state.identity_service = IdentityService(
    validator=OidcTokenValidator(oidc_settings),
    role_source=oidc_settings.role_source,
    role_client=oidc_settings.role_client,
    human_client=oidc_settings.human_client,
)
app.include_router(health_router)
app.include_router(identity_router)
app.include_router(bibliograph_router)
