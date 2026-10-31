@echo off
REM Crea un acceso directo en la carpeta Inicio de Windows: el Balance arranca
REM solo (en segundo plano, sin ventana) cada vez que inicia sesión en este PC.
REM Para desactivarlo: desactivar_inicio_automatico.bat
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Startup')+'\Balance Grupo de Empresas.lnk');" ^
  "$s.TargetPath='powershell.exe';" ^
  "$s.Arguments='-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File \"%~dp0iniciar_balance.ps1\" -SinNavegador';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.WindowStyle=7; $s.Save(); 'Inicio automatico ACTIVADO.'"
pause
