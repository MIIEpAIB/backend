"""移动端接口 v1：内容与课程 /api/content/*"""
from fastapi import APIRouter, Query

from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/content", tags=["Mobile-Content"])


@router.get("/culture/list", response_model=APIResponse[dict])
def mobile_culture_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：玄学文化列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router.get("/culture/detail", response_model=APIResponse[dict])
def mobile_culture_detail(course_id: str = Query(...)):
    """移动端：文化内容详情"""
    return APIResponse(code=0, msg="ok", data={"content_id": course_id, "title": "", "content": ""})


@router.get("/course/list", response_model=APIResponse[dict])
def mobile_course_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    level: str | None = Query(None),
):
    """移动端：在线课程列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router.get("/course/detail", response_model=APIResponse[dict])
def mobile_course_detail(course_id: str = Query(...)):
    """移动端：课程详情"""
    return APIResponse(code=0, msg="ok", data={"course_id": course_id, "title": "", "chapters": []})
