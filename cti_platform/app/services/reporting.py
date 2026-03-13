"""
Report generation service: produces JSON and PDF reports.
"""
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.report import Report, ReportFormat, ReportStatus
from app.models.ioc import IoC, RiskLevel
from app.models.alert import Alert, AlertStatus

REPORTS_DIR = "/tmp/cti_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def _build_report_data(db: Session, filters: dict) -> dict:
    q = db.query(IoC)
    if filters.get("risk_level"):
        q = q.filter(IoC.risk_level == filters["risk_level"])
    if filters.get("ioc_type"):
        q = q.filter(IoC.ioc_type == filters["ioc_type"])
    if filters.get("is_active") is not None:
        q = q.filter(IoC.is_active == filters["is_active"])

    iocs = q.order_by(IoC.risk_score.desc()).limit(filters.get("limit", 500)).all()

    open_alerts = db.query(Alert).filter(Alert.status == AlertStatus.OPEN).count()

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "filters_applied": filters,
        "summary": {
            "total_iocs": len(iocs),
            "critical": sum(1 for i in iocs if i.risk_level == RiskLevel.CRITICAL),
            "high": sum(1 for i in iocs if i.risk_level == RiskLevel.HIGH),
            "medium": sum(1 for i in iocs if i.risk_level == RiskLevel.MEDIUM),
            "low": sum(1 for i in iocs if i.risk_level == RiskLevel.LOW),
            "open_alerts": open_alerts,
        },
        "iocs": [
            {
                "id": ioc.id,
                "value": ioc.value,
                "type": ioc.ioc_type.value,
                "risk_level": ioc.risk_level.value,
                "risk_score": ioc.risk_score,
                "source": ioc.source,
                "tags": ioc.tags,
                "ttps": [t.technique_id for t in ioc.ttps],
                "last_enriched_at": ioc.last_enriched_at.isoformat() if ioc.last_enriched_at else None,
                "created_at": ioc.created_at.isoformat(),
            }
            for ioc in iocs
        ],
    }


def _generate_pdf(data: dict, path: str) -> None:
    """Generate a simple PDF report using ReportLab (optional dependency)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("CTI Platform — Rapport de Menaces", styles["Title"]))
        elements.append(Paragraph(f"Généré le: {data['generated_at']}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        summary = data["summary"]
        summary_data = [
            ["Métrique", "Valeur"],
            ["Total IoCs", str(summary["total_iocs"])],
            ["Critiques", str(summary["critical"])],
            ["Élevés", str(summary["high"])],
            ["Moyens", str(summary["medium"])],
            ["Faibles", str(summary["low"])],
            ["Alertes ouvertes", str(summary["open_alerts"])],
        ]
        t = Table(summary_data, colWidths=[200, 100])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("IoCs les plus risqués", styles["Heading2"]))
        ioc_data = [["Valeur", "Type", "Risque", "Score", "TTPs"]]
        for ioc in data["iocs"][:50]:
            ioc_data.append([
                ioc["value"][:40],
                ioc["type"],
                ioc["risk_level"],
                str(ioc["risk_score"]),
                ", ".join(ioc["ttps"][:3]),
            ])
        ioc_table = Table(ioc_data, colWidths=[150, 60, 60, 50, 100])
        ioc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        elements.append(ioc_table)
        doc.build(elements)
    except ImportError:
        # If reportlab not installed, write a text-based "PDF"
        with open(path, "w") as f:
            f.write(f"CTI Report — {data['generated_at']}\n\n")
            f.write(json.dumps(data, indent=2))


def generate_report(report_id: int) -> None:
    db: Session = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        report.status = ReportStatus.GENERATING
        db.commit()

        filters = json.loads(report.filters) if report.filters else {}
        data = _build_report_data(db, filters)

        if report.format == ReportFormat.JSON:
            report.content = json.dumps(data, indent=2)
            report.status = ReportStatus.READY

        elif report.format == ReportFormat.CSV:
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["value", "type", "risk_level", "risk_score", "source", "tags", "ttps"],
            )
            writer.writeheader()
            for ioc in data["iocs"]:
                writer.writerow({
                    "value": ioc["value"],
                    "type": ioc["type"],
                    "risk_level": ioc["risk_level"],
                    "risk_score": ioc["risk_score"],
                    "source": ioc["source"] or "",
                    "tags": ioc["tags"] or "",
                    "ttps": ";".join(ioc["ttps"]),
                })
            path = os.path.join(REPORTS_DIR, f"report_{report_id}.csv")
            with open(path, "w") as f:
                f.write(output.getvalue())
            report.file_path = path
            report.status = ReportStatus.READY

        elif report.format == ReportFormat.PDF:
            path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
            _generate_pdf(data, path)
            report.file_path = path
            report.status = ReportStatus.READY

        report.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        if report:
            report.status = ReportStatus.FAILED
            db.commit()
    finally:
        db.close()
