$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
$env:PYTHONPATH = $scriptDir
Write-Host "Starting DCI AI Business Assistant..." -ForegroundColor Cyan
& "$scriptDir\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
