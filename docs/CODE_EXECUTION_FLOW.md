# Code Execution Flow

Two workflows for developers: **UI Testing** (full-stack browser testing) and
**Component Testing** (isolated module/endpoint testing).

---

## 1. UI Testing Flow

End-to-end flow from fresh clone to clicking around the browser.

### 1.1 Startup

```
Terminal 1: ollama serve ─────────────────────────────► http://127.0.0.1:11434
Terminal 2: ollama pull llama3  (one-time; skip if already done)
Terminal 2: python -m uvicorn app.main:app --reload ──► http://127.0.0.1:8000
Browser:    http://localhost:8000
```

The `--reload` flag auto-restarts the server when you edit any `.py` file.

### 1.2 Home — Screen a Name

| Step | What you do | What happens | Server receives |
|------|-----------|--------------|-----------------|
| 1 | Type a name in the input field and click **Screen Now** | HTMX evaluates `hx-vals='js:{name: ..., ...}'` → POSTs form-encoded data to `/screen` | `name` (str), `id_type` (str), `id_value` (str), `entity_type` (str) |
| 2 | | `screen.py:29-35` → `Form()` params extracted from request body | |
| 3 | | `screen.py:37` → `if id_type and id_value:` checks for exact-match path | |
| 4 | | `exact.py:24-40` → Searches `sanction_referents.referent` for match. If found → `format_match_response()` returns blocked status | |
| 5 | | `screen.py:44` → `if name:` → `fuzzy_match()` called with threshold 70% | |
| 6 | | `fuzzy.py:38-54` → **prefilter**: SQL `SELECT DISTINCT s.id WHERE name LIKE '%query%'` | reads `sanction_names` table |
| 7 | | `fuzzy.py:62-86` → For each candidate, `combined_score()` runs 4 sub-scorers | |
| 8 | | `scorer.py:17-19` → `token_set_ratio(query, name)` from thefuzz (weight 0.40) | |
| 9 | | `scorer.py:20` → `partial_ratio(query, name)` from thefuzz (weight 0.30) | |
| 10 | | `scorer.py:21` → `soundex_match(query, name) × 100` from jellyfish (weight 0.15) | |
| 11 | | `scorer.py:22` → `metaphone_match(query, name) × 100` from jellyfish (weight 0.15) | |
| 12 | | `scorer.py:24` → weighted sum → 0–100 score | |
| 13 | | `fuzzy.py:99-100` → Only candidates with `score >= 70` kept | |
| 14 | If matches found | `screen.py:51-62` → `Case` created with UUID, `matches_json=json.dumps(matches)`, status=`"open"` | writes to `cases` table |
| 15 | | `screen.py:63-66` → HTMX response: `_screen_result.html` with match cards rendered | returns HTML to browser |
| 16 | In browser | Green/yellow/red score badge + score breakdown bars + Confirm/Not a Match buttons | |
| 17 | Click **Confirm Match** | HTMX POSTs to `/resolve` with `case_id`, `match_id`, `decision="approve"` | |
| 18 | | `resolve.py:35-36` → `case.status = "blocked"`, `case.decision = "approve"`, `case.resolved_at = now()` | writes to `cases` table |
| 19 | | `resolve.py:47-49` → HTMX response includes `HX-Redirect: /cases` header | |
| 20 | Browser redirects to `/cases` | `pages.py:21-42` → queries all cases, renders `cases.html` | reads `cases` table |

### 1.3 Cases — Approve / Reject / Notes

| Step | What you do | What happens |
|------|-----------|--------------|
| 1 | Open `/cases` | `pages.py:21-42` → loads all cases ordered by `created_at DESC` |
| 2 | Click on a row | JS toggles `.hidden` class on the detail row below |
| 3 | Click **Approve** or **Reject** | HTMX POSTs to `/resolve` with `case_id`, `match_id`, `decision` |
| 4 | | Same resolve flow as 1.2 step 18–20 above |
| 5 | Type notes and click **Save Notes** | JS `fetch(PATCH /api/cases/{id})` with JSON `{"notes": "..."}` |
| 6 | | `cases.py:72-79` → `case.notes = body.notes`, `db.commit()` |

### 1.4 Dashboard — Stats

| Step | What you do | What happens |
|------|-----------|--------------|
| 1 | Open `/dashboard` | `pages.py:50-83` → queries `cases` table for counts (total, open, blocked, cleared, match_rate) + 10 most recent cases |

### 1.5 Batch — Generate Random Test Data

| Step | What you do | What happens |
|------|-----------|--------------|
| 1 | Set count (default 5), choose Standard or AI, click **Generate & Screen** | HTMX POSTs to `/batch/generate` with `count` and `use_ai` |
| 2 | | `batch.py:39-43` → SQL `SELECT DISTINCT name FROM sanction_names ORDER BY RANDOM() LIMIT n` |
| 3 | | `batch.py:47-83` → For each name, calls `fuzzy_match()`, appends result row |
| 4 | | `batch.py:66-77` → If `use_ai=True`, calls `analyze_match()` via Ollama on best match |
| 5 | | Returns `_batch_results.html` with table of results |
| 6 | In browser | Table shows Row #, Name, Status (Clear/Fuzzy/Error), Match count, optional AI column |

### 1.6 Query — Natural Language to SQL

| Step | What you do | What happens |
|------|-----------|--------------|
| 1 | Open `/query` | `query.py` route renders `query.html` |
| 2 | Type a question, click **Ask** | HTMX POSTs to `/api/query` with `{"question": "..."}` |
| 3 | | `query.py:44-45` → `nl_to_sql()` calls Ollama `generate()` with `NL_QUERY_SYSTEM` prompt |
| 4 | | `query.py:56` → `_is_safe_select(sql)` checks it starts with SELECT + no forbidden keywords |
| 5 | | `query.py:66-74` → `db.execute(text(sql))` → `fetchall()` → returns `columns` + `rows` |
| 6 | Browser renders results table | Or error message if Ollama is down / SQL failed |

---

## 2. Component Testing Flow

Test individual pieces without the full stack.

### 2.1 Test a Python function directly

```powershell
cd C:\Users\memeo\Downloads\CursorProjects\SanctionScreeningPrototype
$env:PYTHONPATH = "C:\Users\memeo\Downloads\CursorProjects\SanctionScreeningPrototype"
python
```

```python
# Test fuzzy matching
from app.database import SessionLocal
from app.matchers.fuzzy import fuzzy_match
from app.matchers.scorer import combined_score

db = SessionLocal()

# Direct score calculation
score = combined_score("SANAVBARI", "SANAVBARI NIKITENKO")
print(f"Score: {score}")           # 85.0

# Full fuzzy match
matches = fuzzy_match(db, "Vladimir Putin", threshold=70.0)
print(f"Matches: {len(matches)}")
for m in matches[:3]:
    print(f"  {m['caption']} — {m['score']}%")

db.close()
```

### 2.2 Test inference engine (fuzzy)
```python
from app.database import SessionLocal
from app.matchers.fuzzy import fuzzy_match

db = SessionLocal()

cases = [
    ("SANAVBARI", None),
    ("Vladimir Putin", "Person"),
    ("North Korea Trading", "Company"),
    ("TotallyFakeName123", None),     # should return clear
]

for name, st in cases:
    matches = fuzzy_match(db, name, schema_filter=st, threshold=70.0)
    if matches:
        print(f"  HIT  {name}: {len(matches)} match(es), top={matches[0]['score']}%")
    else:
        print(f"  CLR  {name}: no match")

db.close()
```

### 2.3 Test exact matching
```python
from app.database import SessionLocal
from app.matchers.exact import match_by_source

db = SessionLocal()
results = match_by_source(db, "us-bis-entity", "some-id")
print(f"Exact matches: {len(results)}")
db.close()
```

### 2.4 Test an endpoint with curl / PowerShell

```powershell
# Screen a name (form-encoded — same as HTMX)
$body = @{ name = "SANAVBARI" }
$r = Invoke-RestMethod -Uri http://localhost:8000/screen -Method Post -Body $body
$r | ConvertTo-Json

# Screen a name (JSON — API-style)
$r = Invoke-RestMethod -Uri http://localhost:8000/screen -Method Post `
  -ContentType "application/json" -Body '{"name":"Morten Austestad"}'
$r | ConvertTo-Json

# Resolve a case (get case_id from screen response)
$r = Invoke-RestMethod -Uri http://localhost:8000/resolve -Method Post -Body @{
  case_id = "your-case-id-here"
  match_id = "some-match-id"
  decision = "approve"
}
$r | ConvertTo-Json

# Get stats
Invoke-RestMethod -Uri http://localhost:8000/api/stats | ConvertTo-Json

# Batch generate
$r = Invoke-WebRequest -Uri http://localhost:8000/batch/generate `
  -Method Post -Body @{ count = 3; use_ai = $false } -UseBasicParsing
Write-Host $r.Content

# NL query
$r = Invoke-RestMethod -Uri http://localhost:8000/api/query -Method Post `
  -ContentType "application/json" -Body '{"question":"How many Person entities are there?"}'
$r | ConvertTo-Json
```

### 2.5 Test data ingestion

```powershell
# Dry run — ingest first 10000 lines and check stats
cd C:\Users\memeo\Downloads\CursorProjects\SanctionScreeningPrototype
$env:PYTHONPATH = "."
python -c "
from app.ingest import ingest
# Modify BATCH_SIZE for faster testing
import app.config
app.config.BATCH_SIZE = 1000
ingest()
"
```

### 2.6 Test the server starts correctly

```powershell
cd C:\Users\memeo\Downloads\CursorProjects\SanctionScreeningPrototype
$env:PYTHONPATH = "."
python -c "
from app.main import app
from app.ingest import ingest
from app.matchers.fuzzy import fuzzy_match
from app.matchers.scorer import combined_score
from app.ai.ollama import OllamaClient
print('All modules import OK')
"
```

### 2.7 Verify all routes register

```powershell
python -c "
from app.main import app
for r in app.routes:
    if hasattr(r, 'methods') and hasattr(r, 'path'):
        print(f'{list(r.methods)[0]:>6} {r.path}')
"
```

Expected output:
```
   GET /
   GET /api/cases
   GET /api/cases/{case_id}
  PATCH /api/cases/{case_id}
   GET /api/stats
   GET /batch
  POST /batch/generate
  POST /batch/upload
   GET /cases
   GET /cases/{case_id}
   GET /dashboard
   GET /query
  POST /analyze
  POST /api/query
  POST /resolve
  POST /screen
```

---

## 3. Quick Reference — Key Entry Points

| What | Command | File executed |
|------|---------|--------------|
| Start server | `python -m uvicorn app.main:app --reload` | `app/main.py` |
| Ingest data | `python -m app.ingest` | `app/ingest.py` |
| Run script | `.\run.ps1` | `run.ps1` → checks deps → ingest → start |
| Test fuzzy match | Interactive Python | `app/matchers/fuzzy.py` |
| Test exact match | Interactive Python | `app/matchers/exact.py` |
| Test endpoint | curl / PowerShell | `app/routes/*.py` |
| Pull AI model | `ollama pull llama3` | Ollama CLI |
| Start Ollama | `ollama serve` | Ollama binary |
