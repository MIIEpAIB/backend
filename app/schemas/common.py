from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "ok"
    data: Optional[T] = None


class PageMeta(BaseModel):
    total: int


class PageResult(BaseModel):
    total: int
    list: list[Any]


class AdminTokenData(BaseModel):
    token: str
    admin_id: int
    username: str
    roles: list[str] = []


class DatetimeModel(BaseModel):
    created_at: datetime

