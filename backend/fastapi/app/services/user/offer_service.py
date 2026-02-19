from gotrue import Optional
from sqlalchemy.orm import Session
from app.schemas.schema import Item, Offer, OfferStatus
from backend.fastapi.app.schemas.dto import OfferCreate
from datetime import datetime, timezone, timedelta


class OfferService:
    def __init__(self, db: Session):
        self.db = db

    def get_offer(self, offer_id: int) -> Optional[Offer]:
        return self.db.query(Offer).filter(Offer.id == offer_id).first()

    def create_offer(self, offer_data: OfferCreate) -> Offer:
        item = self.db.query(Item).filter(Item.id == offer_data.item_id).first()
        if not item:
            raise ValueError("This item is no longer accepting offers.")

        new_offer = Offer(
            item_id=offer_data.item_id,
            fixer_id=offer_data.fixer_id,
            offered_price=offer_data.offered_price,
            message=offer_data.message,
            status=OfferStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(new_offer)
        self.db.commit()
        self.db.refresh(new_offer)
        return new_offer

    def accept_offer(self, offer_id: int) -> Optional[Offer]:
        offer = self.get_offer(offer_id)
        if not offer or offer.status != OfferStatus.PENDING:
            return None

        offer.status = OfferStatus.ACCEPTED

        self.db.query(Offer).filter(
            Offer.item_id == offer.item_id,
            Offer.id != offer_id,
            Offer.status == OfferStatus.PENDING,
        ).update({"status": OfferStatus.REJECTED})

        self.db.commit()
        self.db.refresh(offer)

        return offer

    def reject_offer(self, offer_id) -> Optional[Offer]:
        offer = self.get_offer(offer_id)
        if offer and offer.status == OfferStatus.PENDING:
            offer.status = OfferStatus.REJECTED
            self.db.commit()
            self.db.refresh(offer)
        return offer

    def cancel_offer(self, offer_id) -> Optional[Offer]:
        offer = self.get_offer(offer_id)
        if offer and offer.status == OfferStatus.PENDING:
            offer.status = OfferStatus.WITHDRAWN
            self.db.commit()
            self.db.refresh(offer)
        return offer
