from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.config import settings

app = FastAPI(title="fortymm-api", root_path=settings.root_path)
app.include_router(v1_router)
