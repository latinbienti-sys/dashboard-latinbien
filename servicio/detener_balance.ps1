# Detiene el servicio Balance: vigilante, servidor y túnel.
$Proyecto = Split-Path -Parent $PSScriptRoot

Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match "powershell|pwsh" -and $_.CommandLine -match "iniciar_balance\.ps1" -and $_.ProcessId -ne $PID } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "Vigilante detenido ($($_.ProcessId))" }

Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match "python" -and $_.CommandLine -match "app_balance\.py" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "Servidor detenido ($($_.ProcessId))" }

Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq "cloudflared.exe" -and $_.CommandLine -match "127\.0\.0\.1:5000" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "Túnel detenido ($($_.ProcessId))" }

Remove-Item (Join-Path $Proyecto "ENLACE_ACTUAL.txt") -ErrorAction SilentlyContinue
"Servicio Balance detenido."
