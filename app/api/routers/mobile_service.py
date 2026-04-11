"""移动端接口 v1：服务模块 /api/service/*"""
from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/service", tags=["Mobile-Service"])


@router.get("/expert/list", response_model=APIResponse[dict])
def mobile_expert_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service_type: str | None = Query(None),
):
    """移动端：专家服务列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


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
