from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.jobs import router as jobs_router
from app.api.v1.permissions import router as permissions_router
from app.api.v1.roles import router as roles_router
from app.api.v1.schemas import UserPublic
from app.auth import encode_token
from app.auth_deps import parse_bearer_user
from app.db import get_session
from app.models import User
from app.usernames import generate_username

router = APIRouter(prefix="/v1")
router.include_router(roles_router)
router.include_router(permissions_router)
router.include_router(jobs_router)

_MAX_USERNAME_ATTEMPTS = 5


class PingResponse(BaseModel):
    data: str


class SessionResponse(BaseModel):
    token: str
    user: UserPublic


@router.get("/ping")
async def ping() -> PingResponse:
    return PingResponse(data="pong")


@router.post("/session")
async def create_session(
    db: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> SessionResponse:
    user = await parse_bearer_user(db, authorization)
    if user is None:
        user = await _create_user(db)

    return SessionResponse(
        token=encode_token(user.id),
        user=UserPublic(id=user.id, username=user.username),
    )


async def _create_user(db: AsyncSession) -> User:
    for _ in range(_MAX_USERNAME_ATTEMPTS):
        user = User(username=generate_username())
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        return user
    raise HTTPException(status_code=500, detail="Could not allocate username")
