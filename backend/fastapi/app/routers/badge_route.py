from typing import List
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.libs.auth_helper import get_current_user, require_admin
from app.libs.db_helper import get_db
from app.schemas.dtos.badge_dto import UserBadgeResponse
from app.schemas.schema import User
from app.services.user.badge_service import BadgeService


router = APIRouter(prefix="/badges", tags=["Badges"])


@router.get("/me", response_model=List[UserBadgeResponse])
def get_my_badge(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return BadgeService(db).get_user_badges(current_user.id)


@router.get("/{user_id}", response_model=List[UserBadgeResponse])
def get_user_badges(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BadgeService(db).get_user_badges(user_id)


@router.get("/admin/all", response_model=List[UserBadgeResponse])
def get_all_distributed_badges(
    skip: int = 0,
    limit: int = 20,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return BadgeService(db).get_all_distributed_badges(skip=skip, limit=limit)


@router.post("/admin/{user_id}/award", response_model=UserBadgeResponse)
def award_badge(
    user_id: uuid.UUID,
    badge_name: str,
    badge_slug: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return BadgeService(db).award_badge(
        user_id=user_id,
        badge_name=badge_name,
        badge_slug=badge_slug,
    )


@router.delete("/admin/{user_id}/revoke/{badge_slug}")
def revoke_badge(
    user_id: uuid.UUID,
    badge_slug: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return BadgeService(db).revoke_badge(user_id=user_id, badge_slug=badge_slug)
