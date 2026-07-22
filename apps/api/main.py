from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.db import Base, engine
from routes.works import router as work_router
from routes.agents import router as agent_router
from routes.instances import router as instance_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Libris - API",
    lifespan=lifespan
)

# Rotas
app.include_router(work_router)
app.include_router(agent_router)
app.include_router(instance_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}