"""仪表盘：今日概况、运营报表"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=APIResponse[dict])
def get_overview(
    date_param: str | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    """获取今日概况。不传 date 默认为今天。"""
    d = date_param or date.today().isoformat()
    try:
        target = datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        target = date.today()
    start = datetime.combine(target, datetime.min.time())
    end = datetime.combine(target, datetime.max.time())

    total_users = db.query(func.count(models.User.id)).scalar() or 0
    today_registered = (
        db.query(func.count(models.User.id))
        .filter(models.User.registered_at >= start, models.User.registered_at <= end)
        .scalar()
        or 0
    )
    recharge_row = db.query(
        func.count(models.RechargeOrder.id),
        func.coalesce(func.sum(models.RechargeOrder.amount), 0),
    ).filter(
        models.RechargeOrder.status == "success",
        models.RechargeOrder.created_at >= start,
        models.RechargeOrder.created_at <= end,
    ).first()
    today_recharge_count = recharge_row[0] or 0
    today_recharge_amount = float(recharge_row[1] or 0)

    goods_total = (
        db.query(func.coalesce(func.sum(models.ProductOrder.amount_total), 0))
        .filter(
            models.ProductOrder.pay_status == "paid",
            models.ProductOrder.created_at >= start,
            models.ProductOrder.created_at <= end,
        )
        .scalar()
        or 0
    )
    goods_payment_total = float(goods_total) if isinstance(goods_total, (Decimal, int)) else 0.0

    memorial_total = (
        db.query(func.coalesce(func.sum(models.SacrificeOrder.rmb_amount), 0))
        .filter(
            models.SacrificeOrder.pay_status == "paid",
            models.SacrificeOrder.created_at >= start,
            models.SacrificeOrder.created_at <= end,
        )
        .scalar()
        or 0
    )
    memorial_consume_total = float(memorial_total) if isinstance(memorial_total, (Decimal, int)) else 0.0

    blessing_total = (
        db.query(func.coalesce(func.sum(models.BlessOrder.rmb_amount), 0))
        .filter(
            models.BlessOrder.pay_status == "paid",
            models.BlessOrder.created_at >= start,
            models.BlessOrder.created_at <= end,
        )
        .scalar()
        or 0
    )
    blessing_consume_total = float(blessing_total) if isinstance(blessing_total, (Decimal, int)) else 0.0

    users_balance = db.query(func.coalesce(func.sum(models.User.balance), 0)).scalar() or 0
    users_total_balance = float(users_balance) if isinstance(users_balance, (Decimal, int)) else 0.0

    data = {
        "total_users": total_users,
        "today_registered": today_registered,
        "today_recharge_count": today_recharge_count,
        "today_recharge_amount": round(today_recharge_amount, 2),
        "goods_payment_total": round(goods_payment_total, 2),
        "memorial_consume_total": round(memorial_consume_total, 2),
        "blessing_consume_total": round(blessing_consume_total, 2),
        "users_total_balance": round(users_total_balance, 2),
    }
    return APIResponse[dict](code=0, msg="ok", data=data)


@router.get("/operation-report/list", response_model=APIResponse[dict])
def operation_report_list(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    """运营报表分页列表 + 底部总计。按日期维度聚合。"""
    # 简化：按 product_order / bless_order / sacrifice_order 的日期汇总
    # 这里返回按日期的模拟结构，实际可建视图或复杂 SQL
    list_ = []
    try:
        start = datetime.strptime(start_date or "2020-01-01", "%Y-%m-%d").date()
        end = datetime.strptime(end_date or date.today().isoformat(), "%Y-%m-%d").date()
    except ValueError:
        start = date.today() - timedelta(days=30)
        end = date.today()

    # 从订单表取日期列表
    dates_q = (
        db.query(func.date(models.ProductOrder.created_at).label("dt"))
        .filter(models.ProductOrder.pay_status == "paid")
        .filter(func.date(models.ProductOrder.created_at) >= start, func.date(models.ProductOrder.created_at) <= end)
        .distinct()
    )
    dates = [r.dt for r in dates_q.all() if r.dt]
    for d in dates:
        day_start = datetime.combine(d, datetime.min.time())
        day_end = datetime.combine(d, datetime.max.time())
        shopping_user_count = (
            db.query(func.count(func.distinct(models.ProductOrder.user_id)))
            .filter(models.ProductOrder.pay_status == "paid", models.ProductOrder.created_at >= day_start, models.ProductOrder.created_at <= day_end)
            .scalar()
            or 0
        )
        shopping_amount = (
            db.query(func.coalesce(func.sum(models.ProductOrder.amount_total), 0))
            .filter(models.ProductOrder.pay_status == "paid", models.ProductOrder.created_at >= day_start, models.ProductOrder.created_at <= day_end)
            .scalar()
            or 0
        )
        shopping_order_count = (
            db.query(func.count(models.ProductOrder.id))
            .filter(models.ProductOrder.pay_status == "paid", models.ProductOrder.created_at >= day_start, models.ProductOrder.created_at <= day_end)
            .scalar()
            or 0
        )
        blessing_user_count = (
            db.query(func.count(func.distinct(models.BlessOrder.user_id)))
            .filter(models.BlessOrder.pay_status == "paid", models.BlessOrder.created_at >= day_start, models.BlessOrder.created_at <= day_end)
            .scalar()
            or 0
        )
        blessing_amount = (
            db.query(func.coalesce(func.sum(models.BlessOrder.rmb_amount), 0))
            .filter(models.BlessOrder.pay_status == "paid", models.BlessOrder.created_at >= day_start, models.BlessOrder.created_at <= day_end)
            .scalar()
            or 0
        )
        memorial_user_count = (
            db.query(func.count(func.distinct(models.SacrificeOrder.user_id)))
            .filter(models.SacrificeOrder.pay_status == "paid", models.SacrificeOrder.created_at >= day_start, models.SacrificeOrder.created_at <= day_end)
            .scalar()
            or 0
        )
        memorial_amount = (
            db.query(func.coalesce(func.sum(models.SacrificeOrder.rmb_amount), 0))
            .filter(models.SacrificeOrder.pay_status == "paid", models.SacrificeOrder.created_at >= day_start, models.SacrificeOrder.created_at <= day_end)
            .scalar()
            or 0
        )
        list_.append({
            "date": d.isoformat(),
            "shopping_user_count": shopping_user_count,
            "shopping_amount": round(float(shopping_amount), 2),
            "blessing_user_count": blessing_user_count,
            "blessing_amount": round(float(blessing_amount), 2),
            "memorial_user_count": memorial_user_count,
            "memorial_amount": round(float(memorial_amount), 2),
            "shopping_order_count": shopping_order_count,
        })
    list_.sort(key=lambda x: x["date"], reverse=True)
    total = len(list_)
    summary = {
        "total_shopping_user_count": sum(x["shopping_user_count"] for x in list_),
        "total_shopping_amount": round(sum(x["shopping_amount"] for x in list_), 2),
        "total_blessing_user_count": sum(x["blessing_user_count"] for x in list_),
        "total_blessing_amount": round(sum(x["blessing_amount"] for x in list_), 2),
        "total_memorial_user_count": sum(x["memorial_user_count"] for x in list_),
        "total_memorial_amount": round(sum(x["memorial_amount"] for x in list_), 2),
        "total_shopping_order_count": sum(x["shopping_order_count"] for x in list_),
    }
    page_list = list_[(page_num - 1) * page_size : page_num * page_size]
    data = {"total": total, "list": page_list, "summary": summary}
    return APIResponse[dict](code=0, msg="ok", data=data)


@router.get("/operation-report/export")
def operation_report_export(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    """导出运营报表 Excel。返回文件流。"""
    import io
    try:
        start = datetime.strptime(start_date or "2020-01-01", "%Y-%m-%d").date()
        end = datetime.strptime(end_date or date.today().isoformat(), "%Y-%m-%d").date()
    except ValueError:
        start = date.today() - timedelta(days=30)
        end = date.today()
    # 简单 CSV 代替 Excel，避免依赖 openpyxl
    buf = io.StringIO()
    buf.write("date,shopping_user_count,shopping_amount,blessing_user_count,blessing_amount,memorial_user_count,memorial_amount,shopping_order_count\n")
    dates_q = (
        db.query(func.date(models.ProductOrder.created_at).label("dt"))
        .filter(models.ProductOrder.pay_status == "paid")
        .filter(func.date(models.ProductOrder.created_at) >= start, func.date(models.ProductOrder.created_at) <= end)
        .distinct()
    )
    for r in dates_q.all():
        if not r.dt:
            continue
        d = r.dt
        day_start = datetime.combine(d, datetime.min.time())
        day_end = datetime.combine(d, datetime.max.time())
        sa = db.query(func.coalesce(func.sum(models.ProductOrder.amount_total), 0)).filter(models.ProductOrder.pay_status == "paid", models.ProductOrder.created_at >= day_start, models.ProductOrder.created_at <= day_end).scalar() or 0
        soc = db.query(func.count(models.ProductOrder.id)).filter(models.ProductOrder.pay_status == "paid", models.ProductOrder.created_at >= day_start, models.ProductOrder.created_at <= day_end).scalar() or 0
        so = db.query(func.count(func.distinct(models.ProductOrder.user_id))).filter(models.ProductOrder.pay_status == "paid", models.ProductOrder.created_at >= day_start, models.ProductOrder.created_at <= day_end).scalar() or 0
        ba = db.query(func.coalesce(func.sum(models.BlessOrder.rmb_amount), 0)).filter(models.BlessOrder.pay_status == "paid", models.BlessOrder.created_at >= day_start, models.BlessOrder.created_at <= day_end).scalar() or 0
        bu = db.query(func.count(func.distinct(models.BlessOrder.user_id))).filter(models.BlessOrder.pay_status == "paid", models.BlessOrder.created_at >= day_start, models.BlessOrder.created_at <= day_end).scalar() or 0
        ma = db.query(func.coalesce(func.sum(models.SacrificeOrder.rmb_amount), 0)).filter(models.SacrificeOrder.pay_status == "paid", models.SacrificeOrder.created_at >= day_start, models.SacrificeOrder.created_at <= day_end).scalar() or 0
        mu = db.query(func.count(func.distinct(models.SacrificeOrder.user_id))).filter(models.SacrificeOrder.pay_status == "paid", models.SacrificeOrder.created_at >= day_start, models.SacrificeOrder.created_at <= day_end).scalar() or 0
        buf.write(f"{d.isoformat()},{so},{float(sa)},{bu},{float(ba)},{mu},{float(ma)},{soc}\n")
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=operation_report.csv"},
    )
