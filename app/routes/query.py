from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.ai.query import execute_nl_query

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class QueryRequest(BaseModel):
    question: str


@router.get("/query", response_class=HTMLResponse)
async def query_page(request: Request):
    return templates.TemplateResponse("query.html", {"request": request})


@router.post("/api/query")
async def run_query(req: QueryRequest):
    result = await execute_nl_query(req.question)
    return result
