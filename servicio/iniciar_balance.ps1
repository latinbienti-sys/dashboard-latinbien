# Inicializador del servicio Balance Grupo de Empresas.
#  - Levanta el servidor (waitress, solo en 127.0.0.1:5000) en modo público.
#  - Levanta Cloudflare Tunnel (HTTPS) y guarda el enlace en ENLACE_ACTUAL.txt.
#  - Vigila ambos procesos y los reinicia si se caen.
# Odoo no se toca: la app solo consulta en modo lectura.
param(
    [switch]$SinNavegador,   # no abrir el navegador al iniciar (arranque automático)
    [switch]$SoloLocal       # sin túnel: solo http://127.0.0.1:5000
)

$ErrorActionPreference = "Stop"
$Proyecto = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Proyecto ".venv\Scripts\python.exe"
$Cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$Logs = Join-Path $Proyecto "logs"
$ArchivoEnlace = Join-Path $Proyecto "ENLACE_ACTUAL.txt"
$Puerto = 5000

New-Item -ItemType Directory -Force $Logs | Out-Null
Set-Location $Proyecto

function Log($msg) {
    $linea = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Write-Host $linea
    Add-Content -Path (Join-Path $Logs "servicio.log") -Value $linea -Encoding utf8
}

# Evitar dos inicializadores a la vez
$mutex = New-Object System.Threading.Mutex($false, "Global\BalanceGrupoEmpresasServicio")
if (-not $mutex.WaitOne(0)) {
    Write-Host "El servicio ya está en ejecución."
    if (Test-Path $ArchivoEnlace) { Get-Content $ArchivoEnlace }
    exit 0
}

function Servidor-Activo {
    [bool](Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue)
}

function Iniciar-Servidor {
    if (-not (Test-Path $Python)) { throw "No existe $Python. Cree el entorno: python -m venv .venv" }
    $env:BALANCE_PUBLICO = if ($SoloLocal) { "0" } else { "1" }
    Start-Process -FilePath $Python -ArgumentList "app_balance.py" -WorkingDirectory $Proyecto `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $Logs "servidor.log") `
        -RedirectStandardError (Join-Path $Logs "servidor_error.log") | Out-Null
    for ($i = 0; $i -lt 30 -and -not (Servidor-Activo); $i++) { Start-Sleep -Milliseconds 500 }
    if (Servidor-Activo) { Log "Servidor iniciado en http://127.0.0.1:$Puerto" }
    else { Log "ERROR: el servidor no arrancó. Revise logs\servidor_error.log" }
}

$script:Tunel = $null
function Iniciar-Tunel {
    $logTunel = Join-Path $Logs "tunel.log"
    Remove-Item $logTunel -ErrorAction SilentlyContinue
    $script:Tunel = Start-Process -FilePath $Cloudflared -PassThru -WindowStyle Hidden `
        -ArgumentList "tunnel --no-autoupdate --logfile `"$logTunel`" --url http://127.0.0.1:$Puerto"
    $url = $null
    for ($i = 0; $i -lt 60 -and -not $url; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $logTunel) {
            $m = Select-String -Path $logTunel -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($m) { $url = $m.Matches[0].Value }
        }
    }
    if ($url) {
        Set-Content -Path $ArchivoEnlace -Encoding utf8 -Value @(
            "Enlace público del Balance (cambia cada vez que se reinicia el servicio):",
            $url,
            "Generado: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        )
        Log "Túnel activo: $url"
    } else {
        Log "ERROR: el túnel no entregó enlace. Revise logs\tunel.log"
    }
    return $url
}

# --- Arranque ---
Log "=== Iniciando servicio Balance ==="
if (Servidor-Activo) { Log "El puerto $Puerto ya estaba en uso: se reutiliza el servidor existente" }
else { Iniciar-Servidor }

$urlPublica = $null
if (-not $SoloLocal) {
    if (-not (Test-Path $Cloudflared)) { Log "ERROR: no está instalado cloudflared" }
    else { $urlPublica = Iniciar-Tunel }
} else {
    Remove-Item $ArchivoEnlace -ErrorAction SilentlyContinue
}

if (-not $SinNavegador) {
    if ($urlPublica) { Start-Process $urlPublica } else { Start-Process "http://127.0.0.1:$Puerto" }
}

Write-Host ""
Write-Host "Servicio en marcha. Local: http://127.0.0.1:$Puerto"
if ($urlPublica) { Write-Host "Público: $urlPublica" }
Write-Host "Para detenerlo: servicio\detener_balance.bat"

# --- Vigilancia: reinicia lo que se caiga ---
while ($true) {
    Start-Sleep -Seconds 20
    if (-not (Servidor-Activo)) {
        Log "El servidor se detuvo: reiniciando"
        Iniciar-Servidor
    }
    if (-not $SoloLocal -and $script:Tunel -and $script:Tunel.HasExited) {
        Log "El túnel se detuvo: reiniciando (el enlace cambiará)"
        Iniciar-Tunel | Out-Null
    }
}
