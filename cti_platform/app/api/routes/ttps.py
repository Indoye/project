from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.ioc import TTP
from app.schemas.ioc import TTPBase, TTPResponse

router = APIRouter(prefix="/ttps", tags=["MITRE ATT&CK"])


@router.post("/", response_model=TTPResponse, status_code=201)
def create_ttp(data: TTPBase, db: Session = Depends(get_db)):
    existing = db.query(TTP).filter(TTP.technique_id == data.technique_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="TTP already exists")
    ttp = TTP(**data.model_dump())
    db.add(ttp)
    db.commit()
    db.refresh(ttp)
    return ttp


@router.get("/", response_model=List[TTPResponse])
def list_ttps(
    tactic: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(TTP)
    if tactic:
        q = q.filter(TTP.tactic.ilike(f"%{tactic}%"))
    if search:
        q = q.filter(
            TTP.name.contains(search) | TTP.technique_id.contains(search)
        )
    return q.offset(skip).limit(limit).all()


@router.get("/{technique_id}", response_model=TTPResponse)
def get_ttp(technique_id: str, db: Session = Depends(get_db)):
    ttp = db.query(TTP).filter(TTP.technique_id == technique_id.upper()).first()
    if not ttp:
        raise HTTPException(status_code=404, detail="TTP not found")
    return ttp


@router.post("/{technique_id}/iocs/{ioc_id}", status_code=200)
def link_ioc_to_ttp(technique_id: str, ioc_id: int, db: Session = Depends(get_db)):
    from app.models.ioc import IoC
    ttp = db.query(TTP).filter(TTP.technique_id == technique_id.upper()).first()
    ioc = db.query(IoC).filter(IoC.id == ioc_id).first()
    if not ttp or not ioc:
        raise HTTPException(status_code=404, detail="TTP or IoC not found")
    if ioc not in ttp.iocs:
        ttp.iocs.append(ioc)
        db.commit()
    return {"message": f"IoC {ioc_id} linked to {technique_id}"}
