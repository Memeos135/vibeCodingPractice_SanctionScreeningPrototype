from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import csv
import io
import json
from typing import Optional

from app.ai.analyzer import analyze_match
from app.database import SessionLocal
from app.matchers.fuzzy import fuzzy_match

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/batch", response_class=HTMLResponse)
async def batch_page(request: Request):
    return templates.TemplateResponse("batch.html", {"request": request})


@router.post("/batch/generate", response_class=HTMLResponse)
async def batch_generate(
    request: Request,
    count: int = Form(5),
    use_ai: bool = Form(False),
    db: Session = Depends(get_db),
):
    from sqlalchemy import text
    count = max(1, min(count, 50))
    result = db.execute(
        text("SELECT DISTINCT name FROM sanction_names ORDER BY RANDOM() LIMIT :n"),
        {"n": count},
    )
    names = [row[0] for row in result.fetchall()]

    results = []
    for row_num, name in enumerate(names, start=1):
        try:
            matches = fuzzy_match(db, name, threshold=70.0)
        except Exception as e:
            results.append({
                "row": row_num, "name": name, "status": "error",
                "message": str(e), "match_count": 0, "matches": [],
                "ai_analysis": None,
            })
            continue

        if not matches:
            results.append({
                "row": row_num, "name": name, "status": "clear",
                "message": None, "match_count": 0, "matches": [],
                "ai_analysis": None,
            })
            continue

        ai_analysis = None
        if use_ai:
            try:
                ai_analysis = await analyze_match(
                    query_name=name,
                    query_type=None,
                    query_country=None,
                    match=matches[0],
                )
            except Exception as e:
                ai_analysis = {"error": str(e)}

        results.append({
            "row": row_num, "name": name, "status": "fuzzy",
            "message": None, "match_count": len(matches),
            "matches": matches[:5], "ai_analysis": ai_analysis,
        })

    return templates.TemplateResponse(
        "partials/_batch_results.html",
        {"request": request, "results": results, "use_ai": use_ai},
    )


@router.post("/batch/upload", response_class=HTMLResponse)
async def batch_upload(
    request: Request,
    file: UploadFile = File(...),
    use_ai: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    use_ai_flag = use_ai == "true"
    content = await file.read()
    filename = file.filename or ""

    if filename.endswith(".json"):
        rows = json.loads(content.decode("utf-8"))
    else:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

    results = []
    for row_num, row in enumerate(rows, start=1):
        name = (row.get("name") or "").strip()
        if not name:
            results.append({
                "row": row_num,
                "name": "",
                "status": "error",
                "message": "Empty name",
                "match_count": 0,
                "matches": [],
                "ai_analysis": None,
            })
            continue

        entity_type = row.get("entity_type") or None

        try:
            matches = fuzzy_match(db, name, schema_filter=entity_type, threshold=70.0)
        except Exception as e:
            results.append({
                "row": row_num,
                "name": name,
                "status": "error",
                "message": str(e),
                "match_count": 0,
                "matches": [],
                "ai_analysis": None,
            })
            continue

        if not matches:
            results.append({
                "row": row_num,
                "name": name,
                "status": "clear",
                "message": None,
                "match_count": 0,
                "matches": [],
                "ai_analysis": None,
            })
            continue

        ai_analysis = None
        if use_ai_flag:
            try:
                ai_analysis = await analyze_match(
                    query_name=name,
                    query_type=row.get("id_type") or None,
                    query_country=None,
                    match=matches[0],
                )
            except Exception as e:
                ai_analysis = {"error": str(e)}

        results.append({
            "row": row_num,
            "name": name,
            "status": "fuzzy",
            "message": None,
            "match_count": len(matches),
            "matches": matches[:5],
            "ai_analysis": ai_analysis,
        })

    return templates.TemplateResponse(
        "partials/_batch_results.html",
        {"request": request, "results": results, "use_ai": use_ai_flag},
    )
