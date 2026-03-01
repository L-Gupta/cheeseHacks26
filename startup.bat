@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "BACKEND_CMD=cd /d ""%ROOT%\backend"" ^&^& if exist ""%ROOT%\venv\Scripts\activate.bat"" (call ""%ROOT%\venv\Scripts\activate.bat"") ^&^& uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
set "FRONTEND_CMD=cd /d ""%ROOT%\frontend"" ^&^& npm run dev"

echo Starting backend in a new terminal...
start "Backend" cmd /k "%BACKEND_CMD%"

echo Starting frontend in a new terminal...
start "Frontend" cmd /k "%FRONTEND_CMD%"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the two spawned terminal windows to stop services.
endlocal
