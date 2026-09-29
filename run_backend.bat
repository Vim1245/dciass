@echo off
cd /d "%~dp0"
echo Starting DCI AI Business Assistant...
set PYTHONPATH=%~dp0
call .venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
pause
