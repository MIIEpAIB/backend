"""移动端接口公共依赖（鉴权等）"""

from fastapi import Header, HTTPException
from jose import JWTError, jwt

from backend.app.core.config import get_settings

settings = get_settings()


def mobile_user_id_from_header(authorization: str | None = Header(None)) -> int:
    """从 Authorization: Bearer <JWT> 解析用户 id（sub）。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub = payload.get("sub")
        if isinstance(sub, int):
            return sub
        if isinstance(sub, str) and sub.isdigit():
            return int(sub)
    except JWTError:
        pass
    raise HTTPException(status_code=401, detail="登录已失效")
