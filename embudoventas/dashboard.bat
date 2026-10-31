@echo off
REM ============================================================
REM  Embudo de Ventas - Latinbien (ejecucion local)
REM  1) Sync incremental SOLO LECTURA a Odoo, en segundo plano
REM     (resultado en cache_live.json + sync_last.log)
REM  2) Sirve el dashboard en http://127.0.0.1:8080
REM  Ejecutar: dashboard.bat
REM ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro "python" en el PATH.
    pause
    exit /b 1
)

echo [%date% %time%] Sync incremental (solo lectura) en segundo plano...
start "EmbudoSync" /b cmd /c "python sync_live.py > sync_last.log 2>&1"

echo [%date% %time%] Abriendo servidor en http://127.0.0.1:8080 ...
python serve.py
if errorlevel 1 (
    echo.
    echo [ERROR] El servidor no pudo iniciar (revise el mensaje anterior).
    pause
)

endlocal
