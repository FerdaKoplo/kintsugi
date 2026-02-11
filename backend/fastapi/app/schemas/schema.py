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


class UserGamification(Base):
    __tablename__ = "user_gamification"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=1)

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


class Items(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)


class Diagnosis(Base):
    __tablename__ = "diagnosis"
    id: Mapped[int] = mapped_column(primary_key=True)


class Offer(Base):
    __tablename__ = "offers"
    id: Mapped[int] = mapped_column(primary_key=True)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)


class Message:
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)


class MessageAttachment:
    __tablename__ = "message_attachments"
    id: Mapped[int] = mapped_column(primary_key=True)


class Review:
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)


class UserSkill(Base):
    __tablename__ = "user_skills"
    id: Mapped[int] = mapped_column(primary_key=True)


class Rewards(Base):
    __tablename__ = "rewards"
    id: Mapped[int] = mapped_column(primary_key=True)
