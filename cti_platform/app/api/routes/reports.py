from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from app.core.database import get_db
from app.models.report import Report, ReportStatus
from app.schemas.report import ReportCreate, ReportResponse, ReportDetailResponse
from app.services.reporting import generate_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(
    data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    import json
    report = Report(
        title=data.title,
        description=data.description,
        format=data.format,
        filters=json.dumps(data.filters) if data.filters else None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    background_tasks.add_task(generate_report, report.id)
    return report


@router.get("/", response_model=List[ReportResponse])
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ReportStatus.READY:
        raise HTTPException(status_code=400, detail=f"Report not ready (status: {report.status})")
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(
        report.file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(report.file_path),
    )
