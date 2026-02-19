from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from gotrue import Optional
from sqlalchemy import exists
from sqlalchemy.orm import Session
from app.schemas.schema import Item, ItemStatus, Job, JobStatus
from backend.fastapi.app.schemas.dto import JobCreate
from backend.fastapi.app.services.user.badge_service import BadgeService


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_job(self, job_id: int) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def has_active_job(self, fixer_id: str, client_id) -> bool:
        stmt = exists().where(
            (Job.fixer_id == fixer_id)
            & (
                Job.client_id == client_id,
                Job.status.in_([JobStatus.ACTIVE, JobStatus.DISPUTED]),
            )
        )

        return self.db.query(stmt).scalar()

    def get_job_by_id(self, job_id) -> Job:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        return job

    def create_job(self, job_data: JobCreate) -> Job:
        new_job = Job(
            item_id=job_data.item_id,
            client_id=job_data.client_id,
            fixer_id=job_data.fixer_id,
            agreed_price=job_data.agreed_price,
            status=JobStatus.ACTIVE,
            started_at=datetime.now(timezone.utc),
        )

        self.db.add(new_job)

        item = self.db.query(Item).filter(Item.id == job_data.item_id).first()

        if item:
            item.status = ItemStatus.IN_PROGRESS

        self.db.commit()
        self.db.refresh(new_job)
        return new_job

    def update_job_status(self, job_id: int, new_status: JobStatus) -> Optional[Job]:
        job = self.get_job(job_id)

        if not job:
            return None

        job.status = new_status
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete_job(self, job_id: int, fixer_id: str) -> Optional[Job]:
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)

        if job.item:
            job.item.status = ItemStatus.FIXED

        job_count = self.db.query(Job).filter(Job.fixer_id == fixer_id).count()

        if job_count == 1:
            badge_service = BadgeService(self.db)
            badge_service.award_badge(
                user_id=fixer_id, badge_name="First Fix", badge_slug="first-fix"
            )

        self.db.commit()
        self.db.refresh(job)
        return job
