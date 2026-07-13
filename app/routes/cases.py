import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.case import Case

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class NotesUpdate(BaseModel):
    notes: str


@router.get("/cases")
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    result = []
    for c in cases:
        result.append({
            "id": c.id,
            "query_name": c.query_name,
            "query_id_type": c.query_id_type,
            "query_id_value": c.query_id_value,
            "query_entity_type": c.query_entity_type,
            "status": c.status,
            "selected_match_id": c.selected_match_id,
            "decision": c.decision,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        })
    return {"cases": result}


@router.get("/cases/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {
        "case": {
            "id": case.id,
            "query_name": case.query_name,
            "query_id_type": case.query_id_type,
            "query_id_value": case.query_id_value,
            "query_entity_type": case.query_entity_type,
            "status": case.status,
            "matches_json": json.loads(case.matches_json) if case.matches_json else None,
            "selected_match_id": case.selected_match_id,
            "decision": case.decision,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        }
    }


@router.patch("/cases/{case_id}")
def update_case_notes(case_id: str, body: NotesUpdate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.notes = body.notes
    db.commit()
    return {"status": "ok", "case_id": case_id, "notes": case.notes}
