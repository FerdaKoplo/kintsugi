from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.libs.auth_helper import get_current_user
from app.libs.db_helper import get_db
from app.schemas.schema import User
from app.services.ai.logic_diagnosis import LogicDiagnosisService
from app.services.ai.skill_matching import SkillMatchingService
from app.services.ai.visual_diagnosis import VisualDiagnosisService


router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])

logic_service = LogicDiagnosisService()


@router.post("/visual")
async def visual_diagnosis(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an image to diagnose visible damage."""
    image_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"
    return VisualDiagnosisService().diagnose(image_bytes, mime_type)


@router.post("/audio")
async def audio_diagnosis(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    audio_bytes = await file.read()
    return VisualDiagnosisService().diagnose(audio_bytes)


@router.post("/logic/start")
def start_logic_diagnosis(
    session_id: str,
    item_description: str,
    current_user: User = Depends(get_current_user),
):
    """Start a diagnostic chat session for invisible issues."""
    return logic_service.start_diagnosis(
        session_id=session_id,
        item_description=item_description,
    )


@router.post("/logic/continue")
def continue_logic_diagnosis(
    session_id: str,
    user_answer: str,
    current_user: User = Depends(get_current_user),
):
    """Continue an existing diagnostic chat session."""
    return logic_service.continue_diagnosis(
        session_id=session_id,
        user_answer=user_answer,
    )


@router.delete("/logic/{session_id}")
def clear_logic_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Clear a diagnostic session manually."""
    logic_service.clear_session(session_id)
    return {"message": f"Session '{session_id}' cleared."}


@router.get("/match")
def match_fixers(
    required_skill: str,
    client_lat: float,
    client_lng: float,
    radius_km: float = 5.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Match nearby verified fixers based on required skill and location."""
    return SkillMatchingService(db).match_fixers(
        required_skill=required_skill,
        client_lat=client_lat,
        client_lng=client_lng,
        radius_km=radius_km,
    )
