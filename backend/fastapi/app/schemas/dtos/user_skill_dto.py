from enum import Enum
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid

from pydantic import BaseModel

from backend.fastapi.app.schemas.schema import SkillLevel, UserVerifyStatus


class UserSkillBase(BaseModel):
    skill_name: str
    level: SkillLevel = SkillLevel.BEGINNER


class UserSkillCreate(UserSkillBase):
    user_id: uuid.UUID


class UserSkillUpdate(BaseModel):
    skill_name: Optional[str] = None
    level: Optional[SkillLevel] = None


class UserSkillResponse(UserSkillBase):
    id: int
    user_id: uuid.UUID
    verified_level: UserVerifyStatus

    model_config = {"from_attributes": True}


class PaginatedUserSkillResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[UserSkillResponse]

    model_config = {"from_attributes": True}
