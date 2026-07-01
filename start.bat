@echo off
echo ============================================
echo   Hit The Point - Start Dev Environment
echo ============================================
echo.

:: Start FastAPI backend in a new window (using venv python -m uvicorn)
echo [1/2] Starting FastAPI backend on http://127.0.0.1:8000 ...
start "FastAPI Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn server:app --reload --port 8000"

:: Give the backend a moment to start
timeout /t 3 /nobreak >nul

:: Start Vite frontend in a new window
echo [2/2] Starting Vite frontend on http://localhost:5173 ...
start "Vite Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait for frontend to be ready, then open browser
timeout /t 5 /nobreak >nul
echo Opening frontend in browser...
start http://localhost:5173

echo.
echo ============================================
echo   Both servers are running!
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:5173
echo ============================================
echo.
echo Close the terminal windows to stop the servers.
