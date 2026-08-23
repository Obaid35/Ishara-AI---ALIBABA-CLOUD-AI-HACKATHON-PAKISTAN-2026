@echo off
chcp 65001 >nul
title PSL Bridge - export snapshot

cd /d "%~dp0backend"

echo.
echo  Exporting the offline demo snapshot to data\*.json
echo.
echo  This is the read-only fallback the app boots from if PostgreSQL is
echo  unavailable. Re-export after ANY content change - a stale snapshot
echo  can restore a sign you removed.
echo.

python -c "from app.db import SessionLocal; from app.services import snapshot; db=SessionLocal(); print('  ', snapshot.export(db)); db.close()"
if errorlevel 1 ( echo  [X] Export failed - is PostgreSQL running? & pause & exit /b 1 )

echo.
echo  [ok] Snapshot exported.
echo.
pause
