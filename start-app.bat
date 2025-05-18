@echo off
echo Starting KnobGallery++ Application...
echo.

echo Starting Backend Server...
start cmd /k "cd backend && uvicorn main:app --reload --port 8000"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo Starting Frontend Application...
start cmd /k "cd frontend && npm run dev"

echo.
echo KnobGallery++ is starting up!
echo - Backend: http://localhost:8000
echo - Frontend: The Electron app should open automatically
echo.
echo Press any key to close this window.
pause > nul
