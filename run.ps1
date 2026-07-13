param(
    [int]$Port = 8000,
    [string]$Host = "127.0.0.1",
    [switch]$Reload = $true
)

Write-Host "=== Sanction Screening Prototype ===" -ForegroundColor Cyan

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERR] Python not found. Install Python 3.7+ and try again." -ForegroundColor Red
    exit 1
}

# Check Python is 3.7+
$ver = [Version](python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if ($ver -lt [Version]"3.7") {
    Write-Host "[ERR] Python 3.7+ required, found $ver" -ForegroundColor Red
    exit 1
}

# Check pip deps
Write-Host "[...] Checking dependencies..." -ForegroundColor Yellow
try {
    $missing = python -c "import fastapi, uvicorn, sqlalchemy, jinja2, thefuzz, jellyfish, httpx, pydantic" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Missing deps"
    }
    Write-Host "[OK] All dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "[...] Installing dependencies..." -ForegroundColor Yellow
    python -m pip install -e . 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERR] pip install failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
}

# Check data file
$dataFile = "$env:USERPROFILE\Downloads\entities.ftm.json"
if (-not (Test-Path -LiteralPath $dataFile)) {
    Write-Host "[WARN] $dataFile not found. Place entities.ftm.json in your Downloads folder." -ForegroundColor Yellow
    Write-Host "[WARN] Screening will return no results without data." -ForegroundColor Yellow
}

# Check if DB exists, if not run ingest
$dbPath = Join-Path $PSScriptRoot "data" "sanctions.db"
if (-not (Test-Path -LiteralPath $dbPath)) {
    Write-Host "[...] Database not found. Running ingest..." -ForegroundColor Yellow
    try {
        python -m app.ingest 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Ingest failed"
        }
        Write-Host "[OK] Database created" -ForegroundColor Green
    } catch {
        Write-Host "[ERR] $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[OK] Database found at $dbPath" -ForegroundColor Green
}

# Start uvicorn
$reloadArg = if ($Reload) { "--reload" } else { "" }
Write-Host "Starting server at http://${Host}:${Port}" -ForegroundColor Cyan
python -m uvicorn app.main:app --host $Host --port $Port $reloadArg

