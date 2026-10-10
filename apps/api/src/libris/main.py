from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from libris.api.health import router as health_router
from libris.core.config import Settings
from libris.infrastructure.database import Database
from libris.modules.identity.api.router import router as identity_router
from libris.modules.identity.application.service import IdentityService
from libris.modules.identity.infrastructure.oidc import OIDCValidator


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(config)
        app.state.database = database
        client = httpx.AsyncClient(trust_env=False)
        app.state.identity_service = IdentityService(
            OIDCValidator(config, client), config.oidc_role_source, config.oidc_role_client
        )
        try:
            yield
        finally:
            await client.aclose()
            await database.close()

    app = FastAPI(title="Libris API", version="0.1.0", lifespan=lifespan)
    app.state.settings = config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type", "Authorization"],
    )
    app.include_router(health_router)
    app.include_router(identity_router)
    return app


app = create_app()
