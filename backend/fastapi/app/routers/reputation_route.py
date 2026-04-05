import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.libs.auth_helper import get_current_user, require_admin
from app.libs.db_helper import get_db
from app.libs.pagination import PaginatedResponse
from app.schemas.schema import User, VerificationTier
from app.schemas.dtos.user_reputation_dto import UserReputationResponse
from app.services.user.reputation_service import ReputationService

router = APIRouter(prefix="/reputation", tags=["Reputation"])


@router.get("/me", response_model=UserReputationResponse)
def get_my_reputation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReputationService(db).get_reputation_by_user_id(current_user.id)


@router.get("/{user_id}", response_model=UserReputationResponse)
def get_user_reputation(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReputationService(db).get_reputation_by_user_id(user_id)


@router.get("/admin/all", response_model=PaginatedResponse[UserReputationResponse])
def admin_get_all_reputations(
    trust_score: Optional[int] = None,
    verification_tier: Optional[VerificationTier] = None,
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ReputationService(db).get_reputation(
        trust_score=trust_score,
        verification_tier=verification_tier,
        page=page,
        page_size=page_size,
    )


@router.patch("/admin/{user_id}/verify", response_model=UserReputationResponse)
def admin_update_verification(
    user_id: uuid.UUID,
    tier: VerificationTier,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ReputationService(db).update_verification(user_id, tier)


@router.post("/admin/{user_id}/init", response_model=UserReputationResponse)
def admin_init_reputation(
    user_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ReputationService(db).create_initial_reputation(user_id)
