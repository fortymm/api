from uuid import UUID

from pydantic import BaseModel


class UserPublic(BaseModel):
    id: UUID
    username: str
