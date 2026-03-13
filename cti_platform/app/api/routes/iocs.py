from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import get_db
from app.models.ioc import IoC, IoCType, RiskLevel
from app.schemas.ioc import IoCCreate, IoCUpdate, IoCResponse, IoCImportBulk
from app.services.enrichment_manager import enrich_ioc

router = APIRouter(prefix="/iocs", tags=["IoCs"])


@router.post("/", response_model=IoCResponse, status_code=201)
def create_ioc(
    data: IoCCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    existing = db.query(IoC).filter(IoC.value == data.value).first()
    if existing:
        raise HTTPException(status_code=409, detail="IoC already exists")

    ioc = IoC(**data.model_dump())
    db.add(ioc)
    db.commit()
    db.refresh(ioc)

    # Auto-enrich after creation
    background_tasks.add_task(enrich_ioc, ioc.id)
    return ioc


@router.post("/bulk", response_model=List[IoCResponse], status_code=201)
def bulk_import(
    data: IoCImportBulk,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    created = []
    for item in data.iocs:
        existing = db.query(IoC).filter(IoC.value == item.value).first()
        if existing:
            continue
        ioc = IoC(**item.model_dump())
        db.add(ioc)
        db.flush()
        created.append(ioc)

    db.commit()
    for ioc in created:
        background_tasks.add_task(enrich_ioc, ioc.id)
    return created


@router.get("/", response_model=List[IoCResponse])
def list_iocs(
    ioc_type: Optional[IoCType] = None,
    risk_level: Optional[RiskLevel] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(IoC)
    if ioc_type:
        q = q.filter(IoC.ioc_type == ioc_type)
    if risk_level:
        q = q.filter(IoC.risk_level == risk_level)
    if is_active is not None:
        q = q.filter(IoC.is_active == is_active)
    if search:
        q = q.filter(
            or_(
                IoC.value.contains(search),
                IoC.tags.contains(search),
                IoC.description.contains(search),
            )
        )
    return q.order_by(IoC.risk_score.desc()).offset(skip).limit(limit).all()


@router.get("/{ioc_id}", response_model=IoCResponse)
def get_ioc(ioc_id: int, db: Session = Depends(get_db)):
    ioc = db.query(IoC).filter(IoC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=404, detail="IoC not found")
    return ioc


@router.patch("/{ioc_id}", response_model=IoCResponse)
def update_ioc(ioc_id: int, data: IoCUpdate, db: Session = Depends(get_db)):
    ioc = db.query(IoC).filter(IoC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=404, detail="IoC not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ioc, field, value)
    db.commit()
    db.refresh(ioc)
    return ioc


@router.delete("/{ioc_id}", status_code=204)
def delete_ioc(ioc_id: int, db: Session = Depends(get_db)):
    ioc = db.query(IoC).filter(IoC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=404, detail="IoC not found")
    db.delete(ioc)
    db.commit()


@router.post("/{ioc_id}/enrich", response_model=IoCResponse)
async def trigger_enrichment(
    ioc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ioc = db.query(IoC).filter(IoC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=404, detail="IoC not found")
    background_tasks.add_task(enrich_ioc, ioc_id)
    return ioc
