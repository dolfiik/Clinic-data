from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

DataT = TypeVar('DataT')

class PaginatedResponse(BaseModel, Generic[DataT]):
    items: List[DataT]
    total: int
    page: int
    size: int
    pages: int

class MessageResponse(BaseModel):
    message: str
    success: bool = True
