@echo off
REM Inicia el Balance (servidor + enlace público). Deje esta ventana abierta o minimizada.
REM Para solo uso local sin internet:  iniciar_balance.bat -SoloLocal
title Servicio Balance Grupo de Empresas
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar_balance.ps1" %*
pause
