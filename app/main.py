from contextlib import asynccontextmanager
from fastapi import FastAPI

from .database import create_db_and_tables
from .routers import common, todos


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(common.router, tags=["common"])
app.include_router(todos.router, prefix="/api/v1", tags=["todos"])