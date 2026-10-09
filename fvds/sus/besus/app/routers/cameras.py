from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import camera as crud
from app.database import get_db
from app.schemas.camera import CameraCreate, CameraResponse, CameraUpdate

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(data: CameraCreate, db: Session = Depends(get_db)):
    duplicate = HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mã camera đã tồn tại")
    if crud.get_camera_by_code(db, data.code):
        raise duplicate
    try:
        return crud.create_camera(db, data)
    except IntegrityError:
        raise duplicate


@router.get("", response_model=list[CameraResponse])
def list_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_cameras(db, skip, limit)


@router.get("/by-code/{code}", response_model=CameraResponse)
def get_camera_by_code(code: str, db: Session = Depends(get_db)):
    """Dành cho aicam: tra danh sách email theo mã camera (kiểm tra `enabled` ở phía gọi)."""
    camera = crud.get_camera_by_code(db, code)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy camera")
    return camera


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy camera")
    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
def update_camera(camera_id: int, data: CameraUpdate, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy camera")
    return crud.update_camera(db, camera, data)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy camera")
    crud.delete_camera(db, camera)