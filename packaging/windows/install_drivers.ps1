<#
.SYNOPSIS
    Provisiona drivers Apple Mobile Device USB (pnputil), o serviço Apple Mobile Device Service (AMDS)
    e o certificado Authenticode do iOS Forensics TUI Suite no Windows 10/11 x64.

.DESCRIPTION
    v1.2.0 — Correções:
      * AUTO-ELEVAÇÃO (UAC): se não estiver como Administrador, o script se relança com -Verb RunAs
        (antes: o atalho "Reparar Drivers" rodava sem privilégios e falhava silenciosamente).
      * LOG PERSISTENTE: toda execução grava transcript em %ProgramData%\iOS_Forensics\logs\
        (antes: o instalador usava -Quiet + runhidden e nenhuma falha ficava registrada).
      * Validação dos exit codes do pnputil (0 = OK, 259 = já atualizado, 3010 = requer reboot).
      * NÃO cria mais o serviço "usbmuxd" via sc.exe: o usbmuxd.exe win32 não implementa a API do
        Service Control Manager e falhava com erro 1053 (travando ~30s). O serviço legado criado
        pela v1.1.0 é removido automaticamente.
      * Opcional: -InstallAppleSupport instala o "Apple Devices" (Microsoft Store) ou iTunes via winget,
        que fornecem o driver usbaapl64.inf e o Apple Mobile Device Service.

.PARAMETER Quiet
    Suprime saída no console (o log continua sendo gravado).
.PARAMETER SkipCertificate
    Não importa o certificado Authenticode (.cer) em TrustedPublisher/Root.
.PARAMETER SkipDrivers
    Não instala drivers / não mexe em serviços (útil para instalar apenas o certificado).
.PARAMETER InstallAppleSupport
    Se nenhum driver Apple USB / AMDS for encontrado, instala "Apple Devices" (ou iTunes) via winget.
.PARAMETER NoElevate
    Não tenta auto-elevação (falha com código 5 se não for Administrador).
.PARAMETER LogPath
    Caminho do arquivo de log. Padrão: %ProgramData%\iOS_Forensics\logs\install_drivers_<timestamp>.log
#>
[CmdletBinding()]
param(
    [switch]$Quiet,
    [switch]$SkipCertificate,
    [switch]$SkipDrivers,
    [switch]$InstallAppleSupport,
    [switch]$NoElevate,
    [string]$LogPath = ""
)

$ErrorActionPreference = "Continue"

# ---------------------------------------------------------------------------
# 0. Auto-elevação UAC
# ---------------------------------------------------------------------------
function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    return ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    if ($NoElevate) {
        Write-Error "Este script requer privilégios de Administrador (pnputil, LocalMachine cert store, serviços)."
        exit 5
    }
    $forward = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
    foreach ($kv in $PSBoundParameters.GetEnumerator()) {
        if ($kv.Value -is [switch]) {
            if ($kv.Value.IsPresent) { $forward += "-$($kv.Key)" }
        } elseif ("$($kv.Value)" -ne "") {
            $forward += "-$($kv.Key)"; $forward += "`"$($kv.Value)`""
        }
    }
    Write-Host "[iOS Forensics Driver Setup] Solicitando elevação de Administrador (UAC)..." -ForegroundColor Yellow
    try {
        $proc = Start-Process -FilePath "powershell.exe" -ArgumentList $forward -Verb RunAs -Wait -PassThru
        exit $proc.ExitCode
    } catch {
        Write-Error "Elevação cancelada ou negada pelo usuário: $_"
        exit 1223
    }
}

# ---------------------------------------------------------------------------
# 1. Log persistente
# ---------------------------------------------------------------------------
if (-not $LogPath) {
    $LogDir = Join-Path $env:ProgramData "iOS_Forensics\logs"
    $LogPath = Join-Path $LogDir ("install_drivers_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null
try { Start-Transcript -Path $LogPath -Append | Out-Null } catch { }

$script:Warnings = 0
$script:RebootRequired = $false

function Write-Step([string]$msg) {
    $line = "[iOS Forensics Driver Setup] $msg"
    if ($Quiet) { Write-Verbose $line -Verbose:$false; Write-Output $line | Out-Null } else { Write-Host $line -ForegroundColor Cyan }
}
function Write-Warn([string]$msg) {
    $script:Warnings++
    Write-Warning $msg
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot   = Split-Path -Parent $ScriptDir
$BinDir    = Join-Path $AppRoot "bin"

Write-Step "Iniciado como Administrador. Log: $LogPath"
Write-Step "AppRoot: $AppRoot"

# ---------------------------------------------------------------------------
# 2. Certificado Authenticode
# ---------------------------------------------------------------------------
if (-not $SkipCertificate) {
    $CerFile = Get-ChildItem -Path $ScriptDir -Filter "*.cer" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($CerFile) {
        Write-Step "Importando certificado ($($CerFile.Name)) em LocalMachine\TrustedPublisher e LocalMachine\Root..."
        try {
            Import-Certificate -FilePath $CerFile.FullName -CertStoreLocation "Cert:\LocalMachine\TrustedPublisher" -ErrorAction Stop | Out-Null
            Import-Certificate -FilePath $CerFile.FullName -CertStoreLocation "Cert:\LocalMachine\Root" -ErrorAction Stop | Out-Null
            Write-Step "Certificado instalado com sucesso."
        } catch {
            Write-Warn "Falha ao importar o certificado: $_"
        }
    } else {
        Write-Step "Nenhum .cer encontrado em $ScriptDir (pulando)."
    }
}

if ($SkipDrivers) {
    Write-Step "SkipDrivers informado: etapa de drivers/serviços ignorada."
} else {
    # -----------------------------------------------------------------------
    # 3. Drivers USB Apple (pnputil)
    # -----------------------------------------------------------------------
    function Invoke-PnpUtilAdd([string]$InfPath) {
        Write-Step "pnputil /add-driver `"$InfPath`" /install"
        $out = & pnputil.exe /add-driver "$InfPath" /install 2>&1
        $code = $LASTEXITCODE
        $out | ForEach-Object { Write-Step "  $_" }
        switch ($code) {
            0     { Write-Step "  -> Driver instalado/registrado." }
            259   { Write-Step "  -> Driver já presente e atualizado (259)." }
            3010  { Write-Step "  -> Instalado; REINICIALIZAÇÃO NECESSÁRIA (3010)."; $script:RebootRequired = $true }
            default { Write-Warn "  -> pnputil retornou código $code para $InfPath" }
        }
    }

    $InfCandidates = @()
    $InfCandidates += Get-ChildItem -Path $ScriptDir -Recurse -Filter "*.inf" -ErrorAction SilentlyContinue
    $AppleDriverDirs = @(
        "$env:CommonProgramFiles\Apple\Mobile Device Support\Drivers",
        "${env:ProgramFiles(x86)}\Common Files\Apple\Mobile Device Support\Drivers"
    )
    foreach ($Dir in $AppleDriverDirs) {
        if (Test-Path $Dir) {
            $InfCandidates += Get-ChildItem -Path $Dir -Filter "*.inf" -ErrorAction SilentlyContinue
        }
    }
    # Apple Devices (Microsoft Store) instala o driver dentro de WindowsApps.
    $StoreDrivers = Get-ChildItem -Path "$env:ProgramFiles\WindowsApps" -Directory -Filter "AppleInc.AppleDevices*" -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ChildItem -Path $_.FullName -Recurse -Filter "usbaapl64.inf" -ErrorAction SilentlyContinue }
    if ($StoreDrivers) { $InfCandidates += $StoreDrivers }

    $InfCandidates = $InfCandidates | Sort-Object FullName -Unique
    if ($InfCandidates) {
        foreach ($Inf in $InfCandidates) { Invoke-PnpUtilAdd $Inf.FullName }
    } else {
        Write-Step "Nenhum .inf empacotado ou do Apple Mobile Device Support encontrado."
    }

    # Já existe driver Apple no DriverStore?
    $DriverStoreApple = (& pnputil.exe /enum-drivers 2>$null | Out-String) -match "usbaapl64\.inf|Apple Inc\."
    if ($DriverStoreApple) {
        Write-Step "Driver Apple Mobile Device USB presente no DriverStore."
    }

    # Instalação opcional do Apple Devices / iTunes via winget.
    $Amds = Get-Service -Name "Apple Mobile Device Service" -ErrorAction SilentlyContinue
    if (-not $DriverStoreApple -and -not $Amds) {
        if ($InstallAppleSupport) {
            $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
            if ($winget) {
                Write-Step "Instalando 'Apple Devices' (Microsoft Store) via winget..."
                & winget.exe install --id 9NP83LWLPZ9K --source msstore --accept-package-agreements --accept-source-agreements --silent
                if ($LASTEXITCODE -ne 0) {
                    Write-Step "Fallback: instalando iTunes (Apple.iTunes) via winget..."
                    & winget.exe install --id Apple.iTunes --source winget --accept-package-agreements --accept-source-agreements --silent
                }
                if ($LASTEXITCODE -ne 0) { Write-Warn "winget não conseguiu instalar Apple Devices/iTunes (código $LASTEXITCODE)." }
            } else {
                Write-Warn "winget.exe não disponível. Instale manualmente 'Apple Devices' (Microsoft Store) ou o iTunes."
            }
        } else {
            Write-Warn ("Nenhum driver Apple USB nem 'Apple Mobile Device Service' encontrado. " +
                "Instale 'Apple Devices' (Microsoft Store) ou o iTunes, ou execute novamente com -InstallAppleSupport.")
        }
    }

    # Força o PnP a reavaliar dispositivos conectados (aplica o driver ao iPhone já plugado).
    & pnputil.exe /scan-devices 2>&1 | Out-Null

    # -----------------------------------------------------------------------
    # 4. Serviço Apple Mobile Device Service (AMDS) e limpeza do legado usbmuxd
    # -----------------------------------------------------------------------
    $Legacy = Get-CimInstance -ClassName Win32_Service -Filter "Name='usbmuxd'" -ErrorAction SilentlyContinue
    if ($Legacy -and ($Legacy.PathName -match "iOS_Forensics|usbmuxd\.exe")) {
        Write-Step "Removendo serviço legado 'usbmuxd' criado pela v1.1.0 (não compatível com o SCM / erro 1053)..."
        Stop-Service -Name "usbmuxd" -Force -ErrorAction SilentlyContinue
        & sc.exe delete usbmuxd | Out-Null
    }

    $Amds = Get-Service -Name "Apple Mobile Device Service" -ErrorAction SilentlyContinue
    if ($Amds) {
        Write-Step "Configurando 'Apple Mobile Device Service' para início automático..."
        Set-Service -Name "Apple Mobile Device Service" -StartupType Automatic -ErrorAction SilentlyContinue
        if ($Amds.Status -ne "Running") {
            Start-Service -Name "Apple Mobile Device Service" -ErrorAction SilentlyContinue
        }
        $Amds.Refresh()
        Write-Step "Status do AMDS: $($Amds.Status)"
    } else {
        Write-Warn ("'Apple Mobile Device Service' não instalado. O libimobiledevice precisa do AMDS (usbmuxd da Apple) " +
            "para enxergar o iPhone no Windows. Instale 'Apple Devices' ou o iTunes.")
    }

    # Diagnóstico: dispositivos Apple presentes e status do driver.
    $AppleDevs = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.InstanceId -match "VID_05AC" }
    if ($AppleDevs) {
        foreach ($d in $AppleDevs) { Write-Step ("Dispositivo: {0} | Status={1} | Classe={2}" -f $d.FriendlyName, $d.Status, $d.Class) }
        if ($AppleDevs | Where-Object { $_.Status -ne "OK" }) {
            Write-Warn "Há dispositivos Apple com driver em estado diferente de OK (verifique o Gerenciador de Dispositivos)."
        }
    } else {
        Write-Step "Nenhum dispositivo Apple (VID_05AC) conectado no momento."
    }
}

# ---------------------------------------------------------------------------
# 5. Diretório Lockdown (pareamentos)
# ---------------------------------------------------------------------------
$LockdownDir = Join-Path $env:ProgramData "Apple\Lockdown"
if (-not (Test-Path $LockdownDir)) {
    New-Item -ItemType Directory -Force -Path $LockdownDir | Out-Null
    Write-Step "Diretório de pareamento Lockdown criado em $LockdownDir"
}

$exitCode = 0
if ($script:RebootRequired) { $exitCode = 3010 }
Write-Step ("Concluído. Avisos: {0}. Reboot necessário: {1}. Log: {2}" -f $script:Warnings, $script:RebootRequired, $LogPath)
try { Stop-Transcript | Out-Null } catch { }
exit $exitCode
