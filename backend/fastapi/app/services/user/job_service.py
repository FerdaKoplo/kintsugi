from datetime import datetime, timezone, timedelta
import uuid
from fastapi import HTTPException, status
from gotrue import Optional
from sqlalchemy import exists
from sqlalchemy.orm import Session
from app.schemas.schema import Item, ItemStatus, Job, JobStatus
from backend.fastapi.app.libs.db_helper import _commit_and_refresh
from backend.fastapi.app.libs.pagination import PaginatedResponse
from backend.fastapi.app.schemas.dtos.job_dto import JobCreate, JobResponse
from backend.fastapi.app.services.user.badge_service import BadgeService
from sqlalchemy.exc import IntegrityError


class JobService:
    def __init__(self, db: Session):
        self.db = db

    # shared
    def get_jobs(
        self,
        client_id: Optional[uuid.UUID] = None,
        fixer_id: Optional[uuid.UUID] = None,
        status: Optional[JobStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[JobResponse]:
        query = self.db.query(Job)

        if client_id:
            query = query.filter(Job.client_id == client_id)
        if fixer_id:
            query = query.filter(Job.fixer_id == fixer_id)
        if status:
            query = query.filter(Job.status == status)

        total = query.count()
        offers = query.offset((page - 1) * page_size).limit(page_size).all()
        return PaginatedResponse[JobResponse](
            total=total,
            page=page,
            page_size=page_size,
            results=[JobResponse.model_validate(o) for o in offers],
        )

    def has_active_job(self, fixer_id: uuid.UUID, client_id=uuid.UUID) -> bool:
        count = (
            self.db.query(Job)
            .filter(
                Job.fixer_id == fixer_id,
                Job.client_id == client_id,
                Job.status.in_([JobStatus.ACTIVE, JobStatus.DISPUTED]),
            )
            .count()
        )
        return count > 0

    def get_job_by_id(self, job_id) -> Job:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        return job

    # all user
    def create_job(self, job_data: JobCreate) -> JobResponse:
        item = self.db.query(Item).filter(Item.id == job_data.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found.")
        new_job = Job(
            item_id=job_data.item_id,
            client_id=job_data.client_id,
            fixer_id=job_data.fixer_id,
            agreed_price=job_data.agreed_price,
            status=JobStatus.ACTIVE,
        )

        self.db.add(new_job)

        new_job = _commit_and_refresh(self.db, new_job)
        return JobResponse.model_validate(new_job)

    def update_job_status(self, job_id: int, new_status: JobStatus) -> JobResponse:
        job = self.get_job_by_id(job_id)
        job.status = new_status
        job = _commit_and_refresh(self.db, job)
        return JobResponse.model_validate(job)

    def complete_job(self, job_id: int, fixer_id: str) -> JobResponse:
        job = self.get_job_by_id(job_id)

        if job.fixer_id != fixer_id:
            raise HTTPException(
                status_code=403, detail="Only the assigned fixer can complete this job."
            )

        if job.status != JobStatus.ACTIVE:
            raise HTTPException(
                status_code=400, detail=f"Job is already {job.status.value}."
            )

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)

        if job.item:
            job.item.status = ItemStatus.FIXED

        job_count = (
            self.db.query(Job)
            .filter(
                Job.fixer_id == fixer_id,
                Job.status == JobStatus.COMPLETED,
            )
            .count()
        )

        if job_count == 0:
            BadgeService(self.db).award_badge(
                user_id=fixer_id,
                badge_name="First Fix",
                badge_slug="first-fix",
            )

        job = _commit_and_refresh(self.db, job)
        return JobResponse.model_validate(job)
