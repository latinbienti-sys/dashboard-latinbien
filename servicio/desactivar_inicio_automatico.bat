@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Remove-Item ([Environment]::GetFolderPath('Startup')+'\Balance Grupo de Empresas.lnk') -ErrorAction SilentlyContinue; 'Inicio automatico DESACTIVADO.'"
pause
