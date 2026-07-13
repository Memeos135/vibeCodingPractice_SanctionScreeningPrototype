from fastapi import APIRouter, Depends
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


@router.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Case).count()
    open_count = db.query(Case).filter(Case.status == "open").count()
    blocked = db.query(Case).filter(Case.status == "blocked").count()
    cleared = db.query(Case).filter(Case.status == "cleared").count()
    resolved = blocked + cleared
    match_rate = round(blocked / resolved * 100, 1) if resolved > 0 else 0
    recent = db.query(Case).order_by(Case.created_at.desc()).limit(10).all()

    recent_cases = []
    for c in recent:
        recent_cases.append({
            "id": c.id,
            "query_name": c.query_name,
            "status": c.status,
            "decision": c.decision,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        })

    return {
        "total_cases": total,
        "open": open_count,
        "blocked": blocked,
        "cleared": cleared,
        "match_rate": match_rate,
        "recent_cases": recent_cases,
    }
