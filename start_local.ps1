$ErrorActionPreference = "Stop"

Write-Host "=== Spoustim NurseShift v lokalnim rezimu (bez nutnosti Dockeru) ===" -ForegroundColor Cyan

# 1. Backend venv & dependencies
if (-not (Test-Path ".\backend\.venv")) {
    Write-Host "Vytvarim Python virtualni prostredi v .\backend\.venv ..." -ForegroundColor Yellow
    py -m venv .\backend\.venv
}

Write-Host "Instaluji/kontroluji Python zavislosti ..." -ForegroundColor Yellow
& .\backend\.venv\Scripts\pip.exe install --disable-pip-version-check -q fastapi "uvicorn[standard]" pydantic pydantic-settings "PyJWT" httpx

# 2. Frontend dependencies
if (-not (Test-Path ".\frontend\node_modules\.bin\vite.cmd")) {
    Write-Host "Instaluji npm balicky pro frontend ..." -ForegroundColor Yellow
    Push-Location .\frontend
    npm install
    Pop-Location
}

# 3. Start Backend & Frontend in separate PowerShell windows
Write-Host "Spoustim FastAPI Backend na http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend'; .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "Spoustim React Vite Frontend na http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "Hotovo! Otevrete v prohlizeci: http://localhost:5173" -ForegroundColor Cyan

