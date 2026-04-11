"""通用接口：图片上传"""
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile
from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/common", tags=["Common"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload/image", response_model=APIResponse[dict])
async def upload_image(
    file: UploadFile,
    admin: models.AdminUser = Depends(get_current_admin),
):
    """通用图片上传，返回可访问 URL。"""
    if not file.content_type or not file.content_type.startswith("image/"):
        return APIResponse[dict](code=400, msg="请上传图片文件", data=None)
    ext = (file.filename or "").split(".")[-1] or "png"
    if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
        ext = "png"
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    # 返回相对 URL，前端可拼 baseURL
    url = f"/static/uploads/{name}"
    return APIResponse[dict](code=0, msg="ok", data={"url": url})
