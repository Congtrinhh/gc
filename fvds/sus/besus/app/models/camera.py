from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    url: Mapped[str] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    email_rows: Mapped[list["CameraEmail"]] = relationship(
        back_populates="camera",
        cascade="all, delete-orphan",
        order_by="CameraEmail.id",
        lazy="selectin",
    )

    @property
    def emails(self) -> list[str]:
        return [row.email for row in self.email_rows]


class CameraEmail(Base):
    __tablename__ = "camera_emails"
    __table_args__ = (UniqueConstraint("camera_id", "email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE")
    )
    email: Mapped[str] = mapped_column(String(255))

    camera: Mapped[Camera] = relationship(back_populates="email_rows")
