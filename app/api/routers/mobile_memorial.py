"""移动端接口 v1：网上祭祀 /api/memorial/*"""
from fastapi import APIRouter, Query, UploadFile
from pydantic import BaseModel

from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/memorial", tags=["Mobile-Memorial"])


@router.get("/tomb/detail", response_model=APIResponse[dict])
def mobile_tomb_detail(tomb_id: str = Query(..., alias="tomb_id")):
    """移动端：陵墓详情"""
    return APIResponse(code=0, msg="ok", data={"tomb_id": tomb_id, "deceased_name": "", "gender": "male", "birth_date": "", "death_date": "", "relationship": ""})


@router.post("/tomb/image/upload", response_model=APIResponse[dict])
async def mobile_tomb_image_upload(file: UploadFile):
    """移动端：上传陵墓图片（可与 /api/common/upload/image 统一实现）"""
    return APIResponse(code=0, msg="ok", data={"image_url": "/static/uploads/placeholder.jpg"})


class TombSaveBody(BaseModel):
    tomb_id: str | None = None
    deceased_name: str = ""
    gender: str = "male"
    birth_date: str = ""
    death_date: str = ""
    tomb_image: str = ""
    epitaph_line1: str = ""
    epitaph_line2: str = ""
    relationship: str = ""


@router.post("/tomb/save", response_model=APIResponse[dict])
def mobile_tomb_save(body: TombSaveBody):
    """移动端：保存陵墓（创建不传 tomb_id，编辑传 tomb_id）"""
    return APIResponse(code=0, msg="ok", data={"tomb_id": "uuid", "message": "保存成功"})


@router.get("/tomb/relationship/options", response_model=APIResponse[list])
def mobile_tomb_relationship_options():
    """移动端：与逝者关系选项"""
    return APIResponse(code=0, msg="ok", data=[{"relationship_code": "son", "relationship_name": "儿子"}, {"relationship_code": "spouse", "relationship_name": "配偶"}])


class TombUpdateBody(BaseModel):
    tomb_id: str = ""
    deceased_name: str = ""
    tomb_title: str = ""
    deceased_avatar: str = ""
    birth_date: str = ""
    death_date: str = ""
    elegiac_couplet_left: str = ""
    elegiac_couplet_right: str = ""
    life_story: str = ""
    is_public: bool = True


@router.post("/tomb/update", response_model=APIResponse[dict])
def mobile_tomb_update(body: TombUpdateBody):
    """移动端：更新陵墓"""
    return APIResponse(code=0, msg="ok", data={"tomb_id": body.tomb_id, "message": "陵墓信息已成功更新"})


class TombDeleteBody(BaseModel):
    tomb_id: str = ""


@router.post("/tomb/delete", response_model=APIResponse[dict])
def mobile_tomb_delete(body: TombDeleteBody):
    """移动端：删除陵墓"""
    return APIResponse(code=0, msg="ok", data={"tomb_id": body.tomb_id, "message": "陵墓已成功删除"})


@router.get("/hall/index", response_model=APIResponse[dict])
def mobile_memorial_hall_index():
    """移动端：祭祀大厅首页"""
    return APIResponse(code=0, msg="ok", data={"banners": [], "recommend_tombs": []})


@router.get("/offerings/list", response_model=APIResponse[dict])
def mobile_offerings_list(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：贡品列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


class MemorialSubmitBody(BaseModel):
    tomb_id: str = ""
    offering_id: str = ""
    quantity: int = 1
    eulogy: str = ""


@router.post("/submit", response_model=APIResponse[dict])
def mobile_memorial_submit(body: MemorialSubmitBody):
    """移动端：提交祭祀"""
    return APIResponse(code=0, msg="ok", data={"record_id": "uuid", "message": "供奉成功"})


@router.get("/square/list", response_model=APIResponse[dict])
def mobile_memorial_square_list(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：陵园广场列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router.get("/my/list", response_model=APIResponse[dict])
def mobile_memorial_my_list(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：我创建的陵墓列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router.get("/square/feed", response_model=APIResponse[dict])
def mobile_memorial_square_feed(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：广场动态"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})
