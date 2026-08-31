import math
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    status: str = Field(default="success", description="Status string: success or error")
    message: Optional[str] = Field(default=None, description="Descriptive response message")
    data: Optional[T] = Field(default=None, description="Payload data")


class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")
    has_next: bool = Field(default=False, description="Whether there is a next page")
    has_previous: bool = Field(default=False, description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    status: str = Field(default="success")
    data: List[T] = Field(default_factory=list, description="List of items on the current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    message: Optional[str] = None

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
        message: Optional[str] = None,
    ) -> "PaginatedResponse[T]":
        total_pages = math.ceil(total / page_size) if page_size > 0 else 1
        meta = PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )
        return cls(status="success", data=items, pagination=meta, message=message)


class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    message: str = Field(..., description="Error summary or reason")
    errors: Optional[Any] = Field(default=None, description="Detailed validation or exception breakdown")
