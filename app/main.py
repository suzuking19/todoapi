from fastapi import FastAPI

from .routers import common 

app = FastAPI()

app.include_router(common.router, prefix="/api", tags=["common"])