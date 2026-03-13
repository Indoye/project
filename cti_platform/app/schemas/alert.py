from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.alert import AlertSeverity, AlertStatus


class AlertCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    ioc_id: Optional[int] = None
    triggered_by: Optional[str] = None


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    description: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    severity: AlertSeverity
    status: AlertStatus
    ioc_id: Optional[int]
    triggered_by: Optional[str]
    notified: bool
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
