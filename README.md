# Sanction Screening Prototype

Two-tier sanction screening with fuzzy matching and local AI analysis via Ollama.

## Features

- **Exact ID matching** — auto-block on referent ID match (OFAC, UN, EU lists)
- **Fuzzy name matching** — weighted token-set + partial-ratio + soundex + metaphone
- **Human-in-the-loop** — approve/reject fuzzy matches via case management
- **AI match analysis** — Ollama-powered risk assessment on candidate matches
- **Batch screening** — generate random test entries, screen them in bulk
- **Natural-language query** — type a question in English, get SQL results
- **Dashboard** — case stats and match rates
- **HTMX + Jinja2 frontend** — server-driven UI, no JS build step

## Prerequisites

See [docs/PREREQUISITES.md](docs/PREREQUISITES.md) for full dependency breakdown.

| Requirement | Notes |
|---|---|
| Python 3.7+ | Tested with 3.7.4 |
| Ollama v0.31.2+ | Required only for AI analysis and NL query |
| `entities.ftm.json` | ~2.7 GB FollowTheMoney dataset in Downloads |

## Setup & Run

Full sequence in [docs/SEQUENCE_FLOW.md](docs/SEQUENCE_FLOW.md).

**Quick start:**
```powershell
# 1. Start Ollama (leave this terminal open)
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve

# 2. Pull AI model (one-time, in a second terminal)
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull llama3

# 3. Start the app
cd C:\Users\memeo\Downloads\CursorProjects\SanctionScreeningPrototype
.\run.ps1
```

Or manually:
```powershell
pip install -e .
python -m app.ingest          # loads sanctions DB from entities.ftm.json
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Documentation

| Doc | Purpose |
|---|---|
| [PREREQUISITES.md](docs/PREREQUISITES.md) | Software + Python dependency breakdown |
| [SEQUENCE_FLOW.md](docs/SEQUENCE_FLOW.md) | Step-by-step run guide + UI flow map |
| [CODE_EXECUTION_FLOW.md](docs/CODE_EXECUTION_FLOW.md) | Code-level trace of every endpoint & data pipeline |

## Pages

| URL | Purpose |
|---|---|
| `/` | Home — screening form + nav cards |
| `/cases` | Case management — approve/reject, notes |
| `/dashboard` | Stats overview |
| `/batch` | Batch screening — generate + screen test entries |
| `/query` | Natural-language query against sanctions DB |

## Project Structure

```
├── run.ps1                # Helper: checks deps, runs ingest, starts server
├── pyproject.toml         # Package metadata + dependencies
├── README.md
├── docs/
│   ├── PREREQUISITES.md   # Dependency breakdown
│   ├── SEQUENCE_FLOW.md   # Run sequence + UI flow
│   └── CODE_EXECUTION_FLOW.md  # Code-level execution trace
├── data/
│   └── sanctions.db       # SQLite database (created by ingest)
└── app/                   # All application code
    ├── main.py            # FastAPI app factory + startup
    ├── config.py          # Paths, Ollama settings
    ├── database.py        # SQLAlchemy engine (SQLite)
    ├── ingest.py          # Data ingestion script (python -m app.ingest)
    ├── schemas.py         # Pydantic response models
    ├── routes/
    │   ├── pages.py       # HTML page handlers (/, /cases, /dashboard)
    │   ├── screen.py      # POST /screen (exact → fuzzy → clear)
    │   ├── resolve.py     # POST /resolve (approve / reject)
    │   ├── cases.py       # GET/PATCH /api/cases (JSON API + notes)
    │   ├── stats.py       # GET /api/stats (dashboard data)
    │   ├── analyze.py     # POST /analyze (Ollama match analysis)
    │   ├── batch.py       # GET /batch + POST /batch/generate
    │   └── query.py       # GET /query + POST /api/query (NL→SQL)
    ├── ai/
    │   ├── ollama.py      # Async Ollama HTTP client
    │   ├── prompts.py     # System prompts for AI analysis & SQL
    │   ├── analyzer.py    # Match analysis via Ollama
    │   └── query.py       # NL-to-SQL engine
    ├── matchers/
    │   ├── exact.py       # Exact ID matching (referents)
    │   ├── fuzzy.py       # Fuzzy name matching
    │   └── scorer.py      # Weighted score calculation
    ├── models/
    │   └── case.py        # Case ORM model
    ├── templates/         # Jinja2 HTML templates
    └── static/
        └── style.css
```

## License

MIT

_For learning purposes — not for production sanction screening._
