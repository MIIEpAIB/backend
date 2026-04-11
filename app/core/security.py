from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db import models
from backend.app.db.database import get_db


# 这里使用 pbkdf2_sha256 避免 bcrypt 72 字节限制和底层自检问题
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

settings = get_settings()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def get_current_admin(
    token: str = Depends(oauth2_scheme_admin),
    db: Session = Depends(get_db),
) -> models.AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        sub = payload.get("sub")
        admin_id: int | None
        if sub is None:
            raise credentials_exception
        if isinstance(sub, int):
            admin_id = sub
        elif isinstance(sub, str) and sub.isdigit():
            admin_id = int(sub)
        else:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = db.get(models.AdminUser, admin_id)
    if admin is None or admin.status != 1:
        raise credentials_exception
    return admin

