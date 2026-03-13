from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class IoCType(str, enum.Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    CVE = "cve"


class RiskLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


# Many-to-many: IoC <-> TTP
ioc_ttp_association = Table(
    "ioc_ttp",
    Base.metadata,
    Column("ioc_id", Integer, ForeignKey("iocs.id")),
    Column("ttp_id", Integer, ForeignKey("ttps.id")),
)


class IoC(Base):
    __tablename__ = "iocs"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(String(512), unique=True, index=True, nullable=False)
    ioc_type = Column(Enum(IoCType), nullable=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.UNKNOWN)
    risk_score = Column(Float, default=0.0)

    description = Column(Text, nullable=True)
    source = Column(String(256), nullable=True)
    tags = Column(String(512), nullable=True)  # comma-separated
    is_active = Column(Boolean, default=True)

    # Enrichment results (JSON stored as text)
    enrichment_data = Column(Text, nullable=True)
    last_enriched_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    ttps = relationship("TTP", secondary=ioc_ttp_association, back_populates="iocs")
    alerts = relationship("Alert", back_populates="ioc")


class TTP(Base):
    """MITRE ATT&CK Tactics, Techniques & Procedures"""
    __tablename__ = "ttps"

    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(String(32), unique=True, index=True)  # e.g. T1566
    name = Column(String(256), nullable=False)
    tactic = Column(String(128), nullable=False)  # e.g. Initial Access
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)

    iocs = relationship("IoC", secondary=ioc_ttp_association, back_populates="ttps")
