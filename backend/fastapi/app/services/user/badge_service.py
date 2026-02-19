from os import name
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.schema import UserBadge, User
from sqlalchemy import exists
# from app.schemas.schema import UserBadge as UserBadgeSchema


class BadgeService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_badges(self, user_id: str) -> List[UserBadge]:
        return self.db.query(UserBadge).filter(UserBadge.user_id == user_id).all()

    def has_badge(self, user_id: str, badge_slug: str) -> bool:
        stmt = exists().where(
            (UserBadge.user_id == user_id) & (UserBadge.badge_slug == badge_slug)
        )

        return self.db.query(stmt).scalar()

    def award_badge(self, user_id: str, badge_name: str, badge_slug: str) -> UserBadge:
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        existing_badge = (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == user_id, UserBadge.badge_slug == badge_slug)
            .first()
        )

        if existing_badge:
            return existing_badge

        new_badge = UserBadge(user_id=user_id, name=badge_name, badge_slug=badge_slug)

        self.db.add(new_badge)
        self.db.commit()
        self.db.refresh(new_badge)

        return new_badge

    def revoke_badge(self, user_id: str, badge_slug: str) -> dict:
        badge = (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == user_id, UserBadge.badge_slug == badge_slug)
            .first()
        )

        if not badge:
            raise HTTPException(status_code=404, detail="Badge not found")

        self.db.delete(badge)
        self.db.commit()

        return {"message": f"Badge '{badge_slug}' revoked from user."}

    def get_all_distributed_badges(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserBadge]:
        return (
            self.db.query(UserBadge)
            .order_by(UserBadge.earned_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
