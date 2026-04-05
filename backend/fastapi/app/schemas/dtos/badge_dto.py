from datetime import datetime
import uuid
from pydantic import BaseModel


class UserBadgeResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    name: str
    badge_slug: str
    earned_at: datetime

    model_config = {"from_attributes": True}


class UserBadgeCreate(BaseModel):
    user_id: uuid.UUID
    name: str
    badge_slug: str
