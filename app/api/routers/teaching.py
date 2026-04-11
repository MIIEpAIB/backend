"""v1 在线教学：视频、课件、一对一、直播 /api/teaching/*"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse


router = APIRouter(prefix="/api/teaching", tags=["Teaching"])


def _dt_str(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


# -------- 视频 --------
@router.get("/video/list", response_model=APIResponse[dict])
def video_list(
    title: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.TeachVideo)
    if title:
        q = q.filter(models.TeachVideo.title.like(f"%{title}%"))
    if start_date:
        try:
            q = q.filter(models.TeachVideo.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.TeachVideo.created_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.TeachVideo.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = [
        {
            "id": r.id,
            "title": r.title,
            "cover_image": r.cover_image or "",
            "created_at": _dt_str(r.created_at),
        }
        for r in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class VideoCreateBody(BaseModel):
    title: str
    cover_image: str = ""
    video_url: str


@router.post("/video/create", response_model=APIResponse[dict])
def video_create(
    body: VideoCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.add(
        models.TeachVideo(
            title=body.title,
            cover_image=body.cover_image or None,
            video_url=body.video_url,
            status="on",
            published_at=datetime.utcnow(),
        )
    )
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


class VideoEditBody(BaseModel):
    video_id: int
    title: str
    cover_image: str = ""
    video_url: str


@router.post("/video/edit", response_model=APIResponse[dict])
def video_edit(
    body: VideoEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.TeachVideo, body.video_id)
    if not r:
        raise HTTPException(404, "视频不存在")
    r.title = body.title
    r.cover_image = body.cover_image or None
    r.video_url = body.video_url
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class VideoDeleteBody(BaseModel):
    video_id: int


@router.post("/video/delete", response_model=APIResponse[dict])
def video_delete(
    body: VideoDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.TeachVideo).filter(models.TeachVideo.id == body.video_id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# -------- 课件 --------
@router.get("/courseware/list", response_model=APIResponse[dict])
def courseware_list(
    title: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.Courseware)
    if title:
        q = q.filter(models.Courseware.title.like(f"%{title}%"))
    if start_date:
        try:
            q = q.filter(models.Courseware.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.Courseware.created_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.Courseware.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = [
        {
            "id": r.id,
            "title": r.title,
            "cover_image": r.cover_image or "",
            "created_at": _dt_str(r.created_at),
        }
        for r in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/courseware/detail", response_model=APIResponse[dict])
def courseware_detail(
    courseware_id: int = Query(..., alias="courseware_id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.Courseware, courseware_id)
    if not r:
        raise HTTPException(404, "课件不存在")
    return APIResponse[dict](
        code=0,
        msg="ok",
        data={
            "id": r.id,
            "title": r.title,
            "cover_image": r.cover_image or "",
            "file_url": r.file_url,
            "publish_time": _dt_str(r.published_at or r.created_at),
        },
    )


class CoursewareCreateBody(BaseModel):
    title: str
    cover_image: str = ""
    file_url: str
    publish_time: str | None = None


@router.post("/courseware/create", response_model=APIResponse[dict])
def courseware_create(
    body: CoursewareCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    published_at = None
    if body.publish_time:
        try:
            published_at = datetime.strptime(body.publish_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            published_at = None
    db.add(
        models.Courseware(
            title=body.title,
            cover_image=body.cover_image or None,
            file_url=body.file_url,
            published_at=published_at or datetime.utcnow(),
        )
    )
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


class CoursewareEditBody(BaseModel):
    courseware_id: int
    title: str
    cover_image: str = ""
    file_url: str
    publish_time: str | None = None


@router.post("/courseware/edit", response_model=APIResponse[dict])
def courseware_edit(
    body: CoursewareEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.Courseware, body.courseware_id)
    if not r:
        raise HTTPException(404, "课件不存在")
    r.title = body.title
    r.cover_image = body.cover_image or None
    r.file_url = body.file_url
    if body.publish_time:
        try:
            r.published_at = datetime.strptime(body.publish_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class CoursewareDeleteBody(BaseModel):
    courseware_id: int


@router.post("/courseware/delete", response_model=APIResponse[dict])
def courseware_delete(
    body: CoursewareDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.Courseware).filter(models.Courseware.id == body.courseware_id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# -------- 一对一 --------
@router.get("/one-on-one/list", response_model=APIResponse[dict])
def one2one_list(
    title: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.One2OneCourse)
    if title:
        q = q.filter(models.One2OneCourse.title.like(f"%{title}%"))
    if start_date:
        try:
            q = q.filter(models.One2OneCourse.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.One2OneCourse.created_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.One2OneCourse.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = [
        {
            "id": r.id,
            "title": r.title,
            "cover_image": r.image or "",
            "created_at": _dt_str(r.created_at),
        }
        for r in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/one-on-one/detail", response_model=APIResponse[dict])
def one2one_detail(
    one_on_one_id: int = Query(..., alias="one_on_one_id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.One2OneCourse, one_on_one_id)
    if not r:
        raise HTTPException(404, "记录不存在")
    return APIResponse[dict](
        code=0,
        msg="ok",
        data={
            "id": r.id,
            "title": r.title,
            "cover_image": r.image or "",
            "content": r.description_html or "",
            "publish_time": _dt_str(r.published_at or r.created_at),
            "status": 1 if r.status == "on" else 0,
        },
    )


class One2OneCreateBody(BaseModel):
    title: str
    cover_image: str = ""
    content: str = ""
    publish_time: str | None = None


@router.post("/one-on-one/create", response_model=APIResponse[dict])
def one2one_create(
    body: One2OneCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    published_at = None
    if body.publish_time:
        try:
            published_at = datetime.strptime(body.publish_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            published_at = None
    db.add(
        models.One2OneCourse(
            title=body.title,
            image=body.cover_image or None,
            description_html=body.content,
            published_at=published_at or datetime.utcnow(),
            status="on",
        )
    )
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


class One2OneEditBody(BaseModel):
    one_on_one_id: int
    title: str
    cover_image: str = ""
    content: str = ""
    publish_time: str | None = None
    status: int = 1


@router.post("/one-on-one/edit", response_model=APIResponse[dict])
def one2one_edit(
    body: One2OneEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.One2OneCourse, body.one_on_one_id)
    if not r:
        raise HTTPException(404, "记录不存在")
    r.title = body.title
    r.image = body.cover_image or None
    r.description_html = body.content
    r.status = "on" if body.status == 1 else "off"
    if body.publish_time:
        try:
            r.published_at = datetime.strptime(body.publish_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class One2OneDeleteBody(BaseModel):
    one_on_one_id: int


@router.post("/one-on-one/delete", response_model=APIResponse[dict])
def one2one_delete(
    body: One2OneDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.One2OneCourse).filter(models.One2OneCourse.id == body.one_on_one_id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# -------- 直播 --------
@router.get("/live/list", response_model=APIResponse[dict])
def live_list(
    title: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.LiveEvent)
    if title:
        q = q.filter(models.LiveEvent.title.like(f"%{title}%"))
    if start_date:
        try:
            q = q.filter(models.LiveEvent.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.LiveEvent.created_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.LiveEvent.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )

    now = datetime.utcnow()
    list_ = []
    for r in rows:
        # v1: 0 未开始 1 直播中 2 已结束
        status = 0
        if now >= r.live_start:
            status = 1
        if r.live_end and now >= r.live_end:
            status = 2
        list_.append(
            {
                "id": r.id,
                "title": r.title,
                "live_time": _dt_str(r.live_start),
                "stream_url": r.live_url,
                "status": status,
                "created_at": _dt_str(r.created_at),
            }
        )
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class LiveCreateBody(BaseModel):
    title: str
    live_time: str
    duration_minutes: int = 60
    stream_url: str


@router.post("/live/create", response_model=APIResponse[dict])
def live_create(
    body: LiveCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    try:
        start = datetime.strptime(body.live_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(400, "live_time 格式应为 yyyy-MM-dd HH:mm:ss")
    end = start + timedelta(minutes=body.duration_minutes or 60)
    db.add(models.LiveEvent(title=body.title, live_start=start, live_end=end, live_url=body.stream_url))
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


class LiveEditBody(BaseModel):
    live_id: int
    title: str
    live_time: str
    duration_minutes: int = 60
    stream_url: str


@router.post("/live/edit", response_model=APIResponse[dict])
def live_edit(
    body: LiveEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.LiveEvent, body.live_id)
    if not r:
        raise HTTPException(404, "直播不存在")
    try:
        start = datetime.strptime(body.live_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(400, "live_time 格式应为 yyyy-MM-dd HH:mm:ss")
    r.title = body.title
    r.live_start = start
    r.live_end = start + timedelta(minutes=body.duration_minutes or 60)
    r.live_url = body.stream_url
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class LiveDeleteBody(BaseModel):
    live_id: int


@router.post("/live/delete", response_model=APIResponse[dict])
def live_delete(
    body: LiveDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.LiveEvent).filter(models.LiveEvent.id == body.live_id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# -------- 移动端专用（无需管理员登录）--------
@router.get("/categories", response_model=APIResponse[list])
def mobile_teaching_categories():
    """移动端：教学分类"""
    return APIResponse(code=0, msg="ok", data=[{"category_code": "live", "category_name": "现场直播"}, {"category_code": "replay", "category_name": "教学回播"}, {"category_code": "courseware", "category_name": "课件"}])


@router.get("/video/detail", response_model=APIResponse[dict])
def mobile_teaching_video_detail(video_id: str = Query(...)):
    """移动端：视频详情"""
    return APIResponse(code=0, msg="ok", data={"video_id": video_id, "title": "", "video_url": "", "duration": ""})


@router.get("/list", response_model=APIResponse[dict])
def mobile_teaching_list(page_num: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """移动端：教学列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router.get("/live/detail", response_model=APIResponse[dict])
def mobile_teaching_live_detail(schedule_id: str = Query(...)):
    """移动端：直播详情"""
    return APIResponse(code=0, msg="ok", data={"schedule_id": schedule_id, "title": "", "play_url": "", "status": ""})


@router.get("/replay/list", response_model=APIResponse[dict])
def mobile_teaching_replay_list(page_num: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """移动端：回播列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router.get("/material/list", response_model=APIResponse[dict])
def mobile_teaching_material_list(page_num: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """移动端：课件资料列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


class One2OneBookBody(BaseModel):
    course_id: str = ""
    book_time: str = ""
    contact: str = ""


@router.post("/one2one/book", response_model=APIResponse[dict])
def mobile_teaching_one2one_book(body: One2OneBookBody):
    """移动端：预约一对一"""
    return APIResponse(code=0, msg="ok", data={"order_id": "uuid", "message": "预约成功"})


@router.get("/one2one/detail", response_model=APIResponse[dict])
def mobile_teaching_one2one_detail(course_id: str = Query(None)):
    """移动端：一对一课程详情"""
    return APIResponse(code=0, msg="ok", data={"course_id": course_id or "uuid", "title": "", "modules": []})


@router.get("/teachers", response_model=APIResponse[dict])
def mobile_teaching_teachers():
    """移动端：讲师列表"""
    return APIResponse(code=0, msg="ok", data={"list": []})


@router.get("/teacher/schedule", response_model=APIResponse[dict])
def mobile_teaching_teacher_schedule(teacher_id: str = Query(...)):
    """移动端：讲师可预约时段"""
    return APIResponse(code=0, msg="ok", data={"slots": []})

