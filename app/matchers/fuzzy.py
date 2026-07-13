from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from .scorer import (
    combined_score,
    token_set_ratio,
    partial_ratio,
    soundex_match,
    metaphone_match,
)


def _normalize(s: str) -> str:
    s = s.strip().upper()
    s = re.sub(r"\s+", " ", s)
    return s


def _split_words(s: str) -> list[str]:
    return _normalize(s).split()


def _parse_topics(topics_str: Optional[str]) -> list[str]:
    if not topics_str:
        return []
    return [t.strip() for t in topics_str.split(",") if t.strip()]


def prefilter_candidates(
    db: Session,
    query_name: str,
    min_share: float = 0.3,
    schema_filter: Optional[str] = None,
):
    query = _normalize(query_name)
    if not query:
        return []

    words = _split_words(query_name)
    if not words:
        return []

    params = {}

    if len(query) <= 3:
        conditions = ["sn.name LIKE :q_prefix"]
        params["q_prefix"] = query + "%"
    else:
        conds = []
        for i, w in enumerate(words):
            key = f"w{i}"
            if len(w) <= 3:
                conds.append(f"sn.name LIKE :{key}")
                params[key] = w + "%"
            else:
                conds.append(f"sn.name LIKE :{key}")
                params[key] = f"%{w}%"
        conditions = ["(" + " OR ".join(conds) + ")"]

    if schema_filter:
        conditions.append("s.schema_type = :schema_filter")
        params["schema_filter"] = schema_filter

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT sn.id, sn.sanction_id, sn.name, sn.name_type,
               s.caption, s.schema_type, s.country, s.program_id, s.topics
        FROM sanction_names sn
        JOIN sanctions s ON s.id = sn.sanction_id
        WHERE {where_clause}
    """

    result = db.execute(text(sql), params)
    return result.fetchall()


def fuzzy_match(
    db: Session,
    query_name: str,
    threshold: float = 70.0,
    max_results: int = 20,
    schema_filter: Optional[str] = None,
) -> list[dict]:
    query = _normalize(query_name)
    if not query:
        return []

    candidates = prefilter_candidates(db, query_name, schema_filter=schema_filter)

    scored = []
    for row in candidates:
        candidate_name = row.name
        sc = combined_score(query, candidate_name)
        if sc >= threshold:
            scored.append(
                {
                    "sanction_id": row.sanction_id,
                    "caption": row.caption,
                    "schema_type": row.schema_type,
                    "matched_name": candidate_name,
                    "match_type": row.name_type,
                    "score": sc,
                    "scores": {
                        "token_set": token_set_ratio(query, candidate_name),
                        "partial": partial_ratio(query, candidate_name),
                        "soundex": soundex_match(query, candidate_name) * 100,
                        "metaphone": metaphone_match(query, candidate_name) * 100,
                    },
                    "country": row.country,
                    "program": row.program_id,
                    "topics": _parse_topics(row.topics),
                }
            )

    scored.sort(key=lambda r: r["score"], reverse=True)

    seen = set()
    deduped = []
    for r in scored:
        sid = r["sanction_id"]
        if sid not in seen:
            seen.add(sid)
            deduped.append(r)

    return deduped[:max_results]
