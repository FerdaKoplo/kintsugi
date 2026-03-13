from typing import TypeVar
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


def _commit_and_refresh(self, obj: T) -> T:
    try:
        self.db.commit()
        self.db.refresh(obj)
        return obj
    except IntegrityError:
        self.db.rollback()
        raise HTTPException(
            status_code=400, detail="Invalid reference — check foreign key constraints."
        )
    except Exception:
        self.db.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
