$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\frontend"
Write-Host "Starting DCI AI Business Assistant Frontend (Vite + React)..." -ForegroundColor Cyan
npm run dev
