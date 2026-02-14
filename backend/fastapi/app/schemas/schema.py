from __future__ import annotations


import uuid
import enum
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class RewardStatus(enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"


class UserVerifyStatus(enum.Enum):
    UNVERIFIED = "unverified"

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class MessageStatus(enum.Enum):
    READ = "read"
    SENT = "sent"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DELETED = "deleted"


class ItemStatus(enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    UNFIXABLE = "unfixable"
    ARCHIVED = "archived"


class OfferStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class DiagnosisType(enum.Enum):
    VISUAL = "visual"
    AUDIO = "audio"
    MANUAL = "manual"
    HYBRID = "hybrid"


class SkillLevel(enum.IntEnum):
    BEGINNER = 1
    INTERMEDIATE = 2
    EXPERT = 3
    CERTIFIED_PRO = 4


class VerificationTier(enum.IntEnum):
    UNVERIFIED = 0
    EMAIL_ONLY = 1
    PHONE_VERIFIED = 2
    GOV_ID_VERIFIED = 3
    PRO_CERTIFIED = 4


class UserStatus(enum.Enum):
    VERIFIED = "verfied"
    ACTIVE = "active"
    BANNED = "banned"
    UNVERIFIED = "unverified"
    SUSPENDED = "suspended"
    PENDING = "pending_review"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String)
    avatar_url: Mapped[Optional[str]] = mapped_column(String)
    bio: Mapped[Optional[str]] = mapped_column(Text)

    user_status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus), default=UserStatus.UNVERIFIED, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    gamification: Mapped["UserGamification"] = relationship(
        "UserGamification",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    reputation: Mapped["UserReputation"] = relationship(
        "UserReputation",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    badges: Mapped[List["UserBadge"]] = relationship(
        "UserBadge", back_populates="user", cascade="all, delete-orphan"
    )

    items: Mapped[List["Item"]] = relationship(
        "Item", back_populates="owner", cascade="all, delete-orphan"
    )

    offers_made: Mapped[List["Offer"]] = relationship(
        "Offer", back_populates="fixer", cascade="all, delete-orphan"
    )

    jobs_as_client: Mapped[List["Job"]] = relationship(
        "Job", back_populates="client", foreign_keys="[Job.client_id]"
    )
    jobs_as_fixer: Mapped[List["Job"]] = relationship(
        "Job", back_populates="fixer", foreign_keys="[Job.fixer_id]"
    )

    skills: Mapped[List["UserSkill"]] = relationship(
        "UserSkill", back_populates="user", cascade="all, delete-orphan"
    )
    reviews_written: Mapped[List["Review"]] = relationship(
        "Review", back_populates="reviewer", foreign_keys="[Review.reviewer_id]"
    )
    reviews_received: Mapped[List["Review"]] = relationship(
        "Review", back_populates="target_user", foreign_keys="[Review.target_id]"
    )


class UserGamification(Base):
    __tablename__ = "user_gamification"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=1)

    login_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_action_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="gamification")


class UserReputation(Base):
    __tablename__ = "user_reputation"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)

    verification_tier: Mapped[VerificationTier] = mapped_column(
        Integer, default=VerificationTier.UNVERIFIED
    )

    user: Mapped["User"] = relationship("User", back_populates="reputation")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String)
    badge_slug: Mapped[str] = mapped_column(String)

    earned_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="badges")


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String, index=True)

    status: Mapped[ItemStatus] = mapped_column(
        SAEnum(ItemStatus), default=ItemStatus.OPEN
    )

    images: Mapped[List[str]] = mapped_column(JSONB, default=[])

    owner: Mapped["User"] = relationship("User", back_populates="items")
    diagnoses: Mapped[List["Diagnosis"]] = relationship(
        "Diagnosis", back_populates="item", cascade="all, delete-orphan"
    )
    offers: Mapped[List["Offer"]] = relationship(
        "Offer", back_populates="item", cascade="all, delete-orphan"
    )
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="item")


class Diagnosis(Base):
    __tablename__ = "diagnosis"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)

    diagnosis_type: Mapped[DiagnosisType] = mapped_column(
        SAEnum(DiagnosisType), default=DiagnosisType.VISUAL
    )
    ai_model_used: Mapped[str] = mapped_column(String)

    result_json: Mapped[dict] = mapped_column(JSONB)
    detected_issue: Mapped[str] = mapped_column(String)
    confidence_score: Mapped[float] = mapped_column(Float)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    item: Mapped["Item"] = relationship("Item", back_populates="diagnoses")


class Offer(Base):
    __tablename__ = "offers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    fixer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    price_bid: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[OfferStatus] = mapped_column(
        SAEnum(OfferStatus), default=OfferStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    item: Mapped["Item"] = relationship("Item", back_populates="offers")
    fixer: Mapped["User"] = relationship("User", back_populates="offers_made")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)

    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    fixer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    agreed_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), default=JobStatus.ACTIVE
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    item: Mapped["Item"] = relationship("Item", back_populates="jobs")
    client: Mapped["User"] = relationship(
        "User", foreign_keys=[client_id], back_populates="jobs_as_client"
    )
    fixer: Mapped["User"] = relationship(
        "User", foreign_keys=[fixer_id], back_populates="jobs_as_fixer"
    )

    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="job", cascade="all, delete-orphan"
    )
    review: Mapped[Optional["Review"]] = relationship(
        "Review", back_populates="job", uselist=False
    )


class Message:
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    message_status: Mapped[MessageStatus] = mapped_column(
        SAEnum(MessageStatus), default=MessageStatus.DELIVERED
    )
    content: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["Job"] = relationship("Job", back_populates="messages")
    attachments: Mapped[List["MessageAttachment"]] = relationship(
        "MessageAttachment", back_populates="message"
    )


class MessageAttachment:
    __tablename__ = "message_attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)

    file_url: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String)

    message: Mapped["Message"] = relationship("Message", back_populates="attachments")


class Review:
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)

    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    rating: Mapped[int] = mapped_column(Integer)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["Job"] = relationship("Job", back_populates="review")
    reviewer: Mapped["User"] = relationship(
        "User", foreign_keys=[reviewer_id], back_populates="reviews_written"
    )
    target_user: Mapped["User"] = relationship(
        "User", foreign_keys=[target_id], back_populates="reviews_received"
    )


class UserSkill(Base):
    __tablename__ = "user_skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    skill_name: Mapped[str] = mapped_column(String)

    level: Mapped[SkillLevel] = mapped_column(
        SAEnum(SkillLevel), default=SkillLevel.BEGINNER
    )

    verified_level: Mapped[UserVerifyStatus] = mapped_column(
        SAEnum(UserVerifyStatus), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="skills")


class Rewards(Base):
    __tablename__ = "rewards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    cost_xp: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[Optional[str]] = mapped_column(String)
