import json
import logging
import time
from collections import defaultdict

from app.config import DATA_PATH, BATCH_SIZE
from app.database import Base, SessionLocal, engine
from app.models import Dataset, Sanction, SanctionName, SanctionReferent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_total_lines():
    """Quick pass to count total lines (for progress %)."""
    count = 0
    with open(str(DATA_PATH), "rb") as f:
        for _ in f:
            count += 1
    return count


def _extract_source(referent_str):
    """Derive a short source name from a referent ID (prefix before first hyphen)."""
    if not referent_str:
        return None
    parts = referent_str.split("-", 1)
    return parts[0].strip() if parts[0].strip() else None


def ingest():
    """Stream-read JSONL, filter target=true, insert into SQLite."""
    start = time.time()

    # Re-create tables for idempotency
    logger.info("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    total_lines = 0
    imported = 0
    errors = 0
    schema_counts = defaultdict(int)
    dataset_counts = defaultdict(int)

    logger.info("Starting ingestion from %s", DATA_PATH)

    with open(str(DATA_PATH), "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1

            if total_lines % 100000 == 0:
                logger.info(
                    "Progress: %s lines processed, %s imported",
                    f"{total_lines:,}",
                    f"{imported:,}",
                )

            # Parse JSON
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors += 1
                if errors <= 10:
                    logger.warning("JSON decode error at line %s: %s", total_lines, e)
                continue

            # Only sanctioned targets
            if not obj.get("target"):
                continue

            # --- Extract fields ---
            entity_id = obj.get("id")
            if not entity_id:
                continue

            caption = obj.get("caption") or ""

            schema_type = obj.get("schema") or "Unknown"

            props = obj.get("properties") or {}

            # Timestamps
            first_seen = _parse_ts(obj.get("first_seen"))
            last_seen = _parse_ts(obj.get("last_seen"))
            last_change = _parse_ts(obj.get("last_change"))

            # Comma-joined fields
            country = _join_list(props.get("country"))
            program_id = _join_list(props.get("programId"))
            topics = _join_list(props.get("topics"))

            # Notes: try several possible property keys, then caption fallback
            notes = _get_notes(props, caption)

            # Build sanction record
            sanction = Sanction(
                id=entity_id,
                caption=caption,
                schema_type=schema_type,
                target=True,
                first_seen=first_seen,
                last_seen=last_seen,
                last_change=last_change,
                country=country,
                program_id=program_id,
                topics=topics,
                notes=notes,
            )
            db.add(sanction)

            # --- Names (caption + name[] + alias[]) ---
            if caption:
                db.add(SanctionName(
                    sanction_id=entity_id,
                    name=caption,
                    name_type="caption",
                ))

            for raw_name in (props.get("name") or []):
                if raw_name and raw_name.strip():
                    db.add(SanctionName(
                        sanction_id=entity_id,
                        name=raw_name.strip(),
                        name_type="name",
                    ))

            for raw_alias in (props.get("alias") or []):
                if raw_alias and raw_alias.strip():
                    db.add(SanctionName(
                        sanction_id=entity_id,
                        name=raw_alias.strip(),
                        name_type="alias",
                    ))

            # --- Referents ---
            referents = obj.get("referents") or []
            for ref in referents:
                if ref and ref.strip():
                    source = _extract_source(ref)
                    db.add(SanctionReferent(
                        sanction_id=entity_id,
                        referent=ref.strip(),
                        source=source,
                    ))

            # --- Dataset counts ---
            datasets = obj.get("datasets") or []
            for ds in datasets:
                if ds:
                    dataset_counts[ds] += 1

            # --- Schema counts ---
            schema_counts[schema_type] += 1

            imported += 1

            # Batch commit
            if imported % BATCH_SIZE == 0:
                try:
                    db.commit()
                except Exception as e:
                    logger.error("Batch commit error at %s imported: %s", imported, e)
                    db.rollback()

    # Final commit
    try:
        db.commit()
    except Exception as e:
        logger.error("Final commit error: %s", e)
        db.rollback()

    # --- Populate datasets table ---
    for ds_name, count in sorted(dataset_counts.items(), key=lambda x: -x[1]):
        db.add(Dataset(name=ds_name, entity_count=count))
    try:
        db.commit()
    except Exception as e:
        logger.error("Datasets commit error: %s", e)
        db.rollback()

    db.close()

    elapsed = time.time() - start
    _report_stats(
        total_lines, imported, errors, elapsed,
        schema_counts, dataset_counts,
    )


def _parse_ts(val):
    if val is None:
        return None
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        # Try ISO format with possible trailing Z
        from datetime import datetime
        try:
            if val.endswith("Z"):
                val = val[:-1] + "+00:00"
            return datetime.fromisoformat(val)
        except (ValueError, TypeError):
            return None
    return val


def _join_list(items):
    if not items:
        return None
    return ", ".join(str(x) for x in items if x is not None)


def _get_notes(props, caption):
    candidates = ["notes", "summary", "notes2", "remarks", "description"]
    parts = []
    for key in candidates:
        vals = props.get(key)
        if vals:
            for v in vals:
                if v and str(v).strip():
                    parts.append(str(v).strip())
    if parts:
        return "\n".join(parts)
    return caption if caption else None


def _report_stats(
    total_lines, imported, errors, elapsed,
    schema_counts, dataset_counts,
):
    from datetime import timedelta

    # Get DB file size
    from app.config import DB_PATH
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0

    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 60)
    logger.info("  Total lines processed:  %s", f"{total_lines:,}")
    logger.info("  Sanctions imported:     %s", f"{imported:,}")
    logger.info("  JSON decode errors:     %s", errors)
    logger.info("  Time taken:             %s", str(timedelta(seconds=elapsed)))
    logger.info("  DB file size:           %s MB", f"{db_size / 1024 / 1024:.1f}")
    logger.info("")
    logger.info("--- Schema Type Counts ---")
    for st, cnt in sorted(schema_counts.items(), key=lambda x: -x[1]):
        logger.info("  %-20s %s", st + ":", f"{cnt:,}")
    logger.info("")
    logger.info("--- Top 10 Data Sources ---")
    for ds, cnt in sorted(dataset_counts.items(), key=lambda x: -x[1])[:10]:
        logger.info("  %-40s %s", ds + ":", f"{cnt:,}")


def main():
    ingest()


if __name__ == "__main__":
    main()
