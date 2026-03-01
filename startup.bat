@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo Starting backend in a new terminal...
if exist "%ROOT%venv\Scripts\activate.bat" (
  start "Backend" cmd /k "cd /d "%ROOT%" ^&^& call venv\Scripts\activate.bat ^&^& uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
) else (
  start "Backend" cmd /k "cd /d "%ROOT%" ^&^& uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
)

echo Starting frontend in a new terminal...
start "Frontend" cmd /k "cd /d "%ROOT%frontend" ^&^& npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the two spawned terminal windows to stop services.
endlocal
