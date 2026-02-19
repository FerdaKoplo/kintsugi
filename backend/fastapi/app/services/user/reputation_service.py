from os.path import expanduser
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.schema import UserReputation, User, VerificationTier, Review


class ReputationService:
    def __init__(self, db: Session):
        self.db = db

    def get_reputation(self, user_id: str) -> UserReputation:
        rep = (
            self.db.query(UserReputation)
            .filter(UserReputation.user_id == user_id)
            .first()
        )
        if not rep:
            rep = self.create_initial_reputation(user_id)
        return rep

    def create_initial_reputation(self, user_id: str) -> UserReputation:
        new_rep = UserReputation(
            user_id=user_id,
            average_rating=0.0,
            total_reviews=0,
            trust_score=50,
            verification_tier=VerificationTier.UNVERIFIED,
        )
        self.db.add(new_rep)
        self.db.commit()
        self.db.refresh(new_rep)
        return new_rep

    def update_rating(self, user_id: str, new_rating: int):
        rep = self.get_reputation(user_id)

        current_total_score = rep.average_rating * rep.total_reviews
        rep.total_reviews += 1
        rep.average_rating = (current_total_score + new_rating) / rep.total_reviews

        self._recalculate_trust_score(rep)

        self.db.commit()
        self.db.refresh(rep)
        return rep

    def update_verification(self, user_id: str, tier: VerificationTier):
        rep = self.get_reputation(user_id)
        rep.verification_tier = tier

        self._recalculate_trust_score(rep)

        self.db.commit()
        self.db.refresh(rep)
        return rep

    def _recalculate_trust_score(self, rep: UserReputation):
        score = 50

        if rep.verification_tier == VerificationTier.EMAIL_ONLY:
            score += 5

        elif rep.verification_tier == VerificationTier.PHONE_VERIFIED:
            score += 15

        elif rep.verification_tier == VerificationTier.GOV_ID_VERIFIED:
            score += 30

        if rep.total_reviews > 0:
            if rep.average_rating >= 4.5:
                score += 20
            elif rep.average_rating >= 4.0:
                score += 10
            elif rep.average_rating < 3.0:
                score -= 10

        experience_bonus = min(rep.total_reviews, 50) * 0.2
        score += int(experience_bonus)

        rep.trust_score = max(0, min(100, score))
