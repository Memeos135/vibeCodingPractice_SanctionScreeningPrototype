import json

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.database import SessionLocal
from app.models.case import Case

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/cases")
def cases_list(request: Request):
    db = SessionLocal()
    try:
        rows = db.query(Case).order_by(Case.created_at.desc()).all()
        items = []
        for c in rows:
            items.append({
                "id": c.id,
                "query_name": c.query_name,
                "query_id_type": c.query_id_type,
                "query_id_value": c.query_id_value,
                "query_entity_type": c.query_entity_type,
                "status": c.status,
                "decision": c.decision,
                "notes": c.notes,
                "matches": json.loads(c.matches_json) if c.matches_json else [],
                "selected_match_id": c.selected_match_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            })
    finally:
        db.close()
    return templates.TemplateResponse("cases.html", {"request": request, "cases": items})


@router.get("/cases/{case_id}")
def case_detail_redirect(case_id: str):
    return RedirectResponse(url="/cases")


@router.get("/dashboard")
def dashboard(request: Request):
    db = SessionLocal()
    try:
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

        stats = {
            "total_cases": total,
            "open": open_count,
            "blocked": blocked,
            "cleared": cleared,
            "match_rate": match_rate,
            "recent_cases": recent_cases,
        }
    finally:
        db.close()
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats})
