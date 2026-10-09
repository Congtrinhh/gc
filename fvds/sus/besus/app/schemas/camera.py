from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CameraBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    emails: list[EmailStr] = Field(min_length=1, max_length=20)
    url: str = Field(min_length=1, max_length=500)
    enabled: bool = True

    @field_validator("emails")
    @classmethod
    def dedupe_emails(cls, emails: list[str]) -> list[str]:
        seen: dict[str, str] = {}
        for email in emails:
            seen.setdefault(email.lower(), email)
        return list(seen.values())


class CameraCreate(CameraBase):
    code: str = Field(min_length=1, max_length=50)


class CameraUpdate(CameraBase):
    pass


class CameraResponse(CameraCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
