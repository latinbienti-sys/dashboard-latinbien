@echo off
REM Cronjob para actualizar dashboard LATINBIEN cada 3 horas
REM Ejecutar: schtasks /create /tn "LATINBIEN_Dashboard" /tr "C:\Users\yarleyc\Documents\New OpenCode Project\update_dashboard.bat" /sc hourly /st 00:00

cd /d "C:\Users\yarleyc\Documents\New OpenCode Project"

echo [%date% %time%] Regenerando dashboard...
python server.py --generate

echo [%date% %time%] Haciendo push a GitHub...
git add index.html
git commit -m "Dashboard actualizado %date%"
git push origin main

echo [%date% %time%] Dashboard actualizado exitosamente
