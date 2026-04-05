import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.libs.auth_helper import get_current_user, require_admin
from app.libs.db_helper import get_db
from app.libs.pagination import PaginatedResponse
from app.schemas.schema import User, JobStatus
from app.schemas.dtos.job_dto import JobCreate, JobResponse
from app.services.user.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=PaginatedResponse[JobResponse])
def get_jobs(
    client_id: Optional[uuid.UUID] = None,
    fixer_id: Optional[uuid.UUID] = None,
    status: Optional[JobStatus] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get jobs filtered by client or fixer — each user sees only their own jobs."""
    return JobService(db).get_jobs(
        client_id=client_id,
        fixer_id=fixer_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job_by_id(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return JobService(db).get_job_by_id(job_id)


# ── Client ─────────────────────────────────────────────────────────────────────


@router.post("", response_model=JobResponse)
def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Client creates a job after accepting an offer."""
    if job_data.client_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only create jobs for yourself."
        )
    return JobService(db).create_job(job_data)


@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: int,
    new_status: JobStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Client updates job status (e.g. mark as disputed)."""
    job = JobService(db).get_job_by_id(job_id)
    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the client can update this job."
        )
    return JobService(db).update_job_status(job_id, new_status)


@router.patch("/{job_id}/complete", response_model=JobResponse)
def complete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return JobService(db).complete_job(job_id, current_user.id)


@router.patch("/admin/{job_id}/status", response_model=JobResponse)
def admin_update_job_status(
    job_id: int,
    new_status: JobStatus,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return JobService(db).update_job_status(job_id, new_status)
