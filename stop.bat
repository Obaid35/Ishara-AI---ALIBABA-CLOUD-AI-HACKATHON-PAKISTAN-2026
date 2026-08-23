@echo off
chcp 65001 >nul
title Ishara AI - stop

echo.
echo  Stopping Ishara AI...

call :freeport 8000 API
call :freeport 3000 Web

echo.
echo  Done. PostgreSQL was left running.
echo.
ping -n 4 127.0.0.1 >nul
exit /b 0

:freeport
set "found="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:"LISTENING" ^| findstr /r /c:":%~1 "') do (
  taskkill /f /pid %%p >nul 2>&1
  set "found=1"
)
if defined found ( echo   [ok] %~2 on port %~1 stopped ) else ( echo   [--] %~2 on port %~1 was not running )
exit /b 0
