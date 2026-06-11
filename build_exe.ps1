<#
    build_exe.ps1 - Build the Posture Monitor Pro desktop executable.

    Steps:
      1. Build the Vue frontend (npm install + npm run build).
      2. Ensure PyInstaller is installed.
      3. Bundle everything into dist\PostureMonitorPro\PostureMonitorPro.exe

    Usage (from the project root):
        ./build_exe.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Posture Monitor Pro - Desktop build" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# 1. Build the frontend ------------------------------------------------------
Write-Host "`n[1/3] Building frontend..." -ForegroundColor Yellow
Push-Location (Join-Path $root "frontend")
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}
npm run build
Pop-Location

if (-not (Test-Path (Join-Path $root "frontend\dist\index.html"))) {
    throw "Frontend build failed: frontend/dist/index.html not found."
}

# 2. Ensure PyInstaller ------------------------------------------------------
Write-Host "`n[2/3] Checking PyInstaller..." -ForegroundColor Yellow
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    python -m pip install pyinstaller
}

# 3. Bundle the executable ---------------------------------------------------
Write-Host "`n[3/3] Packaging executable with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller PostureMonitorPro.spec --noconfirm

$exePath = Join-Path $root "dist\PostureMonitorPro\PostureMonitorPro.exe"
if (Test-Path $exePath) {
    Write-Host "`nBuild complete!" -ForegroundColor Green
    Write-Host "Executable: $exePath" -ForegroundColor Green
    Write-Host "Share the entire 'dist\PostureMonitorPro' folder with users." -ForegroundColor Green
} else {
    throw "Build failed: executable not found at $exePath"
}
