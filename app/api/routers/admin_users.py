from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin, get_password_hash
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse
from backend.app.schemas.user import UserBase, UserCreateByAdmin, UserDetail


router = APIRouter(prefix="/api/admin/users", tags=["AdminUser"])


@router.get("", response_model=APIResponse[dict])
def list_users(
    mobile: str | None = Query(None),
    source: str | None = Query(None),
    registered_from: str | None = Query(None),
    registered_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.User)
    if mobile:
        q = q.filter(models.User.mobile.like(f"%{mobile}%"))
    if source in ("portal", "backend"):
        q = q.filter(models.User.source == source)
    # 时间筛选可按需要转换为 datetime，这里简单略过
    total = q.count()
    items = (
        q.order_by(models.User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = {
        "total": total,
        "list": [UserBase.from_orm(u).dict() for u in items],
    }
    return APIResponse[dict](code=0, msg="ok", data=data)


@router.post("", response_model=APIResponse[dict])
def create_user_by_admin(
    payload: UserCreateByAdmin,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    exists = db.query(models.User).filter_by(mobile=payload.mobile).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="mobile exists"
        )
    user = models.User(
        mobile=payload.mobile,
        password_hash=get_password_hash(payload.password),
        source=models.UserSource.backend,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return APIResponse[dict](code=0, msg="ok", data={"id": user.id})


@router.get("/{user_id}", response_model=APIResponse[UserDetail])
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    addrs = (
        db.query(models.UserAddress)
        .filter(models.UserAddress.user_id == user.id)
        .all()
    )
    detail = UserDetail(
        **UserBase.from_orm(user).dict(),
        real_name=user.real_name,
        bank_cards=[],
        addresses=addrs,
    )
    return APIResponse[UserDetail](code=0, msg="ok", data=detail)


@router.put("/{user_id}/password", response_model=APIResponse[Any])
def reset_user_password(
    user_id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    new_password = body.get("new_password")
    if not new_password:
        raise HTTPException(status_code=400, detail="new_password required")
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    db.commit()
    return APIResponse[Any](code=0, msg="ok", data=None)

