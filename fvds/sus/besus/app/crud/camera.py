from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.camera import Camera, CameraEmail
from app.schemas.camera import CameraCreate, CameraUpdate


def get_camera(db: Session, camera_id: int) -> Camera | None:
    return db.get(Camera, camera_id)


def get_camera_by_code(db: Session, code: str) -> Camera | None:
    stmt = select(Camera).where(Camera.code == code)
    return db.scalars(stmt).first()


def get_cameras(db: Session, skip: int = 0, limit: int = 100) -> list[Camera]:
    stmt = select(Camera).order_by(Camera.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def create_camera(db: Session, data: CameraCreate) -> Camera:
    camera = Camera(
        code=data.code,
        url=data.url,
        enabled=data.enabled,
        email_rows=[CameraEmail(email=email) for email in data.emails],
    )
    db.add(camera)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(camera)
    return camera


def update_camera(db: Session, camera: Camera, data: CameraUpdate) -> Camera:
    camera.url = data.url
    camera.enabled = data.enabled

    # Giữ các row email còn tồn tại, chỉ xóa/thêm phần chênh lệch
    # (tránh vi phạm unique (camera_id, email) khi xóa-rồi-thêm cùng email).
    wanted = {email.lower() for email in data.emails}
    kept = [row for row in camera.email_rows if row.email.lower() in wanted]
    kept_lower = {row.email.lower() for row in kept}
    camera.email_rows = kept + [
        CameraEmail(email=email)
        for email in data.emails
        if email.lower() not in kept_lower
    ]

    db.commit()
    db.refresh(camera)
    return camera


def delete_camera(db: Session, camera: Camera) -> None:
    db.delete(camera)
    db.commit()
