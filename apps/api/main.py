from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.seed import seed_roles
from core.db import Base, engine, SessionLocal
import models
from routes.works import router as work_router
from routes.agents import router as agent_router
from routes.instances import router as instance_router
from routes.items import router as item_router
from routes.subjects import router as subject_router
from routes.users import router as user_router
from routes.auth import router as auth_router

from indexer.elastic.client import close_elasticsearch

@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Executa os seeds
    async with SessionLocal() as db:
        await seed_roles(db)
        
    yield
    await close_elasticsearch()

app = FastAPI(
    title="Libris - API",
    lifespan=lifespan
)

# Rotas
app.include_router(work_router)
app.include_router(agent_router)
app.include_router(instance_router)
app.include_router(item_router)
app.include_router(subject_router)
app.include_router(user_router)
app.include_router(auth_router)