from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from app.models import Sanction, SanctionReferent


def match_by_referent(db: Session, referent: str) -> Optional[List[Sanction]]:
    if not referent or not referent.strip():
        return None
    ref_value = referent.strip()
    rows = (
        db.query(SanctionReferent)
        .filter(SanctionReferent.referent == ref_value)
        .options(joinedload(SanctionReferent.sanction))
        .all()
    )
    if not rows:
        return None
    return [r.sanction for r in rows]


def match_by_referents(db: Session, referents: List[str]) -> List[Sanction]:
    cleaned = [r.strip() for r in referents if r and r.strip()]
    if not cleaned:
        return []
    rows = (
        db.query(SanctionReferent)
        .filter(SanctionReferent.referent.in_(cleaned))
        .options(joinedload(SanctionReferent.sanction))
        .all()
    )
    seen = set()
    results = []
    for r in rows:
        if r.sanction_id not in seen:
            seen.add(r.sanction_id)
            results.append(r.sanction)
    return results


def match_by_source(db: Session, source: str, ref_value: str) -> Optional[List[Sanction]]:
    if not ref_value or not ref_value.strip():
        return None
    ref_value = ref_value.strip()
    source = source.strip() if source else ""
    full = f"{source}-{ref_value}" if source else ref_value
    return match_by_referent(db, full)


def format_match_response(sanction: Sanction, referent: str) -> dict:
    return {
        "status": "exact",
        "decision": "blocked",
        "match": {
            "id": sanction.id,
            "caption": sanction.caption,
            "schema_type": sanction.schema_type,
            "referent": referent,
            "country": sanction.country,
            "program": sanction.program_id,
            "topics": [t.strip() for t in sanction.topics.split(",") if t.strip()] if sanction.topics else [],
            "notes": sanction.notes,
        },
    }
