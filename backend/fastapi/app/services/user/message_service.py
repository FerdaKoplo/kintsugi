from typing import List
import uuid
from gotrue import Optional
from sqlalchemy.orm import Session, joinedload
from app.schemas.schema import Message, MessageAttachment, MessageStatus
from app.schemas.dtos.message_dto import (
    MessageCreate,
    MessageStatus,
    MessageResponse,
    ChatHistoryResponse,
    MessageType,
    SendImageRequest,
)


class MessageService:
    def __init__(self, db: Session):
        self.db = db

    def get_message_by_id(self, message_id: int, user_id: int) -> Optional[Message]:
        return (
            self.db.query(Message)
            .options(joinedload(Message.attachments))
            .filter(Message.id == message_id)
            .first()
        )

    def get_chat_history(self, job_id: int, user_id: uuid.UUID) -> ChatHistoryResponse:
        messages: List[Message] = (
            self.db.query(Message)
            .options(joinedload(Message.attachments))
            .filter(Message.job_id == job_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        return ChatHistoryResponse(
            job_id=job_id,
            messages=[MessageResponse.model_validate(m) for m in messages],
        )

    def send_message(self, message_data: MessageCreate) -> MessageResponse:
        if (
            message_data.message_type == MessageType.IMAGE
            and not message_data.attachments
        ):
            raise ValueError("Image message requires at least one attachment.")

        db_message = Message(
            job_id=message_data.job_id,
            sender_id=message_data.sender_id,
            content=message_data.content,
            message_type=message_data.message_type,
            message_status=MessageStatus.DELIVERED,
        )

        self.db.add(db_message)
        self.db.flush()

        if message_data.attachments:
            attachments = [
                MessageAttachment(
                    message_id=db_message.id,
                    file_url=a.file_url,
                    file_type=a.file_type,
                )
                for a in message_data.attachments
            ]
            self.db.bulk_save_objects(attachments)

        self.db.commit()
        self.db.refresh(db_message)
        return MessageResponse.model_validate(db_message)

    def mark_as_read(
        self, message_id: int, user_id: uuid.UUID
    ) -> Optional[MessageResponse]:
        db_message = self.get_chat_history(message_id, user_id)
        if not db_message:
            return None

        db_message.message_status = MessageStatus.READ
        self.db.commit()
        self.db.refresh(db_message)
        return MessageResponse.model_validate(db_message)
