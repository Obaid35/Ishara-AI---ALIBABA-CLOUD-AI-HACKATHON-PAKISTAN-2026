@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Ishara AI - Setup

cd /d "%~dp0"

echo.
echo  ==========================================================
echo   Ishara AI - setup
echo  ==========================================================
echo.

REM ============================================================ 1. toolchain
where python >nul 2>&1
if errorlevel 1 (
  echo  [X] Python was not found on PATH.
  echo      Install Python 3.11+ from https://www.python.org/downloads/
  echo      Be sure to tick "Add python.exe to PATH".
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

REM ============================================================ 2. locate psql
set "PSQL_DIR="
for %%d in (18 17 16 15 14 13) do (
  if exist "C:\Program Files\PostgreSQL\%%d\bin\psql.exe" (
    if not defined PSQL_DIR set "PSQL_DIR=C:\Program Files\PostgreSQL\%%d\bin"
  )
)
if defined PSQL_DIR (
  set "PATH=!PSQL_DIR!;%PATH%"
  echo  [ok] PostgreSQL tools at "!PSQL_DIR!"
) else (
  where psql >nul 2>&1
  if errorlevel 1 (
    echo  [X] PostgreSQL was not found.
    echo      Install it from https://www.postgresql.org/download/windows/
    echo      and remember the password you set for the "postgres" user.
    goto :fail
  )
  echo  [ok] PostgreSQL tools on PATH
)

REM ============================================================ 3. .env
echo.
if exist ".env" (
  echo  [ok] .env already exists - leaving it untouched
) else (
  echo  ----------------------------------------------------------
  echo   Creating .env
  echo  ----------------------------------------------------------
  echo.
  echo   Enter the password for your PostgreSQL "postgres" user.
  echo   This is the password you chose when installing PostgreSQL.
  echo.
  set "PGPW="
  set /p "PGPW=  PostgreSQL password: "
  if "!PGPW!"=="" (
    echo.
    echo  [X] A password is required.
    goto :fail
  )

  echo.
  echo   Choose a password for the admin account you will sign in with.
  echo   Press Enter to use: admin123
  echo.
  set "ADMINPW="
  set /p "ADMINPW=  Admin password: "
  if "!ADMINPW!"=="" set "ADMINPW=admin123"

  python backend\scripts\make_env.py --db-password "!PGPW!" --admin-password "!ADMINPW!"
  if errorlevel 1 ( echo. & echo  [X] Could not write .env - see the message above. & goto :fail )
)

REM ---- read the values back so the rest of the script can use them
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="POSTGRES_PASSWORD" set "PGPASSWORD=%%b"
  if /i "%%a"=="POSTGRES_USER" set "PGUSER=%%b"
)
if not defined PGUSER set "PGUSER=postgres"

REM ============================================================ 4. verify the password
echo.
echo  [..] Testing the PostgreSQL connection
psql -U !PGUSER! -h localhost -d postgres -c "SELECT 1" >nul 2>&1
if errorlevel 1 (
  echo  [X] Could not connect to PostgreSQL as "!PGUSER!".
  echo      Check that the service is running and that POSTGRES_PASSWORD
  echo      in .env is correct, then run setup.bat again.
  goto :fail
)
echo  [ok] Connected

REM ============================================================ 5. database
echo.
psql -U !PGUSER! -h localhost -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='ishara_ai'" 2>nul | findstr "1" >nul
if errorlevel 1 (
  echo  [..] Creating the ishara_ai database
  createdb -U !PGUSER! -h localhost ishara_ai
  if errorlevel 1 ( echo  [X] Could not create the database. & goto :fail )
  echo  [ok] Database created
) else (
  echo  [ok] Database already exists
)

REM ============================================================ 6. backend deps
echo.
echo  [..] Installing backend dependencies
pushd backend
python -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 ( popd & echo  [X] Backend dependency install failed. & goto :fail )
echo  [ok] Backend dependencies installed

REM ============================================================ 7. migrate
echo.
echo  [..] Applying migrations
python -m app.migrate
if errorlevel 1 ( popd & echo  [X] Migrations failed. & goto :fail )

REM ============================================================ 8. seed
echo.
echo  ----------------------------------------------------------
echo   Seed development content?
echo.
echo   This marks the 15 freeze-list signs Reliable and enables
echo   their messages using PLACEHOLDER assets, so the app is
echo   usable straight away. It is labelled DEV PLACEHOLDER and
echo   is NOT verified PSL - replace it before any real demo.
echo.
echo   Answer N for a clean install with all content disabled.
echo  ----------------------------------------------------------
echo.
choice /c YN /m "  Include development content"
if errorlevel 2 (
  python -m app.seed
) else (
  python -m app.seed --dev-content
  echo.
  echo  [..] Generating placeholder audio ^(tones, not speech^)
  python scripts\generate_audio.py --placeholder
)
if errorlevel 1 ( popd & echo  [X] Seeding failed. & goto :fail )
popd

REM ============================================================ 9. frontend
echo.
echo  [..] Installing frontend dependencies ^(takes a minute^)
pushd frontend
call npm install --no-audit --no-fund
if errorlevel 1 ( popd & echo  [X] Frontend dependency install failed. & goto :fail )
echo.
echo  [..] Building the frontend
call npm run build
if errorlevel 1 ( popd & echo  [X] Frontend build failed. & goto :fail )
popd

REM ============================================================ done
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="SEED_ADMIN_EMAIL" set "AEMAIL=%%b"
  if /i "%%a"=="SEED_ADMIN_PASSWORD" set "APASS=%%b"
)

echo.
echo  ==========================================================
echo   Setup complete.
echo.
echo   Start it with:  run.bat
echo.
echo   Staff sign in:  !AEMAIL!
echo                   !APASS!
echo.
echo   The patient does NOT need an account.
echo  ==========================================================
echo.
exit /b 0

:fail
echo.
echo  Setup did not complete.
echo.
pause
exit /b 1
