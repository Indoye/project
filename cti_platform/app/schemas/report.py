from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.report import ReportFormat, ReportStatus


class ReportCreate(BaseModel):
    title: str
    description: Optional[str] = None
    format: ReportFormat = ReportFormat.JSON
    filters: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    format: ReportFormat
    status: ReportStatus
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    content: Optional[str]
    file_path: Optional[str]
