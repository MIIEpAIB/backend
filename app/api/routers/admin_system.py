from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin, get_password_hash, verify_password
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse


router = APIRouter(prefix="/api/admin", tags=["AdminSystem"])

def _fmt_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def _get_admin_role_name(db: Session, admin_id: int) -> str:
    r = (
        db.query(models.Role.name)
        .join(models.AdminUserRole, models.AdminUserRole.role_id == models.Role.id)
        .filter(models.AdminUserRole.admin_id == admin_id)
        .first()
    )
    return r[0] if r else ""


def _get_role_permission_codes(db: Session, role_id: int) -> list[str]:
    rows = (
        db.query(models.Permission.code)
        .join(models.RolePermission, models.RolePermission.permission_id == models.Permission.id)
        .filter(models.RolePermission.role_id == role_id)
        .all()
    )
    return [r[0] for r in rows]


def _ensure_permissions_seeded(db: Session) -> None:
    # 仅做最小种子，满足 v1 的“模块-权限”展示
    if db.query(models.Permission.id).first():
        return
    seed = [
        ("article:view", "查看文章"),
        ("article:add", "新增文章"),
        ("article:edit", "编辑文章"),
        ("article:delete", "删除文章"),
        ("video:view", "查看视频"),
        ("video:add", "新增视频"),
        ("video:edit", "编辑视频"),
        ("video:delete", "删除视频"),
        ("courseware:view", "查看课件"),
        ("courseware:add", "新增课件"),
        ("courseware:edit", "编辑课件"),
        ("courseware:delete", "删除课件"),
        ("live:view", "查看直播"),
        ("live:add", "新增直播"),
        ("live:edit", "编辑直播"),
        ("live:delete", "删除直播"),
        ("user:view", "查看用户"),
        ("order:view", "查看订单"),
    ]
    db.add_all([models.Permission(code=c, name=n) for c, n in seed])
    db.commit()


@router.post("/change-password", response_model=APIResponse[dict])
def change_admin_password_v1(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    """
    按 v1 文档：
    URL: /api/admin/change-password
    Method: POST
    Body: { old_password, new_password, confirm_password }
    """
    old_password = body.get("old_password")
    new_password = body.get("new_password")
    confirm_password = body.get("confirm_password")
    if not old_password or not new_password or not confirm_password:
        raise HTTPException(
            status_code=400, detail="old_password, new_password, confirm_password required"
        )
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="new_password and confirm_password not match")
    if not verify_password(old_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="old_password incorrect")
    admin.password_hash = get_password_hash(new_password)
    db.add(admin)
    db.commit()
    return APIResponse[dict](code=0, msg="ok", data={})


@router.put("/profile/password", response_model=APIResponse[dict])
def change_admin_password_legacy(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    """
    兼容旧地址：/api/admin/profile/password
    Body: { old_password, new_password }
    """
    old_password = body.get("old_password")
    new_password = body.get("new_password")
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="old_password and new_password required")
    if not verify_password(old_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="old_password incorrect")
    admin.password_hash = get_password_hash(new_password)
    db.add(admin)
    db.commit()
    return APIResponse[dict](code=0, msg="ok", data={})


# ---------- v1 管理员管理 ----------
@router.get("/list", response_model=APIResponse[dict])
def admin_list_v1(
    account: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.AdminUser)
    if account:
        q = q.filter(models.AdminUser.username.like(f"%{account}%"))
    total = q.count()
    rows = (
        q.order_by(models.AdminUser.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = [
        {
            "id": r.id,
            "account": r.username,
            "role_name": _get_admin_role_name(db, r.id) or "超级管理员",
            "created_at": _fmt_dt(r.created_at),
        }
        for r in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/roles", response_model=APIResponse[list])
def admin_roles_v1(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    rows = db.query(models.Role).order_by(models.Role.id.asc()).all()
    return APIResponse[list](code=0, msg="ok", data=[{"id": r.id, "name": r.name} for r in rows])


@router.post("/create", response_model=APIResponse[dict])
def admin_create_v1(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    account = body.get("account")
    password = body.get("password")
    role_id = body.get("role_id")
    if not account or not password or not role_id:
        raise HTTPException(status_code=400, detail="account/password/role_id required")
    exists = db.query(models.AdminUser).filter_by(username=account).first()
    if exists:
        raise HTTPException(status_code=400, detail="account exists")
    role = db.get(models.Role, role_id)
    if not role:
        raise HTTPException(status_code=400, detail="role not found")
    u = models.AdminUser(username=account, password_hash=get_password_hash(password), status=1)
    db.add(u)
    db.commit()
    db.refresh(u)
    db.add(models.AdminUserRole(admin_id=u.id, role_id=role.id))
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


@router.post("/edit", response_model=APIResponse[dict])
def admin_edit_v1(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    admin_id = body.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=400, detail="admin_id required")
    u = db.get(models.AdminUser, admin_id)
    if not u:
        raise HTTPException(status_code=404, detail="admin not found")
    password = body.get("password")
    role_id = body.get("role_id")
    if password:
        u.password_hash = get_password_hash(password)
    if role_id:
        role = db.get(models.Role, role_id)
        if not role:
            raise HTTPException(status_code=400, detail="role not found")
        db.query(models.AdminUserRole).filter(models.AdminUserRole.admin_id == u.id).delete()
        db.add(models.AdminUserRole(admin_id=u.id, role_id=role.id))
    db.add(u)
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


@router.post("/delete", response_model=APIResponse[dict])
def admin_delete_v1(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    admin_id = body.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=400, detail="admin_id required")
    if int(admin_id) == int(admin.id):
        raise HTTPException(status_code=400, detail="cannot delete self")
    db.query(models.AdminUserRole).filter(models.AdminUserRole.admin_id == admin_id).delete()
    db.query(models.AdminUser).filter(models.AdminUser.id == admin_id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# ---------- v1 操作日志 ----------
@router.get("/log/list", response_model=APIResponse[dict])
def admin_log_list_v1(
    account: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.AdminOpLog)
    if account:
        q = q.filter(models.AdminOpLog.username.like(f"%{account}%"))
    total = q.count()
    rows = (
        q.order_by(models.AdminOpLog.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = [
        {
            "id": r.id,
            "admin_account": r.username,
            "role_name": _get_admin_role_name(db, r.admin_id) or "超级管理员",
            "action": r.action,
            "created_at": _fmt_dt(r.created_at),
        }
        for r in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


# ---------- v1 角色管理 ----------
@router.get("/role/list", response_model=APIResponse[dict])
def role_list_v1(
    name: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.Role)
    if name:
        q = q.filter(models.Role.name.like(f"%{name}%"))
    total = q.count()
    rows = (
        q.order_by(models.Role.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = [
        {
            "id": r.id,
            "name": r.name,
            "permissions": _get_role_permission_codes(db, r.id),
            "created_at": _fmt_dt(r.created_at),
        }
        for r in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/role/permissions", response_model=APIResponse[list])
def role_permissions_v1(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    _ensure_permissions_seeded(db)
    # v1 结构：按 module 分组
    groups = [
        ("玄学文化管理", ["article:view", "article:add", "article:edit", "article:delete"]),
        ("在线教学管理", ["video:view", "video:add", "video:edit", "video:delete", "courseware:view", "courseware:add", "courseware:edit", "courseware:delete", "live:view", "live:add", "live:edit", "live:delete"]),
        ("用户与订单", ["user:view", "order:view"]),
    ]
    code_to_name = {p.code: p.name for p in db.query(models.Permission).all()}
    data = []
    for module, codes in groups:
        data.append(
            {
                "module": module,
                "children": [{"id": c, "name": code_to_name.get(c, c)} for c in codes],
            }
        )
    return APIResponse[list](code=0, msg="ok", data=data)


@router.get("/role/detail", response_model=APIResponse[dict])
def role_detail_v1(
    id: int = Query(...),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.Role, id)
    if not r:
        raise HTTPException(status_code=404, detail="role not found")
    return APIResponse[dict](
        code=0,
        msg="ok",
        data={
            "id": r.id,
            "name": r.name,
            "permissions": _get_role_permission_codes(db, r.id),
            "created_at": _fmt_dt(r.created_at),
        },
    )


@router.post("/role/create", response_model=APIResponse[dict])
def role_create_v1(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    name = body.get("name")
    permissions = body.get("permissions") or []
    if not name or not isinstance(permissions, list) or not permissions:
        raise HTTPException(status_code=400, detail="name/permissions required")
    exists = db.query(models.Role).filter_by(name=name).first()
    if exists:
        raise HTTPException(status_code=400, detail="role exists")
    _ensure_permissions_seeded(db)
    r = models.Role(name=name)
    db.add(r)
    db.commit()
    db.refresh(r)
    perm_rows = db.query(models.Permission).filter(models.Permission.code.in_(permissions)).all()
    for p in perm_rows:
        db.add(models.RolePermission(role_id=r.id, permission_id=p.id))
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


@router.post("/role/edit", response_model=APIResponse[dict])
def role_edit_v1(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    role_id = body.get("id")
    name = body.get("name")
    permissions = body.get("permissions") or []
    if not role_id or not name or not isinstance(permissions, list):
        raise HTTPException(status_code=400, detail="id/name/permissions required")
    r = db.get(models.Role, role_id)
    if not r:
        raise HTTPException(status_code=404, detail="role not found")
    _ensure_permissions_seeded(db)
    r.name = name
    db.add(r)
    db.query(models.RolePermission).filter(models.RolePermission.role_id == r.id).delete()
    perm_rows = db.query(models.Permission).filter(models.Permission.code.in_(permissions)).all()
    for p in perm_rows:
        db.add(models.RolePermission(role_id=r.id, permission_id=p.id))
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


@router.post("/role/delete", response_model=APIResponse[dict])
def role_delete_v1(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    role_id = body.get("id")
    if not role_id:
        raise HTTPException(status_code=400, detail="id required")
    used = db.query(models.AdminUserRole).filter(models.AdminUserRole.role_id == role_id).first()
    if used:
        raise HTTPException(status_code=400, detail="role is in use")
    db.query(models.RolePermission).filter(models.RolePermission.role_id == role_id).delete()
    db.query(models.Role).filter(models.Role.id == role_id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


@router.get("/admin-users", response_model=APIResponse[dict])
def list_admin_users(
    username: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.AdminUser)
    if username:
        q = q.filter(models.AdminUser.username.like(f"%{username}%"))
    total = q.count()
    rows = (
        q.order_by(models.AdminUser.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data_list = [
        {
            "id": a.id,
            "username": a.username,
            "roles": [],
            "status": a.status,
            "created_at": a.created_at,
        }
        for a in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": data_list})


@router.post("/admin-users", response_model=APIResponse[dict])
def create_admin_user(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    exists = db.query(models.AdminUser).filter_by(username=username).first()
    if exists:
        raise HTTPException(status_code=400, detail="username exists")
    u = models.AdminUser(username=username, password_hash=get_password_hash(password), status=1)
    db.add(u)
    db.commit()
    db.refresh(u)
    return APIResponse[dict](code=0, msg="ok", data={"id": u.id})


@router.get("/op-logs", response_model=APIResponse[dict])
def list_op_logs(
    admin_name: str | None = Query(None),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.AdminOpLog)
    if admin_name:
        q = q.filter(models.AdminOpLog.username.like(f"%{admin_name}%"))
    if action:
        q = q.filter(models.AdminOpLog.action.like(f"%{action}%"))
    total = q.count()
    rows = (
        q.order_by(models.AdminOpLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data_list = [
        {
            "id": r.id,
            "admin_id": r.admin_id,
            "username": r.username,
            "action": r.action,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "detail": r.detail,
            "ip": r.ip,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": data_list})

