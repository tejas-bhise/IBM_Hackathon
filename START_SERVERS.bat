@echo off
echo ========================================
echo   Starting Backend and Frontend Servers
echo ========================================
echo.

REM Start Backend Server in new window
echo [1/2] Starting Backend Server...
start "Backend Server" cmd /k "cd /d c:\Users\hp\ibm\bobbackend && echo Starting FastAPI Backend... && uvicorn main:app --reload --port 8000"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend Server in new window
echo [2/2] Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d C:\Users\hp\frontend && echo Starting Next.js Frontend... && npm run dev"

echo.
echo ========================================
echo   Servers Starting!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Two new windows will open:
echo   1. Backend Server (FastAPI)
echo   2. Frontend Server (Next.js)
echo.
echo Wait for both to finish starting, then open:
echo   http://localhost:3000
echo.
echo Press any key to exit this window...
pause >nul

@REM Made with Bob
