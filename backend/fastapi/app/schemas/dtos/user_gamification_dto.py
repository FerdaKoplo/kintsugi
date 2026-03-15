from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, field_validator


class UserGamificationBase(BaseModel):
    current_xp: int = 0
    current_level: int = 1
    login_streak: int = 0
    last_action_date: Optional[datetime] = None


class UserGamificationUpdate(BaseModel):
    current_xp: Optional[int] = None
    current_level: Optional[int] = None
    login_streak: Optional[int] = None
    last_action_date: Optional[datetime] = None

    @field_validator("current_xp")
    @classmethod
    def xp_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("XP cannot be negative.")
        return v

    @field_validator("current_level")
    @classmethod
    def level_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("Level must be at least 1.")
        return v

    @field_validator("login_streak")
    @classmethod
    def streak_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Login streak cannot be negative.")
        return v


class UserGamificationResponse(UserGamificationBase):
    user_id: uuid.UUID

    model_config = {"from_attributes": True}
