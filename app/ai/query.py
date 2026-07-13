import re

from typing import Optional

import httpx
from sqlalchemy import text

from app.ai.ollama import OllamaClient
from app.ai.prompts import NL_QUERY_SYSTEM
from app.database import SessionLocal


FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)\b", re.IGNORECASE
)


def _is_safe_select(sql: str) -> bool:
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        return False
    if FORBIDDEN_KEYWORDS.search(sql):
        return False
    return True


async def nl_to_sql(
    question: str, client: Optional[OllamaClient] = None
) -> str:
    if client is None:
        client = OllamaClient()
    sql = await client.generate(question, system=NL_QUERY_SYSTEM)
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.splitlines()
        lines = [l for l in lines if not l.startswith("```")]
        sql = "\n".join(lines).strip()
    return sql


async def execute_nl_query(
    question: str, client: Optional[OllamaClient] = None
) -> dict:
    try:
        sql = await nl_to_sql(question, client=client)
    except Exception as e:
        if isinstance(e, httpx.ConnectError):
            err = "Ollama is not running. Start it with: ollama serve"
        else:
            err = str(e)
        return {
            "sql": None,
            "columns": [],
            "rows": [],
            "error": f"Failed to generate SQL: {err}",
        }

    if not _is_safe_select(sql):
        return {
            "sql": sql,
            "columns": [],
            "rows": [],
            "error": "Only SELECT queries are allowed.",
        }

    db = None
    try:
        db = SessionLocal()
        result = db.execute(text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        return {
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "error": None,
        }
    except Exception as e:
        return {
            "sql": sql,
            "columns": [],
            "rows": [],
            "error": f"Query execution failed: {str(e)}",
        }
    finally:
        if db is not None:
            db.close()
