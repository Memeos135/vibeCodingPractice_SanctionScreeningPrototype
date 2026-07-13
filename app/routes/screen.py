import json
import uuid

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.matchers.exact import match_by_source, format_match_response
from app.matchers.fuzzy import fuzzy_match
from app.models.case import Case
from app.schemas import ScreenResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/screen")
def screen_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    id_type: Optional[str] = Form(None),
    id_value: Optional[str] = Form(None),
    entity_type: Optional[str] = Form(None),
):
    if id_type and id_value:
        sanctions = match_by_source(db, id_type, id_value)
        if sanctions:
            sanc = sanctions[0]
            ref = f"{id_type}-{id_value}"
            resp = format_match_response(sanc, ref)
            if request.headers.get("hx-request") == "true":
                return templates.TemplateResponse(
                    "partials/_screen_result.html",
                    {"request": request, "status": "exact", "match": resp["match"]},
                )
            return ScreenResponse(
                status="exact",
                decision="blocked",
                match=resp["match"],
            )

    if name:
        matches = fuzzy_match(
            db, name,
            schema_filter=entity_type,
            threshold=70.0,
        )
        if matches:
            case = Case(
                id=str(uuid.uuid4()),
                query_name=name,
                query_id_type=id_type,
                query_id_value=id_value,
                query_entity_type=entity_type,
                status="open",
                matches_json=json.dumps(matches, default=str),
            )
            db.add(case)
            db.commit()
            if request.headers.get("hx-request") == "true":
                return templates.TemplateResponse(
                    "partials/_screen_result.html",
                    {"request": request, "status": "fuzzy", "matches": matches, "case_id": case.id},
                )
            return ScreenResponse(
                status="fuzzy",
                case_id=case.id,
                matches=matches,
            )

    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(
            "partials/_screen_result.html",
            {"request": request, "status": "clear"},
        )
    return ScreenResponse(status="clear")
