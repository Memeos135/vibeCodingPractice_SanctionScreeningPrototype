from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.case import Case
from app.schemas import ResolveResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/resolve")
def resolve_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    case_id: str = Form(...),
    match_id: str = Form(...),
    decision: str = Form(...),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if decision == "approve":
        case.status = "blocked"
    elif decision == "reject":
        case.status = "cleared"
    else:
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")

    case.selected_match_id = match_id
    case.decision = decision
    case.resolved_at = datetime.utcnow()
    db.commit()

    if request.headers.get("hx-request") == "true":
        return Response(
            status_code=200,
            headers={"HX-Redirect": "/cases"},
        )

    return ResolveResponse(
        status="resolved",
        decision=case.status,
        case_id=case.id,
    )
