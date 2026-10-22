from fastapi import FastAPI

from app.api.health_router import health_router


app = FastAPI(
    title="Libris API",
    version="0.2.0",
)
app.include_router(health_router)
