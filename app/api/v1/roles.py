import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import UserPublic
from app.auth_deps import get_current_user
from app.db import get_session
from app.models import Permission, Role, RolePermission, User, UserRole

router = APIRouter(prefix="/roles", dependencies=[Depends(get_current_user)])

_MAX_SLUG_ATTEMPTS = 25
_MAX_DESCRIPTION = 2000
_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class RolePublic(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    member_count: int
    permission_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=_MAX_DESCRIPTION)
    permission_ids: list[UUID] | None = None


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=_MAX_DESCRIPTION)
    permission_ids: list[UUID] | None = None


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


async def _permission_ids_for(db: AsyncSession, role_id: UUID) -> list[UUID]:
    stmt = (
        select(RolePermission.permission_id)
        .where(RolePermission.role_id == role_id)
        .order_by(RolePermission.permission_id)
    )
    return list((await db.execute(stmt)).scalars())


async def _permission_ids_by_role(db: AsyncSession, role_ids: list[UUID]) -> dict[UUID, list[UUID]]:
    if not role_ids:
        return {}
    stmt = (
        select(RolePermission.role_id, RolePermission.permission_id)
        .where(RolePermission.role_id.in_(role_ids))
        .order_by(RolePermission.role_id, RolePermission.permission_id)
    )
    grouped: dict[UUID, list[UUID]] = {rid: [] for rid in role_ids}
    for role_id, permission_id in (await db.execute(stmt)).all():
        grouped[role_id].append(permission_id)
    return grouped


async def _set_role_permissions(
    db: AsyncSession, role_id: UUID, permission_ids: list[UUID]
) -> list[UUID]:
    desired = set(permission_ids)
    if desired:
        found = set(
            (await db.execute(select(Permission.id).where(Permission.id.in_(desired)))).scalars()
        )
        missing = desired - found
        if missing:
            ids = ", ".join(sorted(str(i) for i in missing))
            raise HTTPException(status_code=400, detail=f"Unknown permission ids: {ids}")

    current = set(
        (
            await db.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
            )
        ).scalars()
    )
    to_remove = current - desired
    to_add = desired - current

    if to_remove:
        await db.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.in_(to_remove),
            )
        )
    for pid in to_add:
        db.add(RolePermission(role_id=role_id, permission_id=pid))

    return sorted(desired)


def _to_public(role: Role, member_count: int, permission_ids: list[UUID]) -> RolePublic:
    return RolePublic(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        member_count=member_count,
        permission_ids=permission_ids,
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
    rows = (await db.execute(stmt)).all()
    perms_by_role = await _permission_ids_by_role(db, [role.id for role, _ in rows])
    return [_to_public(role, int(count), perms_by_role.get(role.id, [])) for role, count in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RolePublic:
    base = _slugify(payload.name)
    role: Role | None = None
    for attempt in range(_MAX_SLUG_ATTEMPTS):
        slug = base if attempt == 0 else f"{base}-{attempt + 1}"
        candidate = Role(slug=slug, name=payload.name, description=payload.description)
        db.add(candidate)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            continue
        role = candidate
        break
    if role is None:
        raise HTTPException(status_code=500, detail="Could not allocate role slug")

    perms = (
        await _set_role_permissions(db, role.id, payload.permission_ids)
        if payload.permission_ids is not None
        else []
    )
    await db.commit()
    await db.refresh(role)
    return _to_public(role, 0, perms)


@router.get("/{role}")
async def get_role(
    role: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RolePublic:
    obj, count = await _get_role_with_count(db, role)
    return _to_public(obj, count, await _permission_ids_for(db, obj.id))


@router.patch("/{role}")
async def update_role(
    role: str,
    payload: RoleUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RolePublic:
    obj, count = await _get_role_with_count(db, role)
    data = payload.model_dump(exclude_unset=True, exclude={"permission_ids"})
    for field, value in data.items():
        setattr(obj, field, value)
    perms = (
        await _set_role_permissions(db, obj.id, payload.permission_ids)
        if payload.permission_ids is not None
        else await _permission_ids_for(db, obj.id)
    )
    await db.commit()
    await db.refresh(obj)
    return _to_public(obj, count, perms)


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
    # FK would reject a missing user with IntegrityError; pre-check is for the 404.
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
