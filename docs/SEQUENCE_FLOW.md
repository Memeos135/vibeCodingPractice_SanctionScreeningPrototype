# Sequence Flow — Local Run Guide

## 1. Start Ollama
```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```
Leave this terminal window open. Ollama serves at `http://127.0.0.1:11434`.

## 2. Pull the AI model (one-time)
In a _second_ terminal:
```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull llama3
```

## 3. Start the App
```powershell
cd C:\Users\memeo\Downloads\CursorProjects\SanctionScreeningPrototype
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
App serves at `http://127.0.0.1:8000`.

Alternatively, use the helper script (auto-checks deps, runs ingest if needed):
```powershell
.\run.ps1
```

## 4. Open in Browser
Navigate to **http://127.0.0.1:8000**

## Sequence Diagram (Startup)
```
Terminal 1: ollama serve ─────────────────────────────────────────► 11434
Terminal 2: ollama pull llama3  (one-time, then done)
Terminal 2: uvicorn app.main:app ─────────────────────────────────► 8000
Browser:   http://localhost:8000 ──► Home page with screening form

POST /screen ──► ExactMatcher (ID match)
             └──► FuzzyMatcher (name match, threshold 70%)
                  └──► Case created (if match found)
                       └──► POST /resolve (approve / reject)

POST /analyze ──► Ollama → risk_level, confidence, recommendation
POST /api/query ──► Ollama → SQL → execute → results
```

## Application Flow (from Home Page)

```
Home (/)
├── Screen a Name ──► Exact match? ──► Blocked (red card)
│                    └── Fuzzy match? ──► Match cards with scores
│                                         ├── Confirm Match (creates case, status=blocked)
│                                         └── Not a Match (status=cleared)
│                    └── No match ──► Clear (green card)
│
├── Cases ──► Expand row for details
│             ├── Approve (block entity)
│             └── Reject (clear entity)
│
├── Dashboard ──► Stats: total, open, blocked, cleared, match rate
│
├── Batch ──► Generate N random names → screen all → table with scores
│             └── Optional: AI analysis column
│
└── Query ──► Type a question in English
              └──► Ollama generates SQL → executes → shows results table
```
