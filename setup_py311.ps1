$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $root '.venv311'

Write-Host 'Checking Python 3.11 availability...' -ForegroundColor Cyan
$py311 = & py -3.11 -c "import sys; print(sys.executable)" 2>$null
if (-not $py311) {
    Write-Host 'Python 3.11 is not installed on this machine.' -ForegroundColor Red
    Write-Host 'Install Python 3.11, then re-run this script.' -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Python 3.11 at: $py311" -ForegroundColor Green

if (-not (Test-Path $venvPath)) {
    Write-Host 'Creating .venv311...' -ForegroundColor Cyan
    & py -3.11 -m venv $venvPath
}

$pythonExe = Join-Path $venvPath 'Scripts\python.exe'

Write-Host 'Installing Python dependencies...' -ForegroundColor Cyan
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $root 'requirements.txt')

Write-Host 'Installing frontend dependencies...' -ForegroundColor Cyan
Push-Location (Join-Path $root 'frontend')
npm install
Pop-Location

Write-Host ''
Write-Host 'Stable Python 3.11 environment is ready.' -ForegroundColor Green
Write-Host 'Next steps:' -ForegroundColor Cyan
Write-Host "1. $venvPath\Scripts\Activate.ps1"
Write-Host '2. python launch.py'
