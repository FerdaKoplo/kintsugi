from enum import Enum
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid

from pydantic import BaseModel, field_validator

from backend.fastapi.app.schemas.schema import OfferStatus


class OfferBase(BaseModel):
    item_id: int
    price_bid: float

    @field_validator("price_bid")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price bid must be greater than 0.")
        return v


class OfferCreate(OfferBase):
    fixer_id: uuid.UUID


class OfferUpdate(BaseModel):
    price_bid: Optional[float] = None
    status: Optional[OfferStatus] = None

    @field_validator("price_bid")
    @classmethod
    def price_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Price bid must be greater than 0.")
        return v


class OfferResponse(OfferBase):
    id: int
    fixer_id: uuid.UUID
    status: OfferStatus
    created_at: datetime

    model_config = {"from_attributes": True}
