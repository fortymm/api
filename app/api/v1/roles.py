import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import UserPublic
from app.auth_deps import get_current_user
from app.db import get_session
from app.models import Role, User, UserRole

router = APIRouter(prefix="/roles", dependencies=[Depends(get_current_user)])

_MAX_SLUG_ATTEMPTS = 25
_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class RolePublic(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    member_count: int
    created_at: datetime
    updated_at: datetime


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None
    # Accepted for forward-compat with the SPA; not persisted (fake permissions).
    permission_codes: list[str] | None = None


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None
    permission_codes: list[str] | None = None


class RoleMember(BaseModel):
    user: UserPublic
    assigned_at: datetime


def _slugify(name: str) -> str:
    base = _SLUG_NON_ALNUM.sub("-", name.lower()).strip("-")
    return base or "role"


def _ident_filter(ident: str):
    try:
        return Role.id == UUID(ident)
    except ValueError:
        return Role.slug == ident


async def _get_role(db: AsyncSession, ident: str) -> Role:
    role = await db.scalar(select(Role).where(_ident_filter(ident)))
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


async def _get_role_with_count(db: AsyncSession, ident: str) -> tuple[Role, int]:
    stmt = (
        select(Role, func.count(UserRole.user_id))
        .join(UserRole, UserRole.role_id == Role.id, isouter=True)
        .where(_ident_filter(ident))
        .group_by(Role.id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return row[0], int(row[1])


def _to_public(role: Role, member_count: int) -> RolePublic:
    return RolePublic(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        member_count=member_count,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.get("")
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[RolePublic]:
    stmt = (
        select(Role, func.count(UserRole.user_id))
        .join(UserRole, UserRole.role_id == Role.id, isouter=True)
        .group_by(Role.id)
        .order_by(Role.created_at)
    )
    result = await db.execute(stmt)
    return [_to_public(role, int(count)) for role, count in result.all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RolePublic:
    base = _slugify(payload.name)
    for attempt in range(_MAX_SLUG_ATTEMPTS):
        slug = base if attempt == 0 else f"{base}-{attempt + 1}"
        role = Role(slug=slug, name=payload.name, description=payload.description)
        db.add(role)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        await db.refresh(role)
        return _to_public(role, 0)
    raise HTTPException(status_code=500, detail="Could not allocate role slug")


@router.get("/{role}")
async def get_role(
    role: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RolePublic:
    obj, count = await _get_role_with_count(db, role)
    return _to_public(obj, count)


@router.patch("/{role}")
async def update_role(
    role: str,
    payload: RoleUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RolePublic:
    obj, count = await _get_role_with_count(db, role)
    data = payload.model_dump(exclude_unset=True, exclude={"permission_codes"})
    for field, value in data.items():
        setattr(obj, field, value)
    await db.commit()
    await db.refresh(obj)
    return _to_public(obj, count)


@router.delete("/{role}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    obj = await _get_role(db, role)
    await db.delete(obj)
    await db.commit()


@router.get("/{role}/members")
async def list_members(
    role: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[RoleMember]:
    obj = await _get_role(db, role)
    stmt = (
        select(User, UserRole.assigned_at)
        .join(UserRole, UserRole.user_id == User.id)
        .where(UserRole.role_id == obj.id)
        .order_by(UserRole.assigned_at)
    )
    result = await db.execute(stmt)
    return [
        RoleMember(
            user=UserPublic(id=user.id, username=user.username),
            assigned_at=assigned_at,
        )
        for user, assigned_at in result.all()
    ]


@router.put("/{role}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(
    role: str,
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    obj = await _get_role(db, role)
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.add(UserRole(user_id=user_id, role_id=obj.id))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()


@router.delete("/{role}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    role: str,
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    obj = await _get_role(db, role)
    membership = await db.get(UserRole, (user_id, obj.id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    await db.delete(membership)
    await db.commit()
