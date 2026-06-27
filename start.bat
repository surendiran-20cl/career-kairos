@echo off
REM ============================================================
REM  AI Resume Matcher - Start Script
REM  Run this from the project root (resume-matcher\).
REM  It will:
REM    1. Start the PostgreSQL Docker container
REM    2. Open a new terminal window for the backend (FastAPI)
REM    3. Open a new terminal window for the frontend (Streamlit)
REM  Each server runs in its OWN venv - see README for why they
REM  are kept separate.
REM ============================================================

echo Starting PostgreSQL via Docker...
docker-compose up -d

echo Waiting a few seconds for the database to be ready...
timeout /t 5 /nobreak >nul

echo Launching backend (FastAPI) in a new window...
start "Resume Matcher - Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"

echo Waiting for backend to come up before launching frontend...
timeout /t 5 /nobreak >nul

echo Launching frontend (Streamlit) in a new window...
start "Resume Matcher - Frontend" cmd /k "cd frontend && venv\Scripts\activate && streamlit run app.py"

echo.
echo All set! Two new windows should have opened:
echo   - Backend  (FastAPI)   -> http://127.0.0.1:8000/docs
echo   - Frontend (Streamlit) -> http://localhost:8501
echo.
echo This window can stay open or be closed - it has no servers running in it.
pause