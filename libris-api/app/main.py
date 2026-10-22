from fastapi import FastAPI

from app.api.health_router import health_router
from app.modules.bibliograph.api.router import router as bibliograph_router
from app.modules.identity.api.router import router as identity_router


app = FastAPI(
    title="Libris API",
    version="0.3.0",
)
app.include_router(health_router)
app.include_router(identity_router)
app.include_router(bibliograph_router)

