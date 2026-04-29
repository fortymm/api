from fastapi import APIRouter
from pydantic import BaseModel

from app.permissions_catalogue import PERMISSION_GROUPS

router = APIRouter(prefix="/permissions")


class PermissionItem(BaseModel):
    code: str
    name: str
    description: str


class PermissionGroup(BaseModel):
    key: str
    label: str
    permissions: list[PermissionItem]


class PermissionsResponse(BaseModel):
    groups: list[PermissionGroup]


_RESPONSE = PermissionsResponse.model_validate({"groups": PERMISSION_GROUPS})


@router.get("")
async def list_permissions() -> PermissionsResponse:
    return _RESPONSE
