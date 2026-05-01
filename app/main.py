from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.config import settings
from app.queue import close_queue, init_queue


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_queue()
    try:
        yield
    finally:
        await close_queue()


app = FastAPI(title="fortymm-api", root_path=settings.root_path, lifespan=lifespan)
app.include_router(v1_router)
