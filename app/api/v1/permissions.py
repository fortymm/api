from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_deps import get_current_user
from app.db import get_session
from app.models import Permission

router = APIRouter(prefix="/permissions", dependencies=[Depends(get_current_user)])

_CODE_PATTERN = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$"


class PermissionPublic(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    group_name: str
    created_at: datetime
    updated_at: datetime


class PermissionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64, pattern=_CODE_PATTERN)
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    group_name: str = Field(min_length=1, max_length=64)


class PermissionUpdate(BaseModel):
    # `code` is immutable — changing it would break code-path references.
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    group_name: str | None = Field(default=None, min_length=1, max_length=64)


def _ident_filter(ident: str):
    try:
        return Permission.id == UUID(ident)
    except ValueError:
        return Permission.code == ident


async def _get_permission(db: AsyncSession, ident: str) -> Permission:
    perm = await db.scalar(select(Permission).where(_ident_filter(ident)))
    if perm is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm


def _to_public(perm: Permission) -> PermissionPublic:
    return PermissionPublic(
        id=perm.id,
        code=perm.code,
        name=perm.name,
        description=perm.description,
        group_name=perm.group_name,
        created_at=perm.created_at,
        updated_at=perm.updated_at,
    )


@router.get("")
async def list_permissions(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[PermissionPublic]:
    stmt = select(Permission).order_by(Permission.group_name, Permission.code)
    result = await db.execute(stmt)
    return [_to_public(p) for p in result.scalars()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PermissionPublic:
    perm = Permission(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        group_name=payload.group_name,
    )
    db.add(perm)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Permission with code {payload.code!r} already exists",
        ) from None
    await db.refresh(perm)
    return _to_public(perm)


@router.get("/{permission}")
async def get_permission(
    permission: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PermissionPublic:
    perm = await _get_permission(db, permission)
    return _to_public(perm)


@router.patch("/{permission}")
async def update_permission(
    permission: str,
    payload: PermissionUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PermissionPublic:
    perm = await _get_permission(db, permission)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(perm, field, value)
    await db.commit()
    await db.refresh(perm)
    return _to_public(perm)


@router.delete("/{permission}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    perm = await _get_permission(db, permission)
    await db.delete(perm)
    await db.commit()
