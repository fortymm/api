from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_token, encode_token
from app.db import get_session
from app.models import User
from app.usernames import generate_username

router = APIRouter(prefix="/v1")

_MAX_USERNAME_ATTEMPTS = 5


class PingResponse(BaseModel):
    data: str


class UserPublic(BaseModel):
    id: UUID
    username: str


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
    user = await _resolve_user(db, authorization)
    if user is None:
        user = await _create_user(db)

    return SessionResponse(
        token=encode_token(user.id),
        user=UserPublic(id=user.id, username=user.username),
    )


async def _resolve_user(db: AsyncSession, authorization: str | None) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    user_id = decode_token(token)
    if user_id is None:
        return None
    return await db.get(User, user_id)


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
