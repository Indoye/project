from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.ioc import IoC, IoCType, RiskLevel
from app.models.alert import Alert, AlertSeverity, AlertStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_iocs = db.query(func.count(IoC.id)).scalar()
    active_iocs = db.query(func.count(IoC.id)).filter(IoC.is_active == True).scalar()

    iocs_by_type = dict(
        db.query(IoC.ioc_type, func.count(IoC.id))
        .group_by(IoC.ioc_type)
        .all()
    )
    iocs_by_risk = dict(
        db.query(IoC.risk_level, func.count(IoC.id))
        .group_by(IoC.risk_level)
        .all()
    )

    total_alerts = db.query(func.count(Alert.id)).scalar()
    open_alerts = db.query(func.count(Alert.id)).filter(
        Alert.status == AlertStatus.OPEN
    ).scalar()
    alerts_by_severity = dict(
        db.query(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
        .all()
    )

    top_risky_iocs = (
        db.query(IoC)
        .filter(IoC.is_active == True)
        .order_by(IoC.risk_score.desc())
        .limit(10)
        .all()
    )

    return {
        "iocs": {
            "total": total_iocs,
            "active": active_iocs,
            "by_type": {k.value if hasattr(k, "value") else k: v for k, v in iocs_by_type.items()},
            "by_risk": {k.value if hasattr(k, "value") else k: v for k, v in iocs_by_risk.items()},
        },
        "alerts": {
            "total": total_alerts,
            "open": open_alerts,
            "by_severity": {
                k.value if hasattr(k, "value") else k: v
                for k, v in alerts_by_severity.items()
            },
        },
        "top_risky_iocs": [
            {"id": i.id, "value": i.value, "type": i.ioc_type, "score": i.risk_score}
            for i in top_risky_iocs
        ],
    }
