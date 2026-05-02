from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timezone
import re


class PopupEnquiry(BaseModel):
    """Scroll popup form — minimal fields"""
    name: str
    phone: str
    email: Optional[EmailStr] = None
    course: Optional[str] = None
    source: str = "popup"

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 80:
            raise ValueError("Name too long")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid(cls, v: str) -> str:
        digits = re.sub(r"[\s\-\+\(\)]", "", v)
        if not digits.isdigit():
            raise ValueError("Phone must contain only digits")
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("Invalid phone number length")
        return v

    @field_validator("course")
    @classmethod
    def sanitize_course(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()[:120]
        return v


class ContactEnquiry(BaseModel):
    """Full contact page form"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    course: Optional[str] = None
    mode: Optional[str] = None
    message: Optional[str] = None
    source: str = "contact"

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 80:
            raise ValueError("Name too long")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        digits = re.sub(r"[\s\-\+\(\)]", "", v)
        if not digits.isdigit():
            raise ValueError("Phone must contain only digits")
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("Invalid phone number length")
        return v

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()[:2000]
        return v

    @field_validator("course", "mode")
    @classmethod
    def sanitize_short_fields(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()[:120]
        return v


class EnquiryResponse(BaseModel):
    success: bool
    message: str
