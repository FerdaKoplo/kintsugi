from enum import Enum
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid

from pydantic import BaseModel

from backend.fastapi.app.schemas.schema import MessageStatus


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class MessageAttachmentBase(BaseModel):
    file_url: str
    file_type: Optional[str] = None


class MessageAttachmentCreate(MessageAttachmentBase):
    pass


class MessageAttachmentResponse(MessageAttachmentBase):
    id: int
    message_id: int
    model_config = {"from_attributes": True}


class MessageBase(BaseModel):
    job_id: int
    content: Optional[str] = None


class MessageCreate(MessageBase):
    sender_id: uuid.UUID
    attachments: List[MessageAttachmentCreate] = []
    message_type: MessageType = MessageType.TEXT


class SendImageRequest(BaseModel):
    job_id: int
    sender_id: uuid.UUID
    content: Optional[str] = None
    attachments: List[MessageAttachmentCreate]


class MessageResponse(MessageBase):
    id: int
    sender_id: uuid.UUID
    message_status: MessageStatus
    created_at: datetime
    attachments: List[MessageAttachmentResponse] = []
    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    job_id: int
    messages: List[MessageResponse]
    model_config = {"from_attributes": True}
