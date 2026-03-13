import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.schemas.schema import JobStatus


class JobBase(BaseModel):
    item_id: int
    agreed_price: float

    @field_validator("agreed_price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Agreed price must be greater than 0.")
        return v


class JobCreate(JobBase):
    client_id: uuid.UUID
    fixer_id: uuid.UUID


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    agreed_price: Optional[float] = None
    completed_at: Optional[datetime] = None

    @field_validator("agreed_price")
    @classmethod
    def price_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Agreed price must be greater than 0.")
        return v


class JobResponse(JobBase):
    id: int
    client_id: uuid.UUID
    fixer_id: uuid.UUID
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
