@echo off
cd /d "%~dp0"
echo Starting DCI AI Business Assistant (Backend + Frontend)...
start "DCI Backend (FastAPI)" cmd /c "run_backend.bat"
timeout /t 5 /nobreak >nul
start "DCI Frontend (React)" cmd /c "run_frontend.bat"
echo Both servers started!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
