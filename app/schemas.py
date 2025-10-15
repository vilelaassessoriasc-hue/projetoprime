from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LatitudeLongitudeModel(BaseModel):
    latitude: Optional[float] = Field(None, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(None, description="Longitude in decimal degrees")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not (-90 <= value <= 90):
            raise ValueError("latitude must be between -90 and 90 degrees")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not (-180 <= value <= 180):
            raise ValueError("longitude must be between -180 and 180 degrees")
        return value


class SkillBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)


class SkillCreate(SkillBase):
    pass


class SkillRead(SkillBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class AddressBase(LatitudeLongitudeModel):
    street: str = Field(..., min_length=2, max_length=120)
    city: str = Field(..., min_length=2, max_length=80)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., min_length=2, max_length=20)


class AddressCreate(AddressBase):
    latitude: float
    longitude: float


class AddressRead(AddressBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserRead(UserBase):
    id: int
    created_at: datetime
    address: Optional[AddressRead] = None
    skills: List[SkillRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class JobBase(LatitudeLongitudeModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=10, max_length=1024)


class JobCreate(JobBase):
    skill_ids: List[int] = Field(default_factory=list)


class JobRead(JobBase):
    id: int
    company_id: int
    created_at: datetime
    skills: List[SkillRead]

    model_config = ConfigDict(from_attributes=True)


class JobMatch(BaseModel):
    user_id: int
    user_name: str
    matching_skills: int
    required_skills: int
    distance_km: Optional[float] = Field(
        None, description="Distance between the job and the candidate address"
    )


class JobDetail(JobRead):
    company: UserRead

    model_config = ConfigDict(from_attributes=True)
