import uuid
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.schema import UserReputation, VerificationTier
from backend.fastapi.app.libs.db_helper import _commit_and_refresh
from backend.fastapi.app.libs.pagination import PaginatedResponse
from backend.fastapi.app.schemas.dtos.user_reputation_dto import UserReputationResponse


class ReputationService:
    def __init__(self, db: Session):
        self.db = db

    # shared
    def get_reputation_by_user_id(self, user_id: uuid.UUID) -> UserReputation:
        rep = (
            self.db.query(UserReputation)
            .filter(UserReputation.user_id == user_id)
            .first()
        )
        if not rep:
            raise HTTPException(status_code=404, detail="Reputation record not found.")
        return rep

    # admin
    def get_reputation(
        self,
        trust_score: Optional[int] = None,
        verification_tier: Optional[VerificationTier] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[UserReputationResponse]:
        query = self.db.query(UserReputation)

        if trust_score is not None:
            query = query.filter(UserReputation.trust_score == trust_score)
        if verification_tier:
            query = query.filter(UserReputation.verification_tier == verification_tier)

        total = query.count()
        reputations = query.offset((page - 1) * page_size).limit(page_size).all()
        return PaginatedResponse[UserReputationResponse](
            total=total,
            page=page,
            page_size=page_size,
            results=[UserReputationResponse.model_validate(r) for r in reputations],
        )

    def update_verification(
        self, user_id: uuid.UUID, tier: VerificationTier
    ) -> UserReputationResponse:
        rep = self.get_reputation_by_user_id(user_id)
        rep.verification_tier = tier
        self._recalculate_trust_score(rep)
        rep = _commit_and_refresh(self.db, rep)
        return UserReputationResponse.model_validate(rep)

    # users
    def create_initial_reputation(self, user_id: str) -> UserReputationResponse:
        new_rep = UserReputation(
            user_id=user_id,
            average_rating=0.0,
            total_reviews=0,
            trust_score=50,
            verification_tier=VerificationTier.UNVERIFIED,
        )
        self.db.add(new_rep)
        new_rep = _commit_and_refresh(self.db, new_rep)
        return UserReputationResponse.model_validate(new_rep)

    def update_rating(
        self, user_id: uuid.UUID, new_rating: float
    ) -> UserReputationResponse:
        if not (0.0 <= new_rating <= 5.0):
            raise ValueError("Rating must be between 0.0 and 5.0.")

        rep = self.get_reputation_by_user_id(user_id)
        current_total_score = rep.average_rating * rep.total_reviews

        rep.total_reviews += 1
        rep.average_rating = (current_total_score + new_rating) / rep.total_reviews

        self._recalculate_trust_score(rep)
        rep = _commit_and_refresh(self.db, rep)

        return UserReputationResponse.model_validate(rep)

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
