# Prerequisites

## Required Software

| Dependency | Version | Purpose |
|---|---|---|
| **Python** | 3.7+ | Runtime |
| **Ollama** | v0.31.2+ | AI analysis & NL query |
| **Llama 3** (via Ollama) | latest | AI model pulled by `ollama pull llama3` |

## Python Dependencies (auto-installed by `run.ps1`)

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server |
| `sqlalchemy` | ORM + SQLite |
| `jinja2` | HTML templating |
| `python-multipart` | Form data parsing |
| `httpx` | Async HTTP for Ollama |
| `pydantic` | Data validation |
| `thefuzz` | Token-based fuzzy matching |
| `jellyfish` | Phonetic matching (soundex, metaphone) |
| `python-Levenshtein` | Speed up thefuzz |

## Source Data

- File: `entities.ftm.json` (FollowTheMoney format, ~2.7 GB)
- Must be placed at `C:\Users\memeo\Downloads\entities.ftm.json` (or update `app/config.py` `DATA_PATH`)
- Contains ~1.32M sanctioned entities from open sanction lists
