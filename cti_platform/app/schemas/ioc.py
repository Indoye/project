from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.ioc import IoCType, RiskLevel
import re


class TTPBase(BaseModel):
    technique_id: str
    name: str
    tactic: str
    description: Optional[str] = None
    url: Optional[str] = None


class TTPResponse(TTPBase):
    id: int

    class Config:
        from_attributes = True


class IoCCreate(BaseModel):
    value: str
    ioc_type: IoCType
    description: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str) -> str:
        return v.strip().lower()


class IoCUpdate(BaseModel):
    description: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None
    risk_level: Optional[RiskLevel] = None


class IoCResponse(BaseModel):
    id: int
    value: str
    ioc_type: IoCType
    risk_level: RiskLevel
    risk_score: float
    description: Optional[str]
    source: Optional[str]
    tags: Optional[str]
    is_active: bool
    last_enriched_at: Optional[datetime]
    created_at: datetime
    ttps: List[TTPResponse] = []

    class Config:
        from_attributes = True


class IoCImportBulk(BaseModel):
    iocs: List[IoCCreate]
