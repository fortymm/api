from fastapi import APIRouter

router = APIRouter(prefix="/v1")


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"data": "pong"}
