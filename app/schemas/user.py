from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    mobile: str
    nickname: Optional[str] = None
    source: str
    register_ip: Optional[str] = None
    registered_at: datetime
    last_login_at: Optional[datetime] = None
    balance: float

    class Config:
        orm_mode = True


class UserCreateByAdmin(BaseModel):
    mobile: str
    password: str
    remark: Optional[str] = None


class UserAddressOut(BaseModel):
    id: int
    receiver_name: str
    mobile: str
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    detail_addr: Optional[str] = None
    is_default: bool

    class Config:
        orm_mode = True


class UserDetail(UserBase):
    real_name: Optional[str] = None
    # 简化：只输出尾号与银行名
    bank_cards: list[dict] = []
    addresses: list[UserAddressOut] = []

