@echo off
REM Publica/actualiza el visor de consulta del Consolidado en Vercel.
REM Primera vez:  publicar_vercel.bat --configurar-clave   (crea el proyecto y la clave del visor)
cd /d "%~dp0.."
".venv\Scripts\python.exe" publicar_vercel.py %*
pause
