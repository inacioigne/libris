from fastapi import FastAPI

from app.api.health_router import health_router
from app.catalog.api.works_router import works_router


app = FastAPI(
    title="Libris API",
    version="0.2.0",
)
app.include_router(health_router)
app.include_router(works_router)
