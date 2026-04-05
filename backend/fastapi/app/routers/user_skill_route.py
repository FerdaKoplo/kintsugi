from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import annotated_handlers
from sqlalchemy.orm import Session

from backend.fastapi.app.libs.auth_helper import get_current_user, require_admin
from backend.fastapi.app.libs.db_helper import get_db
from backend.fastapi.app.libs.pagination import PaginatedResponse
from backend.fastapi.app.schemas.dtos.user_skill_dto import (
    UserSkillCreate,
    UserSkillResponse,
)
from backend.fastapi.app.schemas.schema import SkillLevel, User, UserVerifyStatus
from backend.fastapi.app.services.user.user_skill_service import UserSkillService


router = APIRouter(prefix="/skill", tags=["Skills"])


@router.get("/me", response_model=PaginatedResponse[UserSkillResponse])
def get_all_user_skills(
    skill_name: Optional[str] = None,
    level: Optional[SkillLevel] = None,
    verified_level: Optional[UserVerifyStatus] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserSkillService(db).get_all_user_skills(
        user_id=current_user.id,
        skill_name=skill_name,
        level=level,
        verified_level=verified_level,
        page=page,
        page_size=page_size,
    )


@router.post("/me", response_model=UserSkillResponse)
def obtain_skill(
    data: UserSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only add skills to your own profile."
        )
    return UserSkillService(db).user_obtain_skill(data)


@router.patch("/me/{skill_id}/progress", response_model=UserSkillResponse)
def update_skill_progress(
    skill_id: int,
    new_level: SkillLevel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = UserSkillService(db).user_skill_progress(
        user_id=current_user.id, skill_id=skill_id, new_level=new_level
    )
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found.")
    return result


@router.get("/me/{skill_id}/check")
def check_has_skill(
    skill_id: int,
    skill_name: Optional[str] = None,
    level: Optional[SkillLevel] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    has = UserSkillService(db).user_has_skill(
        user_id=current_user.id,
        skill_id=skill_id,
        skill_name=skill_name,
        level=level,
    )
    return {"has_skill": has}


# admin


@router.get("/admin/{user_id}", response_model=PaginatedResponse[UserSkillResponse])
def admin_get_user_skills(
    user_id: uuid.UUID,
    skill_name: Optional[str] = None,
    level: Optional[SkillLevel] = None,
    verified_level: Optional[UserVerifyStatus] = None,
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin views any user's skills."""
    return UserSkillService(db).get_all_user_skills(
        user_id=user_id,
        skill_name=skill_name,
        level=level,
        verified_level=verified_level,
        page=page,
        page_size=page_size,
    )


@router.patch("/admin/{skill_id}/verify", response_model=UserSkillResponse)
def admin_verify_skill(
    skill_id: int,
    verified_level: UserVerifyStatus,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    result = UserSkillService(db).verify_user_skill(skill_id, verified_level)
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found.")
    return result
