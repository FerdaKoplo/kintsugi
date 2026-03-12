import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.fastapi.app.schemas.dtos.user_skill_dto import (
    UserSkillCreate,
    UserSkillResponse,
)
from backend.fastapi.app.schemas.schema import SkillLevel, UserSkill, UserVerifyStatus


class UserSkillService:
    def __init__(self, db: Session):
        self.db = db

    "Admin"

    def get_all_user_skills(
        self,
        user_id: uuid.UUID,
        skill_name: Optional[str] = None,
        level: Optional[SkillLevel] = None,
        verified_level: Optional[UserVerifyStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = self.db.query(UserSkill).filter(UserSkill.user_id == user_id)
        if skill_name:
            query = query.filter(UserSkill.skill_name.ilike(f"%{skill_name}%"))
        if level:
            query = query.filter(UserSkill.level == level)
        if verified_level:
            query = query.filter(UserSkill.verified_level == verified_level)

        total = query.count()
        skills = query.offset((page - 1) * page_size).limit(page_size).all()

        return {"total": total, "page": page, "page_size": page_size, "results": skills}

    def verify_user_skill(self, skill_id: int, verified_level: UserVerifyStatus):
        skill = self.db.query(UserSkill).filter(UserSkill.id == skill_id).first()
        if not skill:
            return None

        skill.verified_level = verified_level
        self.db.commit()
        self.db.refresh(skill)
        return UserSkillResponse.model_validate(skill)

    "User"

    def user_has_skill(
        self,
        user_id: uuid.UUID,
        skill_id: int,
        skill_name: Optional[str] = None,
        level: Optional[SkillLevel] = None,
        verified_level: Optional[UserVerifyStatus] = None,
    ) -> bool:
        query = self.db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.id == skill_id,
        )

        if skill_name:
            query = query.filter(UserSkill.skill_name.ilike(skill_name))
        if level:
            query = query.filter(UserSkill.level == level)
        if verified_level:
            query = query.filter(UserSkill.verified_level == verified_level)
        return query.count() > 0

    def user_obtain_skill(self, data: UserSkillCreate) -> UserSkillResponse:
        existing = (
            self.db.query(UserSkill)
            .filter(
                UserSkill.user_id == data.user_id,
                UserSkill.skill_name.ilike(data.skill_name),
            )
            .first()
        )
        if existing:
            raise ValueError(f"Skill '{data.skill_name}' already exists for this user.")

        skill = UserSkill(
            user_id=data.user_id,
            skill_name=data.skill_name,
            level=data.level,
            verified_level=UserVerifyStatus.UNVERIFIED,
        )

        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return UserSkillResponse.model_validate(skill)

    def user_skill_progress(
        self, user_id: uuid.UUID, skill_id: int, new_level: SkillLevel
    ) -> Optional[UserSkillResponse]:
        skill = (
            self.db.query(UserSkill)
            .filter(UserSkill.id == skill_id, UserSkill.user_id == user_id)
            .first()
        )
        if not skill:
            return None

        level_order = [
            SkillLevel.BEGINNER,
            SkillLevel.INTERMEDIATE,
            SkillLevel.EXPERT,
        ]
        if level_order.index(new_level) < level_order.index(skill.level):
            raise ValueError(
                f"Cannot downgrade skill level from {skill.level} to {new_level}."
            )

        skill.level = new_level
        skill.verified_level = UserVerifyStatus.UNVERIFIED
        self.db.commit()
        self.db.refresh(skill)
        return UserSkillResponse.model_validate(skill)
