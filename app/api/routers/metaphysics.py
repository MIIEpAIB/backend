"""v1 玄学文化：分类 + 文章 /api/metaphysics/*"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse


router = APIRouter(prefix="/api/metaphysics", tags=["Metaphysics"])


def _dt_str(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


# -------- 分类 --------
@router.get("/category/list", response_model=APIResponse[dict])
def category_list(
    category_name: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.ArticleCategory)
    if category_name:
        q = q.filter(models.ArticleCategory.name.like(f"%{category_name}%"))
    if start_date:
        try:
            q = q.filter(models.ArticleCategory.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.ArticleCategory.created_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.ArticleCategory.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = {
        "total": total,
        "list": [
            {"id": r.id, "category_name": r.name, "created_at": _dt_str(r.created_at)}
            for r in rows
        ],
    }
    return APIResponse[dict](code=0, msg="ok", data=data)


class CategoryAddBody(BaseModel):
    category_name: str


@router.post("/category/add", response_model=APIResponse[dict])
def category_add(
    body: CategoryAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.add(models.ArticleCategory(name=body.category_name))
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


class CategoryEditBody(BaseModel):
    id: int
    category_name: str


@router.post("/category/edit", response_model=APIResponse[dict])
def category_edit(
    body: CategoryEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.ArticleCategory, body.id)
    if not r:
        raise HTTPException(404, "分类不存在")
    r.name = body.category_name
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class CategoryDeleteBody(BaseModel):
    id: int


@router.post("/category/delete", response_model=APIResponse[dict])
def category_delete(
    body: CategoryDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    exists = db.query(models.Article).filter(models.Article.category_id == body.id).first()
    if exists:
        return APIResponse[dict](code=400, msg="该分类下存在文章，无法删除", data=None)
    db.query(models.ArticleCategory).filter(models.ArticleCategory.id == body.id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# -------- 文章 --------
@router.get("/article/list", response_model=APIResponse[dict])
def article_list(
    title: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.Article).join(
        models.ArticleCategory, models.Article.category_id == models.ArticleCategory.id
    )
    if title:
        q = q.filter(models.Article.title.like(f"%{title}%"))
    if start_date:
        try:
            q = q.filter(models.Article.published_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.Article.published_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.Article.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = []
    for r in rows:
        cat = db.get(models.ArticleCategory, r.category_id)
        list_.append(
            {
                "id": r.id,
                "title": r.title,
                "category_name": cat.name if cat else "",
                "cover_image": r.cover_image or "",
                "created_at": _dt_str(r.created_at),
            }
        )
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/article/detail", response_model=APIResponse[dict])
def article_detail(
    article_id: int = Query(..., alias="article_id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.Article, article_id)
    if not r:
        raise HTTPException(404, "文章不存在")
    cat = db.get(models.ArticleCategory, r.category_id)
    data = {
        "id": r.id,
        "title": r.title,
        "category_id": r.category_id,
        "category_name": cat.name if cat else "",
        "cover_image": r.cover_image or "",
        "content": r.content_html or "",
        "publish_time": _dt_str(r.published_at or r.created_at),
    }
    return APIResponse[dict](code=0, msg="ok", data=data)


class ArticleCreateBody(BaseModel):
    title: str
    category_id: int
    cover_image: str
    content: str = ""
    publish_time: str | None = None


@router.post("/article/create", response_model=APIResponse[dict])
def article_create(
    body: ArticleCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    if not db.get(models.ArticleCategory, body.category_id):
        raise HTTPException(400, "分类不存在")
    published_at = None
    if body.publish_time:
        try:
            published_at = datetime.strptime(body.publish_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            published_at = None
    a = models.Article(
        title=body.title,
        category_id=body.category_id,
        cover_image=body.cover_image,
        content_html=body.content,
        status="published",
        published_at=published_at or datetime.utcnow(),
    )
    db.add(a)
    db.commit()
    return APIResponse[dict](code=0, msg="发布成功", data=None)


class ArticleEditBody(BaseModel):
    article_id: int
    title: str
    category_id: int
    cover_image: str
    content: str = ""
    publish_time: str | None = None


@router.post("/article/edit", response_model=APIResponse[dict])
def article_edit(
    body: ArticleEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.Article, body.article_id)
    if not r:
        raise HTTPException(404, "文章不存在")
    r.title = body.title
    r.category_id = body.category_id
    r.cover_image = body.cover_image
    r.content_html = body.content
    if body.publish_time:
        try:
            r.published_at = datetime.strptime(body.publish_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class ArticleDeleteBody(BaseModel):
    article_id: int


@router.post("/article/delete", response_model=APIResponse[dict])
def article_delete(
    body: ArticleDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.Article).filter(models.Article.id == body.article_id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)

