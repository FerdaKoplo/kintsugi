from enum import Enum
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid

from pydantic import BaseModel, field_validator

from backend.fastapi.app.schemas.schema import VerificationTier


class UserReputationBase(BaseModel):
    average_rating: float = 0.0
    total_reviews: int = 0
    trust_score: int = 50
    verification_tier: VerificationTier = VerificationTier.UNVERIFIED


class UserReputationUpdate(BaseModel):
    average_rating: Optional[float] = None
    trust_score: Optional[int] = None
    verification_tier: Optional[VerificationTier] = None

    @field_validator("average_rating")
    @classmethod
    def rating_must_be_valid(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("Average rating must be between 0.0 and 5.0.")
        return v

    @field_validator("trust_score")
    @classmethod
    def trust_score_must_be_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Trust score must be between 0 and 100.")
        return v


class UserReputationResponse(UserReputationBase):
    user_id: uuid.UUID

    model_config = {"from_attributes": True}
