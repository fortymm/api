from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1")


class PingResponse(BaseModel):
    data: str


@router.get("/ping")
async def ping() -> PingResponse:
    return PingResponse(data="pong")
