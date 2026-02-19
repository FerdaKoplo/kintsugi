from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.schemas.schema import UserGamification


XP_PER_LEVEL_BASE = 100
STREAK_BONUS_XP = 10


class GamificationService:
    def __init__(self, db: Session):
        self.db = db

    def get_progress(self, user_id: str) -> UserGamification:
        progress = (
            self.db.query(UserGamification)
            .filter(UserGamification.user_id == user_id)
            .first()
        )
        if not progress:
            progress = UserGamification(
                user_id=user_id,
                current_xp=0,
                current_level=1,
                login_streak=0,
                last_action_date=datetime.now(timezone.utc),
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)
        return progress

    def add_xp(self, user_id: str, amount: int) -> dict:
        progress = self.get_progress(user_id)
        progress.current_xp += amount

        xp_needed = progress.current_level * XP_PER_LEVEL_BASE

        leveled_up = False
        while progress.current_xp >= xp_needed:
            progress.current_xp -= xp_needed
            progress.current_level += 1
            xp_needed = progress.current_level * XP_PER_LEVEL_BASE
            leveled_up = True

        self.db.commit()
        self.db.refresh(progress)

        return {
            "leveled_up": leveled_up,
            "new_level": progress.current_level,
            "current_xp": progress.current_xp,
        }

    def update_login_streak(self, user_id: str) -> int:
        progress = self.get_progress(user_id)
        now = datetime.now(timezone.utc)

        if not progress.last_action_date:
            progress.last_action_date = now
            progress.login_streak = 1
            self.db.commit()
            return 1

        last_date = progress.last_action_date.date()
        today = now.date()

        delta = (today - last_date).days

        if delta == 1:
            progress.login_streak += 1
            self.add_xp(user_id, STREAK_BONUS_XP)

        elif delta > 1:
            progress.login_streak = 1

        progress.last_action_date = now
        self.db.commit()
        return progress.login_streak
