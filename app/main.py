from fastapi import FastAPI

from app.api.v1.router import router as v1_router

app = FastAPI(title="fortymm-api")
app.include_router(v1_router)
