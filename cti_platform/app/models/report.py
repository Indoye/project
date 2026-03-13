from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ReportFormat(str, enum.Enum):
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    format = Column(Enum(ReportFormat), default=ReportFormat.JSON)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)

    filters = Column(Text, nullable=True)   # JSON: filters used to generate
    content = Column(Text, nullable=True)   # JSON report data
    file_path = Column(String(512), nullable=True)  # PDF path if applicable

    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
