"""v1 用户与资金：/api/user/* 及充值、账变"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin, get_password_hash
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/user", tags=["User"])


def _source_label(s):
    return "平台注册" if str(s) == "portal" else "后台创建"


@router.get("/list", response_model=APIResponse[dict])
def user_list(
    user_account: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.User)
    if user_account:
        q = q.filter(models.User.mobile.like(f"%{user_account}%"))
    if start_date:
        try:
            q = q.filter(models.User.registered_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.User.registered_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.User.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = []
    for u in rows:
        list_.append({
            "id": u.id,
            "user_account": u.mobile,
            "nickname": u.nickname or "",
            "balance": float(u.balance or 0),
            "source": _source_label(u.source),
            "created_at": u.registered_at.strftime("%Y-%m-%d %H:%M:%S") if u.registered_at else "",
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class UserAddBody(BaseModel):
    user_account: str
    nickname: str = ""
    password: str


@router.post("/add", response_model=APIResponse[dict])
def user_add(
    body: UserAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    if db.query(models.User).filter(models.User.mobile == body.user_account).first():
        raise HTTPException(400, "账号已存在")
    u = models.User(
        mobile=body.user_account,
        nickname=body.nickname or None,
        password_hash=get_password_hash(body.password),
        source=models.UserSource.backend,
    )
    db.add(u)
    db.commit()
    return APIResponse[dict](code=0, msg="创建成功", data=None)


@router.get("/detail", response_model=APIResponse[dict])
def user_detail(
    user_id: int = Query(..., alias="user_id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    u = db.get(models.User, user_id)
    if not u:
        raise HTTPException(404, "用户不存在")
    addrs = db.query(models.UserAddress).filter(models.UserAddress.user_id == u.id).all()
    addresses = [{"receiver": a.receiver_name, "phone": a.mobile, "detail": (a.province or "") + (a.city or "") + (a.district or "") + (a.detail_addr or "")} for a in addrs]
    return APIResponse[dict](code=0, msg="ok", data={
        "id": u.id,
        "user_account": u.mobile,
        "nickname": u.nickname or "",
        "balance": float(u.balance or 0),
        "source": _source_label(u.source),
        "created_at": u.registered_at.strftime("%Y-%m-%d %H:%M:%S") if u.registered_at else "",
        "register_ip": u.register_ip or "",
        "last_login_at": u.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if u.last_login_at else "",
        "cards": [],
        "addresses": addresses,
    })


class UserEditBody(BaseModel):
    user_id: int
    new_password: str


@router.post("/edit", response_model=APIResponse[dict])
def user_edit(
    body: UserEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    u = db.get(models.User, body.user_id)
    if not u:
        raise HTTPException(404, "用户不存在")
    u.password_hash = get_password_hash(body.new_password)
    db.commit()
    return APIResponse[dict](code=0, msg="密码修改成功", data=None)


# ---------- 充值记录 ----------
@router.get("/recharge/list", response_model=APIResponse[dict])
def recharge_list(
    user_account: str | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.RechargeOrder).join(models.User, models.RechargeOrder.user_id == models.User.id)
    if user_account:
        q = q.filter(models.User.mobile.like(f"%{user_account}%"))
    if status and status != "all":
        if status == "success":
            q = q.filter(models.RechargeOrder.status == "success")
        elif status == "failed":
            q = q.filter(models.RechargeOrder.status == "failed")
        elif status == "pending":
            q = q.filter(models.RechargeOrder.status == "pending")
    if start_date:
        try:
            q = q.filter(models.RechargeOrder.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.RechargeOrder.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.RechargeOrder.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    status_map = {"success": "已成功", "failed": "已失败", "pending": "处理中"}
    pay_map = {"wechat": "微信支付", "alipay": "支付宝支付", "card": "信用卡"}
    list_ = []
    for r in rows:
        user = db.get(models.User, r.user_id)
        list_.append({
            "id": r.id,
            "user_account": user.mobile if user else "",
            "recharge_time": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            "amount": float(r.amount),
            "status": status_map.get(r.status, r.status),
            "pay_method": pay_map.get(r.pay_method, r.pay_method or "微信支付"),
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class RechargeConfirmBody(BaseModel):
    recharge_id: int


@router.post("/recharge/confirm", response_model=APIResponse[dict])
def recharge_confirm(
    body: RechargeConfirmBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.RechargeOrder, body.recharge_id)
    if not r:
        raise HTTPException(404, "充值记录不存在")
    if r.status != "pending":
        raise HTTPException(400, "仅处理中的订单可确认")
    from sqlalchemy import func
    user = db.get(models.User, r.user_id)
    if user:
        before = float(user.balance or 0)
        user.balance = before + float(r.amount)
        db.add(models.BalanceLog(user_id=user.id, type="recharge", amount_change=float(r.amount), balance_before=before, balance_after=float(user.balance), ref_type="recharge_order", ref_id=r.id))
    r.status = "success"
    db.commit()
    return APIResponse[dict](code=0, msg="确认成功，余额已增加", data=None)


@router.post("/recharge/cancel", response_model=APIResponse[dict])
def recharge_cancel(
    body: RechargeConfirmBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.RechargeOrder, body.recharge_id)
    if not r:
        raise HTTPException(404, "充值记录不存在")
    if r.status != "pending":
        raise HTTPException(400, "仅处理中的订单可取消")
    r.status = "failed"
    db.commit()
    return APIResponse[dict](code=0, msg="已取消", data=None)


# ---------- 账变记录 ----------
@router.get("/balance-log/list", response_model=APIResponse[dict])
def balance_log_list(
    user_account: str | None = Query(None),
    type: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.BalanceLog).join(models.User, models.BalanceLog.user_id == models.User.id)
    if user_account:
        q = q.filter(models.User.mobile.like(f"%{user_account}%"))
    if type:
        if type == "recharge":
            q = q.filter(models.BalanceLog.type == "recharge")
        elif type == "purchase":
            q = q.filter(models.BalanceLog.type.in_(["order", "purchase"]))
        elif type == "sacrifice":
            q = q.filter(models.BalanceLog.type == "sacrifice")
        elif type == "blessing":
            q = q.filter(models.BalanceLog.type == "blessing")
    if start_date:
        try:
            q = q.filter(models.BalanceLog.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.BalanceLog.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.BalanceLog.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    type_label = {"recharge": "充值", "order": "购买商品", "purchase": "购买商品", "sacrifice": "网上祭祀", "blessing": "网上祈福"}
    list_ = []
    for r in rows:
        user = db.get(models.User, r.user_id)
        list_.append({
            "id": r.id,
            "user_account": user.mobile if user else "",
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            "type": type_label.get(r.type, r.type),
            "before_balance": float(r.balance_before),
            "change_amount": float(r.amount_change),
            "after_balance": float(r.balance_after),
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class UserPasswordEditBody(BaseModel):
    user_id: int
    new_password: str


@router.post("/password/edit", response_model=APIResponse[dict])
def user_password_edit(
    body: UserPasswordEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    u = db.get(models.User, body.user_id)
    if not u:
        raise HTTPException(404, "用户不存在")
    u.password_hash = get_password_hash(body.new_password)
    db.commit()
    return APIResponse[dict](code=0, msg="密码修改成功", data=None)
