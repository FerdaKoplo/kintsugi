import uuid
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from backend.fastapi.app.schemas.dtos.user_gamification_dto import (
    UserGamificationResponse,
)
from backend.fastapi.app.libs.db_helper import _commit_and_refresh
from backend.fastapi.app.schemas.schema import UserGamification


XP_PER_LEVEL_BASE = 100
STREAK_BONUS_XP = 10


class GamificationService:
    def __init__(self, db: Session):
        self.db = db

    # shared
    def get_progress(self, user_id: uuid.UUID) -> UserGamification:
        progress = (
            self.db.query(UserGamification)
            .filter(UserGamification.user_id == user_id)
            .first()
        )
        if not progress:
            raise HTTPException(
                status_code=404, detail="Gamification record not found."
            )
        return progress

    def create_initial_progress(self, user_id: uuid.UUID) -> UserGamificationResponse:
        existing = (
            self.db.query(UserGamification)
            .filter(UserGamification.user_id == user_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="Gamification record already exists."
            )

        progress = UserGamification(
            user_id=user_id,
            current_xp=0,
            current_level=1,
            login_streak=0,
            last_action_date=datetime.now(timezone.utc),
        )
        self.db.add(progress)
        progress = _commit_and_refresh(self.db, progress)
        return UserGamificationResponse.model_validate(progress)

    def add_xp(self, user_id: uuid.UUID, amount: int) -> UserGamificationResponse:
        if amount <= 0:
            raise ValueError("XP amount must be greater than 0.")

        progress = self.get_progress(user_id)
        progress.current_xp += amount

        while progress.current_xp >= (
            xp_needed := progress.current_level * XP_PER_LEVEL_BASE
        ):
            progress.current_xp -= xp_needed
            progress.current_level += 1

        progress = _commit_and_refresh(self.db, progress)
        return UserGamificationResponse.model_validate(progress)

    def update_login_streak(self, user_id: uuid.UUID) -> UserGamificationResponse:
        progress = self.get_progress(user_id)
        now = datetime.now(timezone.utc)

        if not progress.last_action_date:
            progress.login_streak = 1
            progress.last_action_date = now
            progress = _commit_and_refresh(self.db, progress)

            return UserGamificationResponse.model_validate(progress)

        delta = (now.date() - progress.last_action_date.date()).days

        if delta == 0:
            return UserGamificationResponse.model_validate(progress)

        elif delta == 1:
            progress.login_streak += 1
            progress.last_action_date = now
            progress = _commit_and_refresh(self.db, progress)

            return self.add_xp(user_id, STREAK_BONUS_XP)

        else:
            progress.login_streak = 1
            progress.last_action_date = now
            progress = _commit_and_refresh(self.db, progress)

            return UserGamificationResponse.model_validate(progress)
