"""移动端接口 v1：服务模块 /api/service/*"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db import models
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/service", tags=["Mobile-Service"])


@router.get("/expert/list", response_model=APIResponse[dict])
def mobile_expert_list(
    # 移动端当前请求用的是 page_num；这里兼容 page/page_num
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service_type: str | None = Query(None),
    page: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    """移动端：专家服务列表"""
    _page = page or page_num
    limit = page_size
    offset = (_page - 1) * page_size

    # 注意：线上数据库未必已经有 avatar_url 列；这里先仅查询“必需列”，避免 unknown column 导致整个接口失败
    total = db.query(models.ExpertContact.id).count()
    rows = (
        db.query(
            models.ExpertContact.id,
            models.ExpertContact.name,
            models.ExpertContact.title,
            models.ExpertContact.wechat,
            models.ExpertContact.mobile,
            models.ExpertContact.description,
        )
        .order_by(models.ExpertContact.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 兼容移动端 ExpertList.vue 字段命名
    list_ = [
        {
            "expert_id": str(r.id),
            "name": r.name or "",
            "avatar": "",
            "title": r.title or "",
            "speciality": r.description or "",
            "honor": r.title or "",
            "wechat": r.wechat or "",
            "phone": r.mobile or "",
            # 目前没有服务统计表，先返回默认值
            "rating": 4.8,
            "order_count": 0,
            # 旧字段兼容：如果前端未来继续用 icon 展示，则提供一个非空默认
            "icon": "",
        }
        for r in rows
    ]

    return APIResponse(code=0, msg="ok", data={"total": total, "list": list_})


class ExpertBookBody(BaseModel):
    expert_id: str = ""
    book_time: str = ""
    question: str = ""
    contact_info: str = ""


@router.post("/expert/book", response_model=APIResponse[dict])
def mobile_expert_book(body: ExpertBookBody):
    """移动端：预约专家"""
    return APIResponse(code=0, msg="ok", data={"order_id": "uuid", "status": "pending", "created_at": ""})


class BlessingBody(BaseModel):
    blessing_type: str = ""
    wish_content: str = ""
    name: str = ""
    birth_date: str = ""


@router.post("/blessing", response_model=APIResponse[dict])
def mobile_service_blessing(body: BlessingBody):
    """移动端：祈福服务"""
    return APIResponse(code=0, msg="ok", data={"blessing_id": "uuid", "status": "processing", "created_at": ""})


class SacrificeBody(BaseModel):
    deceased_name: str = ""
    birth_date: str = ""
    death_date: str = ""
    sacrifice_type: str = "online"
    wish_content: str = ""
    contact_info: str = ""


@router.post("/sacrifice", response_model=APIResponse[dict])
def mobile_service_sacrifice(body: SacrificeBody):
    """移动端：祭祀服务"""
    return APIResponse(code=0, msg="ok", data={"sacrifice_id": "uuid", "status": "processing", "memorial_url": "", "created_at": ""})
