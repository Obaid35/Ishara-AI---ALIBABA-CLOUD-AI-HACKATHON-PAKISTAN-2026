@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title PSL Bridge

cd /d "%~dp0"

echo.
echo  ==========================================================
echo   PSL Bridge
echo   Communication assistance only - not diagnostic.
echo  ==========================================================
echo.
echo  Checking prerequisites...
echo.

REM ============================================================ 1. toolchain
where python >nul 2>&1
if errorlevel 1 (
  echo  [X] Python was not found on PATH.
  echo      Install Python 3.11+ from https://www.python.org/downloads/
  echo      Be sure to tick "Add python.exe to PATH" during installation.
  goto :fail
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo  [ok] Python %%v

where npm >nul 2>&1
if errorlevel 1 (
  echo  [X] Node.js / npm was not found on PATH.
  echo      Install Node.js 20+ from https://nodejs.org/
  goto :fail
)
for /f %%v in ('npm -v 2^>^&1') do echo  [ok] npm %%v

REM ============================================================ 2. fresh checkout?
REM A clone has no .env, no node_modules and no build. Rather than send the
REM user away with an error, offer to do the whole setup here.
if not exist ".env" (
  echo.
  echo  ----------------------------------------------------------
  echo   This looks like a fresh checkout - .env is missing.
  echo.
  echo   Setup will: create .env, install backend and frontend
  echo   dependencies, create the database, apply migrations,
  echo   seed content and build the frontend.
  echo  ----------------------------------------------------------
  echo.
  choice /c YN /m "  Run setup now"
  if errorlevel 2 goto :needsetup
  echo.
  call "%~dp0setup.bat"
  if errorlevel 1 goto :setupfailed
  if not exist ".env" goto :needsetup
  echo.
  echo  Setup finished - continuing to start the app.
  echo.
) else (
  echo  [ok] .env present
)

REM ============================================================ 3. frontend deps
if not exist "frontend\node_modules" (
  echo  [warn] Frontend dependencies are not installed.
  choice /c YN /m "     Install them now"
  if errorlevel 2 (
    echo  [X] Cannot start without node_modules.
    goto :fail
  )
  pushd frontend
  call npm install --no-audit --no-fund
  if errorlevel 1 ( popd & echo  [X] npm install failed. & goto :fail )
  popd
)
echo  [ok] Frontend dependencies installed

REM ============================================================ 4. frontend build
if not exist "frontend\.next\BUILD_ID" (
  echo  [warn] No production build found - building now ^(takes a minute^)
  pushd frontend
  call npm run build
  if errorlevel 1 ( popd & echo  [X] Build failed. & goto :fail )
  popd
)
echo  [ok] Frontend build present

REM ============================================================ 5. backend deps
python -c "import fastapi, sqlalchemy, psycopg2, jwt, bcrypt, dotenv, email_validator" >nul 2>&1
if errorlevel 1 (
  echo  [warn] Backend Python packages are not installed.
  choice /c YN /m "     Install them now"
  if errorlevel 2 (
    echo  [X] Cannot start without the backend packages.
    goto :fail
  )
  pushd backend
  python -m pip install --disable-pip-version-check -q -r requirements.txt
  if errorlevel 1 ( popd & echo  [X] pip install failed. & goto :fail )
  popd
)
echo  [ok] Backend packages installed

REM ============================================================ 6. backend preflight
echo.
echo  Checking backend...
echo.
call :preflight
if "!PRE!"=="1" (
  echo.
  echo  Some of this can be fixed automatically by running setup.
  choice /c YN /m "  Run setup now"
  if errorlevel 2 goto :fail
  echo.
  call "%~dp0setup.bat"
  if errorlevel 1 goto :setupfailed
  echo.
  echo  Re-checking...
  echo.
  call :preflight
  if "!PRE!"=="1" (
    echo.
    echo  [X] Still not ready. Fix the items above and try again.
    goto :fail
  )
)
if "!PRE!"=="2" (
  echo.
  choice /c YN /m "  Start anyway with these warnings"
  if errorlevel 2 goto :abort
)

REM ============================================================ 7. free ports
echo.
call :freeport 8000 API
call :freeport 3000 Web

REM ============================================================ 8. start
echo.
echo  [..] Starting API on http://localhost:8000
start "PSL Bridge API" /min cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo  [..] Starting web on http://localhost:3000
start "PSL Bridge Web" /min cmd /c "cd /d "%~dp0frontend" && npm run start"

REM ============================================================ 9. wait for BOTH
echo.
echo  [..] Waiting for both services to answer
set /a tries=0
set "APIUP="
set "WEBUP="

:waitloop
set /a tries+=1
ping -n 3 127.0.0.1 >nul

if not defined APIUP (
  curl -s -f -o nul http://localhost:8000/api/health 2>nul && set "APIUP=1"
  if defined APIUP echo  [ok] API is answering
)
if not defined WEBUP (
  curl -s -f -o nul http://localhost:3000 2>nul && set "WEBUP=1"
  if defined WEBUP echo  [ok] Web is answering
)

if defined APIUP if defined WEBUP goto :ready

if !tries! geq 40 (
  echo.
  if not defined APIUP echo  [X] The API did not start. Check the "PSL Bridge API" window.
  if not defined WEBUP echo  [X] The web server did not start. Check the "PSL Bridge Web" window.
  goto :fail
)
goto :waitloop

REM ============================================================ 10. report
:ready
echo.
for /f "delims=" %%d in ('curl -s http://localhost:8000/api/health ^| python -c "import sys,json;d=json.load(sys.stdin);[print(x) for x in d['degradations']]" 2^>nul') do echo  [warn] %%d

echo.
echo  ==========================================================
echo   Communication screen   http://localhost:3000
echo   Staff sign in          http://localhost:3000/login
echo   Admin console          http://localhost:3000/admin
echo   API docs               http://localhost:8000/docs
echo.
echo   The patient does NOT need an account.
echo   Run stop.bat, or close the two minimised windows, to stop.
echo  ==========================================================
echo.
start "" http://localhost:3000
echo  This window can be closed.
ping -n 7 127.0.0.1 >nul
exit /b 0

REM ============================================================ helpers
:preflight
pushd backend
python scripts\preflight.py
set "PRE=%errorlevel%"
popd
exit /b 0

:freeport
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:"LISTENING" ^| findstr /r /c:":%~1 "') do (
  echo  [warn] Port %~1 [%~2] in use by PID %%p - stopping it
  taskkill /f /pid %%p >nul 2>&1
)
exit /b 0

:needsetup
echo.
echo  Nothing was started.
echo.
echo  To set the project up manually:
echo     1. copy .env.example to .env and fill in your PostgreSQL password
echo     2. run setup.bat
echo     3. run run.bat
echo.
pause
exit /b 1

:setupfailed
echo.
echo  [X] Setup did not complete. See the messages above.
echo.
pause
exit /b 1

:abort
echo.
echo  Cancelled.
echo.
pause
exit /b 1

:fail
echo.
pause
exit /b 1
