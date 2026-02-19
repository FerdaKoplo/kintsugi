from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.schemas.schema import JobStatus


class JobBase:
    item_id: int
    agreed_price: float


class JobCreate(JobBase):
    fixer_id: UUID
    client_id: UUID


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None


class JobResponse(JobBase):
    id: int
    client_id: UUID
    fixer_id: UUID
    status: JobStatus

    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OfferCreate(BaseModel):
    item_id: int
    fixer_id: UUID
    offered_price: float
    message: Optional[str] = None
