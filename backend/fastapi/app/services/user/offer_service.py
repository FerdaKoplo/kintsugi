import uuid
from fastapi import HTTPException, status
from gotrue import Optional
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST
from app.schemas.schema import Item, Offer, OfferStatus
from backend.fastapi.app.libs.db_helper import _commit_and_refresh
from backend.fastapi.app.libs.pagination import PaginatedResponse
from backend.fastapi.app.schemas.dtos.offer_dto import OfferResponse, OfferCreate
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError


class OfferService:
    def __init__(self, db: Session):
        self.db = db

    def get_offers(
        self,
        item_id: Optional[int] = None,
        fixer_id: Optional[uuid.UUID] = None,
        status: Optional[OfferStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[OfferResponse]:
        query = self.db.query(Offer)

        if item_id:
            query = query.filter(Offer.item_id == item_id)
        if fixer_id:
            query = query.filter(Offer.fixer_id == fixer_id)
        if status:
            query = query.filter(Offer.status == status)

        total = query.count()
        offers = query.offset((page - 1) * page_size).limit(page_size).all()
        return PaginatedResponse[OfferResponse](
            total=total,
            page=page,
            page_size=page_size,
            results=[OfferResponse.model_validate(o) for o in offers],
        )

    def _get_pending_offer(self, offer_id: int) -> Offer:
        offer = self.db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found.")
        if offer.status != OfferStatus.PENDING:
            raise HTTPException(
                status_code=400, detail=f"Offer is already {offer.status.value}."
            )
        return offer

    def create_offer(self, offer_data: OfferCreate) -> OfferResponse:
        item = self.db.query(Item).filter(Item.id == offer_data.item_id).first()
        if not item:
            raise ValueError("This item is no longer accepting offers.")

        offer = Offer(
            item_id=offer_data.item_id,
            fixer_id=offer_data.fixer_id,
            price_bid=offer_data.price_bid,
            status=OfferStatus.PENDING,
        )

        self.db.add(offer)
        offer = _commit_and_refresh(self.db, offer)
        return OfferResponse.model_validate(offer)

    def accept_offer(self, offer_id: int) -> OfferResponse:
        offer = self._get_pending_offer(offer_id)
        offer.status = OfferStatus.ACCEPTED

        self.db.query(Offer).filter(
            Offer.item_id == offer.item_id,
            Offer.id != offer_id,
            Offer.status == OfferStatus.PENDING,
        ).update({"status": OfferStatus.REJECTED})

        offer = _commit_and_refresh(self.db, offer)
        return OfferResponse.model_validate(offer)

    def reject_offer(self, offer_id) -> OfferResponse:
        offer = self._get_pending_offer(offer_id)
        offer.status = OfferStatus.REJECTED
        offer = _commit_and_refresh(self.db, offer)
        return OfferResponse.model_validate(offer)

    def cancel_offer(self, offer_id) -> OfferResponse:
        offer = self._get_pending_offer(offer_id)
        offer.status = OfferStatus.WITHDRAWN
        offer = _commit_and_refresh(self.db, offer)
        return OfferResponse.model_validate(offer)
