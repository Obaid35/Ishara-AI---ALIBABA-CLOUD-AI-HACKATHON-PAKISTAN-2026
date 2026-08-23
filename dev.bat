@echo off
chcp 65001 >nul
title Ishara AI - development

cd /d "%~dp0"

echo.
echo  Ishara AI - development mode [hot reload]
echo.

if not exist ".env" ( echo  [X] .env missing. Run setup.bat first. & pause & exit /b 1 )

call :freeport 8000
call :freeport 3000

echo  [..] API   http://localhost:8000  [auto-reload]
start "Ishara AI API (dev)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo  [..] Web   http://localhost:3000  [hot reload]
start "Ishara AI Web (dev)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo  Both servers run in their own windows with live logs.
echo  Close those windows, or run stop.bat, to stop.
echo.
ping -n 7 127.0.0.1 >nul
start "" http://localhost:3000
exit /b 0

:freeport
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:"LISTENING" ^| findstr /r /c:":%~1 "') do taskkill /f /pid %%p >nul 2>&1
exit /b 0
