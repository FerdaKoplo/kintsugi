from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    results: List[T]

    model_config = {"from_attributes": True}
