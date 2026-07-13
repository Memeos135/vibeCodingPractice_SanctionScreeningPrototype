import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.ai.analyzer import analyze_match
from app.database import SessionLocal
from app.models.case import Case

router = APIRouter()


class AnalyzeRequest(BaseModel):
    case_id: str
    match_index: int


class AnalyzeResponse(BaseModel):
    status: str
    analysis: Optional[dict] = None
    error: Optional[str] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_match_endpoint(req: AnalyzeRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == req.case_id).first()
    if not case:
        return AnalyzeResponse(status="error", error="Case not found")

    if not case.matches_json:
        return AnalyzeResponse(status="error", error="No matches found on case")

    try:
        matches = json.loads(case.matches_json)
    except json.JSONDecodeError:
        return AnalyzeResponse(status="error", error="Invalid matches data")

    if req.match_index < 0 or req.match_index >= len(matches):
        return AnalyzeResponse(status="error", error="Invalid match index")

    match = matches[req.match_index]

    try:
        analysis = await analyze_match(
            query_name=case.query_name or "",
            query_type=case.query_entity_type,
            query_country=None,
            match=match,
        )
    except Exception as e:
        return AnalyzeResponse(status="error", error=f"Analysis failed: {str(e)}")

    return AnalyzeResponse(status="analyzed", analysis=analysis)
