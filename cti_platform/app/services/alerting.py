"""
Alerting service: auto-creates alerts based on IoC risk score
and dispatches notifications via email and/or Slack.
"""
import smtplib
import json
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.ioc import IoC, RiskLevel
from app.models.alert import Alert, AlertSeverity, AlertStatus


def _risk_to_severity(risk_level: RiskLevel) -> AlertSeverity:
    mapping = {
        RiskLevel.CRITICAL: AlertSeverity.CRITICAL,
        RiskLevel.HIGH: AlertSeverity.HIGH,
        RiskLevel.MEDIUM: AlertSeverity.MEDIUM,
        RiskLevel.LOW: AlertSeverity.LOW,
    }
    return mapping.get(risk_level, AlertSeverity.LOW)


def create_alert_if_needed(db: Session, ioc: IoC) -> None:
    """Create an alert when an IoC reaches HIGH or CRITICAL risk."""
    settings = get_settings()
    if ioc.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        return

    # Avoid duplicate open alerts for the same IoC
    existing = (
        db.query(Alert)
        .filter(Alert.ioc_id == ioc.id, Alert.status == AlertStatus.OPEN)
        .first()
    )
    if existing:
        return

    severity = _risk_to_severity(ioc.risk_level)
    alert = Alert(
        title=f"[{severity.value.upper()}] IoC détecté: {ioc.value}",
        description=(
            f"Type: {ioc.ioc_type.value} | Score: {ioc.risk_score}/100\n"
            f"Source: {ioc.source or 'N/A'} | Tags: {ioc.tags or 'N/A'}"
        ),
        severity=severity,
        ioc_id=ioc.id,
        triggered_by="enrichment_auto",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Send notifications
    _notify(alert, ioc, settings)


def _notify(alert: Alert, ioc: IoC, settings) -> None:
    if settings.slack_webhook_url:
        _send_slack(alert, ioc, settings.slack_webhook_url)
    if settings.smtp_host and settings.alert_email_to:
        _send_email(alert, ioc, settings)


def _send_slack(alert: Alert, ioc: IoC, webhook_url: str) -> None:
    color = {"critical": "#FF0000", "high": "#FF6600", "medium": "#FFD700", "low": "#36A64F"}
    payload = {
        "attachments": [
            {
                "color": color.get(alert.severity.value, "#808080"),
                "title": alert.title,
                "text": alert.description,
                "fields": [
                    {"title": "IoC", "value": ioc.value, "short": True},
                    {"title": "Risk Score", "value": str(ioc.risk_score), "short": True},
                    {"title": "Type", "value": ioc.ioc_type.value, "short": True},
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                ],
                "footer": "CTI Platform",
            }
        ]
    }
    try:
        httpx.post(webhook_url, json=payload, timeout=10)
    except Exception:
        pass


def _send_email(alert: Alert, ioc: IoC, settings) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[CTI Alert] {alert.title}"
    msg["From"] = settings.smtp_user
    msg["To"] = settings.alert_email_to

    body = f"""
    <h2 style="color: red;">CTI Platform — Alerte de Sécurité</h2>
    <p><strong>Titre:</strong> {alert.title}</p>
    <p><strong>Sévérité:</strong> {alert.severity.value.upper()}</p>
    <p><strong>IoC:</strong> {ioc.value} ({ioc.ioc_type.value})</p>
    <p><strong>Score de risque:</strong> {ioc.risk_score}/100</p>
    <p><strong>Description:</strong> {alert.description}</p>
    <hr>
    <p>Consultez votre plateforme CTI pour plus de détails.</p>
    """
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, settings.alert_email_to, msg.as_string())
    except Exception:
        pass
