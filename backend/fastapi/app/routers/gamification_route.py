import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.schema import User
from app.schemas.dtos.user_gamification_dto import UserGamificationResponse
from app.libs.auth_helper import get_current_user, require_admin
from app.libs.db_helper import get_db
from app.services.user.gamification_service import GamificationService

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/me", response_model=UserGamificationResponse)
def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GamificationService(db).get_progress(current_user.id)


@router.post("/me/streak", response_model=UserGamificationResponse)
def update_my_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GamificationService(db).update_login_streak(current_user.id)


@router.get("/admin/{user_id}", response_model=UserGamificationResponse)
def admin_get_progress(
    user_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return GamificationService(db).get_progress(user_id)


@router.post("/admin/{user_id}/init", response_model=UserGamificationResponse)
def admin_init_progress(
    user_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return GamificationService(db).create_initial_progress(user_id)


@router.post("/admin/{user_id}/xp", response_model=UserGamificationResponse)
def admin_add_xp(
    user_id: uuid.UUID,
    amount: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return GamificationService(db).add_xp(user_id, amount)
