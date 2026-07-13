from typing import Optional

from app.ai.ollama import OllamaClient
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from app.ai.prompts import MATCH_ANALYSIS_SYSTEM, MATCH_ANALYSIS_USER


async def analyze_match(
    query_name: str,
    query_type: Optional[str],
    query_country: Optional[str],
    match: dict,
    client: Optional[OllamaClient] = None,
) -> dict:
    if client is None:
        client = OllamaClient(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, timeout=OLLAMA_TIMEOUT)

    prompt = MATCH_ANALYSIS_USER.format(
        query_name=query_name or "N/A",
        query_type=query_type or "N/A",
        query_country=query_country or "N/A",
        match_name=match.get("caption", "N/A"),
        match_type=match.get("schema_type", "N/A"),
        match_country=match.get("country", "N/A"),
        match_program=match.get("program", "N/A"),
        match_topics=", ".join(match.get("topics", [])),
        match_notes=match.get("notes", "N/A"),
    )

    result = await client.generate_json(prompt, system=MATCH_ANALYSIS_SYSTEM)
    return result


async def check_ollama_health() -> dict:
    client = OllamaClient()
    available = await client.check_available()
    model_ok = await client.is_model_available() if available else False
    return {
        "available": available,
        "model_available": model_ok,
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_BASE_URL,
    }
