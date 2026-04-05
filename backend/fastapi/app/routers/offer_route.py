import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.libs.auth_helper import get_current_user, require_admin
from app.libs.db_helper import get_db
from app.libs.pagination import PaginatedResponse
from app.schemas.schema import User, OfferStatus
from app.schemas.dtos.offer_dto import OfferCreate, OfferResponse
from app.services.user.offer_service import OfferService

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.get("", response_model=PaginatedResponse[OfferResponse])
def get_offers(
    item_id: Optional[int] = None,
    fixer_id: Optional[uuid.UUID] = None,
    status: Optional[OfferStatus] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OfferService(db).get_offers(
        item_id=item_id,
        fixer_id=fixer_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=OfferResponse)
def create_offer(
    offer_data: OfferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if offer_data.fixer_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only create offers for yourself."
        )
    return OfferService(db).create_offer(offer_data)


@router.patch("/{offer_id}/cancel", response_model=OfferResponse)
def cancel_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offer = OfferService(db).get_offers(fixer_id=current_user.id)
    return OfferService(db).cancel_offer(offer_id)


@router.patch("/{offer_id}/accept", response_model=OfferResponse)
def accept_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OfferService(db).accept_offer(offer_id, current_user.id)


@router.patch("/{offer_id}/reject", response_model=OfferResponse)
def reject_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OfferService(db).reject_offer(offer_id)


@router.get("/admin/all", response_model=PaginatedResponse[OfferResponse])
def admin_get_all_offers(
    item_id: Optional[int] = None,
    fixer_id: Optional[uuid.UUID] = None,
    status: Optional[OfferStatus] = None,
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return OfferService(db).get_offers(
        item_id=item_id,
        fixer_id=fixer_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.patch("/admin/{offer_id}/reject", response_model=OfferResponse)
def admin_reject_offer(
    offer_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return OfferService(db).reject_offer(offer_id)
