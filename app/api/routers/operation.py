"""运营管理：收款码、首页分类、轮播图、专家联系方式、虚拟币汇率"""
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/operation", tags=["Operation"])

PAY_TYPE_NAMES = {"wechat": "微信支付", "alipay": "支付宝"}
CONTACT_TYPE_NAMES = {
    "qq": "QQ",
    "wechat": "微信",
    "phone": "电话",
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
}


# ---------- 收款码 ----------
@router.get("/payment-qrcode/list", response_model=APIResponse[list])
def payment_qrcode_list(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    rows = db.query(models.PayQr).order_by(models.PayQr.id).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "pay_type": r.pay_method,
            "pay_type_name": PAY_TYPE_NAMES.get(r.pay_method, r.pay_method),
            "qrcode_url": r.image_url or "",
            "status": getattr(r, "status", 1),
        })
    if not out:
        out = [
            {"id": 1, "pay_type": "wechat", "pay_type_name": "微信支付", "qrcode_url": "", "status": 1},
            {"id": 2, "pay_type": "alipay", "pay_type_name": "支付宝", "qrcode_url": "", "status": 0},
        ]
    return APIResponse[list](code=0, msg="ok", data=out)


class PaymentQrcodeSaveItem(BaseModel):
    id: int
    pay_type: str
    qrcode_url: str = ""
    status: int = 1


class PaymentQrcodeSaveBody(BaseModel):
    list: list[PaymentQrcodeSaveItem]


@router.post("/payment-qrcode/save", response_model=APIResponse[Any])
def payment_qrcode_save(
    body: PaymentQrcodeSaveBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    for item in body.list:
        q = db.query(models.PayQr).filter(models.PayQr.id == item.id).first()
        if q:
            q.pay_method = item.pay_type
            q.image_url = item.qrcode_url or ""
            q.status = item.status
        else:
            db.add(models.PayQr(pay_method=item.pay_type, image_url=item.qrcode_url or "", status=item.status))
    db.commit()
    return APIResponse[Any](code=0, msg="ok", data=None)


# ---------- 首页分类（3 个固定分类名）----------
@router.get("/home-category/detail", response_model=APIResponse[dict])
def home_category_detail(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    sections = db.query(models.HomeSection).order_by(models.HomeSection.sort_order).limit(3).all()
    data = {
        "category1_name": "热门商品",
        "category2_name": "转运法宝",
        "category3_name": "守护平安",
    }
    keys = ["category1_name", "category2_name", "category3_name"]
    for i, s in enumerate(sections):
        if i < 3 and s.key_name in keys:
            data[s.key_name] = s.title
    return APIResponse[dict](code=0, msg="ok", data=data)


class HomeCategorySaveBody(BaseModel):
    category1_name: str
    category2_name: str
    category3_name: str


@router.post("/home-category/save", response_model=APIResponse[Any])
def home_category_save(
    body: HomeCategorySaveBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    for i, key in enumerate(["category1_name", "category2_name", "category3_name"]):
        name = getattr(body, key, "")
        section = db.query(models.HomeSection).filter(models.HomeSection.key_name == key).first()
        if section:
            section.title = name
        else:
            db.add(models.HomeSection(key_name=key, title=name, sort_order=i + 1))
    db.commit()
    return APIResponse[Any](code=0, msg="保存成功", data=None)


# ---------- 轮播图 ----------
@router.get("/banner/list", response_model=APIResponse[dict])
def banner_list(
    title: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.HomeBanner)
    if title:
        q = q.filter(models.HomeBanner.title.like(f"%{title}%"))
    if start_date:
        try:
            q = q.filter(models.HomeBanner.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.HomeBanner.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    q = q.order_by(models.HomeBanner.sort_order, models.HomeBanner.id)
    total = q.count()
    rows = q.offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = []
    for r in rows:
        list_.append({
            "id": r.id,
            "title": getattr(r, "title", "") or "",
            "image_url": r.image_url,
            "sort": r.sort_order,
            "link_url": r.link_url or "",
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class BannerAddBody(BaseModel):
    title: str = ""
    image_url: str
    sort: int = 0
    link_url: str = ""


@router.post("/banner/add", response_model=APIResponse[Any])
def banner_add(
    body: BannerAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    b = models.HomeBanner(
        title=body.title,
        image_url=body.image_url,
        link_type="external",
        link_url=body.link_url or None,
        sort_order=body.sort,
    )
    db.add(b)
    db.commit()
    return APIResponse[Any](code=0, msg="新增成功", data=None)


@router.get("/banner/detail", response_model=APIResponse[dict])
def banner_detail(
    id: int = Query(..., alias="id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.query(models.HomeBanner).filter(models.HomeBanner.id == id).first()
    if not r:
        raise HTTPException(404, "轮播图不存在")
    return APIResponse[dict](code=0, msg="ok", data={
        "id": r.id,
        "title": getattr(r, "title", "") or "",
        "image_url": r.image_url,
        "sort": r.sort_order,
        "link_url": r.link_url or "",
    })


class BannerEditBody(BaseModel):
    id: int
    title: str = ""
    image_url: str
    sort: int = 0
    link_url: str = ""


@router.post("/banner/edit", response_model=APIResponse[Any])
def banner_edit(
    body: BannerEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.query(models.HomeBanner).filter(models.HomeBanner.id == body.id).first()
    if not r:
        raise HTTPException(404, "轮播图不存在")
    r.title = body.title
    r.image_url = body.image_url
    r.sort_order = body.sort
    r.link_url = body.link_url or None
    db.commit()
    return APIResponse[Any](code=0, msg="保存成功", data=None)


class BannerDeleteBody(BaseModel):
    id: int


@router.post("/banner/delete", response_model=APIResponse[Any])
def banner_delete(
    body: BannerDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.HomeBanner).filter(models.HomeBanner.id == body.id).delete()
    db.commit()
    return APIResponse[Any](code=0, msg="删除成功", data=None)


# ---------- 专家联系方式 ----------
@router.get("/contact-config/detail", response_model=APIResponse[dict])
def contact_config_detail(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    rows = db.query(models.ContactConfig).all()
    list_ = []
    seen = set()
    for r in rows:
        seen.add(r.contact_type)
        accounts = []
        if r.account_list_json:
            try:
                accounts = json.loads(r.account_list_json)
            except Exception:
                accounts = []
        list_.append({
            "contact_type": r.contact_type,
            "contact_type_name": CONTACT_TYPE_NAMES.get(r.contact_type, r.contact_type),
            "account_list": accounts,
            "status": r.status,
        })
    for ct in CONTACT_TYPE_NAMES:
        if ct not in seen:
            list_.append({
                "contact_type": ct,
                "contact_type_name": CONTACT_TYPE_NAMES[ct],
                "account_list": [],
                "status": 0,
            })
    return APIResponse[dict](code=0, msg="ok", data={"list": list_})


class ContactConfigItem(BaseModel):
    contact_type: str
    account_list: list[str] = []
    status: int = 1


class ContactConfigSaveBody(BaseModel):
    list: list[ContactConfigItem]


@router.post("/contact-config/save", response_model=APIResponse[Any])
def contact_config_save(
    body: ContactConfigSaveBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    for item in body.list:
        r = db.query(models.ContactConfig).filter(models.ContactConfig.contact_type == item.contact_type).first()
        json_str = json.dumps(item.account_list, ensure_ascii=False)
        if r:
            r.account_list_json = json_str
            r.status = item.status
        else:
            db.add(models.ContactConfig(contact_type=item.contact_type, account_list_json=json_str, status=item.status))
    db.commit()
    return APIResponse[Any](code=0, msg="保存成功", data=None)


# ---------- 虚拟币汇率 ----------
@router.get("/exchange-rate/detail", response_model=APIResponse[dict])
def exchange_rate_detail(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    blessing = db.query(models.ExchangeRate).filter(models.ExchangeRate.currency == "blessing_coin").order_by(models.ExchangeRate.id.desc()).first()
    memorial = db.query(models.ExchangeRate).filter(models.ExchangeRate.currency == "memorial_coin").order_by(models.ExchangeRate.id.desc()).first()
    data = {
        "blessing_coin_rate": int(blessing.rate) if blessing else 10,
        "memorial_coin_rate": int(memorial.rate) if memorial else 10,
    }
    return APIResponse[dict](code=0, msg="ok", data=data)


class ExchangeRateSaveBody(BaseModel):
    blessing_coin_rate: int
    memorial_coin_rate: int


@router.post("/exchange-rate/save", response_model=APIResponse[Any])
def exchange_rate_save(
    body: ExchangeRateSaveBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    for currency, rate in [("blessing_coin", body.blessing_coin_rate), ("memorial_coin", body.memorial_coin_rate)]:
        r = db.query(models.ExchangeRate).filter(models.ExchangeRate.currency == currency).order_by(models.ExchangeRate.id.desc()).first()
        if r:
            r.rate = rate
        else:
            db.add(models.ExchangeRate(currency=currency, rate=rate))
    db.commit()
    return APIResponse[Any](code=0, msg="保存成功", data=None)
