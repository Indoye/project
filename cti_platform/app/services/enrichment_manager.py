"""
Orchestrates enrichment from multiple sources and computes a unified risk score.
"""
import json
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ioc import IoC, IoCType, RiskLevel
from app.services.enrichment import virustotal, abuseipdb, shodan
from app.services.alerting import create_alert_if_needed


def _compute_risk_score(enrichment: dict, ioc_type: IoCType) -> float:
    """Aggregate signals from all sources into a 0-100 score."""
    score = 0.0

    for source_data in enrichment.values():
        if not isinstance(source_data, dict):
            continue

        # VirusTotal signals
        malicious = source_data.get("malicious", 0)
        suspicious = source_data.get("suspicious", 0)
        score += malicious * 5 + suspicious * 2

        # AbuseIPDB
        abuse_score = source_data.get("abuse_confidence_score", 0)
        score += abuse_score * 0.4

        if source_data.get("is_tor"):
            score += 10

        # Shodan vulns
        vulns = source_data.get("vulns", [])
        score += min(len(vulns) * 8, 40)

        # Reputation (negative = bad on VT)
        reputation = source_data.get("reputation", 0)
        if reputation < 0:
            score += min(abs(reputation) * 0.5, 20)

    return min(round(score, 2), 100.0)


def _score_to_level(score: float) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL
    elif score >= 50:
        return RiskLevel.HIGH
    elif score >= 25:
        return RiskLevel.MEDIUM
    elif score > 0:
        return RiskLevel.LOW
    return RiskLevel.UNKNOWN


async def _run_enrichment(ioc: IoC) -> dict:
    tasks = {}

    if ioc.ioc_type == IoCType.IP:
        tasks["virustotal"] = virustotal.enrich_ip(ioc.value)
        tasks["abuseipdb"] = abuseipdb.enrich_ip(ioc.value)
        tasks["shodan"] = shodan.enrich_ip(ioc.value)

    elif ioc.ioc_type == IoCType.DOMAIN:
        tasks["virustotal"] = virustotal.enrich_domain(ioc.value)

    elif ioc.ioc_type == IoCType.FILE_HASH:
        tasks["virustotal"] = virustotal.enrich_hash(ioc.value)

    elif ioc.ioc_type == IoCType.URL:
        tasks["virustotal"] = virustotal.enrich_url(ioc.value)

    results = {}
    if tasks:
        gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for key, result in zip(tasks.keys(), gathered):
            if isinstance(result, Exception) or result is None:
                continue
            results[key] = result

    return results


def enrich_ioc(ioc_id: int) -> None:
    """Synchronous wrapper called from FastAPI background tasks."""
    db: Session = SessionLocal()
    try:
        ioc = db.query(IoC).filter(IoC.id == ioc_id).first()
        if not ioc:
            return

        enrichment = asyncio.run(_run_enrichment(ioc))
        score = _compute_risk_score(enrichment, ioc.ioc_type)
        level = _score_to_level(score)

        ioc.enrichment_data = json.dumps(enrichment)
        ioc.risk_score = score
        ioc.risk_level = level
        ioc.last_enriched_at = datetime.utcnow()
        db.commit()

        # Trigger alert if high risk
        create_alert_if_needed(db, ioc)
    finally:
        db.close()
