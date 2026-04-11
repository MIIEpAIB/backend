from typing import Optional

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    username: str
    password: str
    captcha: str
    # 兼容 v1 文档中的 captcha_key 字段（可选）
    captcha_key: Optional[str] = None


class AdminUserOut(BaseModel):
    id: int
    username: str
    status: int

    class Config:
        orm_mode = True

