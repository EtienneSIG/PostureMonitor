@echo off
REM start.bat — Launch PostureMonitor on Windows
setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend
set FRONTEND_DIR=%SCRIPT_DIR%frontend
set STATIC_DIR=%BACKEND_DIR%\static

REM ── 1. Build frontend if needed ──────────────────────────────────────────
if not exist "%STATIC_DIR%\index.html" (
    echo Building SvelteKit frontend...
    cd /d "%FRONTEND_DIR%"
    call yarn install --frozen-lockfile
    call yarn build
    cd /d "%SCRIPT_DIR%"
)

REM ── 2. Install Python deps ───────────────────────────────────────────────
cd /d "%BACKEND_DIR%"
python -c "import fastapi" 2>nul || (
    echo Installing Python dependencies...
    pip install -r requirements.txt
)

REM ── 3. Launch ────────────────────────────────────────────────────────────
echo Starting PostureMonitor at http://127.0.0.1:8000
python main.py
