from os import name
from typing import List
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.schema import UserBadge, User
from sqlalchemy import exists

from backend.fastapi.app.libs.db_helper import _commit_and_refresh
from backend.fastapi.app.schemas.dtos.badge_dto import UserBadgeResponse
# from app.schemas.schema import UserBadge as UserBadgeSchema


class BadgeService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_badges(self, user_id: uuid.UUID) -> List[UserBadgeResponse]:
        badges = self.db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
        return [UserBadgeResponse.model_validate(b) for b in badges]

    def has_badge(self, user_id: uuid.UUID, badge_slug: str) -> bool:
        count = (
            self.db.query(UserBadge)
            .filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_slug == badge_slug,
            )
            .count()
        )
        return count > 0

    def get_all_distributed_badges(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserBadgeResponse]:
        badges = (
            self.db.query(UserBadge)
            .order_by(UserBadge.earned_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [UserBadgeResponse.model_validate(b) for b in badges]

    def award_badge(
        self, user_id: uuid.UUID, badge_name: str, badge_slug: str
    ) -> UserBadgeResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        existing = (
            self.db.query(UserBadge)
            .filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_slug == badge_slug,
            )
            .first()
        )
        if existing:
            return UserBadgeResponse.model_validate(
                existing
            )  # idempotent — no error, just return

        new_badge = UserBadge(user_id=user_id, name=badge_name, badge_slug=badge_slug)
        self.db.add(new_badge)
        new_badge = _commit_and_refresh(self.db, new_badge)
        return UserBadgeResponse.model_validate(new_badge)

    def revoke_badge(self, user_id: uuid.UUID, badge_slug: str) -> dict:
        badge = (
            self.db.query(UserBadge)
            .filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_slug == badge_slug,
            )
            .first()
        )
        if not badge:
            raise HTTPException(status_code=404, detail="Badge not found.")

        self.db.delete(badge)
        self.db.commit()
        return {"message": f"Badge '{badge_slug}' revoked from user."}
