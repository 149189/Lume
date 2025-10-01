@echo off
echo ========================================
echo    LUME AI Assistant - Server Starter
echo ========================================
echo.

echo Starting Django Backend...
start cmd /k "cd /d %~dp0lume_django && venv\Scripts\activate && echo Django Backend Starting... && python manage.py runserver"

timeout /t 3 /nobreak > NUL

echo Starting Next.js Frontend...
start cmd /k "cd /d %~dp0lume_frontend && echo Next.js Frontend Starting... && npm run dev"

timeout /t 2 /nobreak > NUL

echo.
echo ========================================
echo Both servers are starting!
echo.
echo Django Backend: http://localhost:8000
echo Next.js Frontend: http://localhost:3000
echo.
echo Open http://localhost:3000 in your browser
echo ========================================
echo.
pause
