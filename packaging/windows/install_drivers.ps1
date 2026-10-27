<#
.SYNOPSIS
    Instala os drivers Apple Mobile Device USB (pnputil), configura o serviço usbmuxd / Apple Mobile Device Service
    e importa opcionalmente o certificado de assinatura do pacote iOS Forensics TUI no Windows.
#>
param(
    [switch]$InstallCertificate = $true,
    [switch]$Quiet = $false
)

$ErrorActionPreference = "Continue"

function Write-Step($msg) {
    if (-not $Quiet) {
        Write-Host "[iOS Forensics Driver Setup] $msg" -ForegroundColor Cyan
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot = Split-Path -Parent $ScriptDir
$BinDir = Join-Path $AppRoot "bin"

# 1. Importa certificado público Authenticode (.cer) se presente
if ($InstallCertificate) {
    $CerFile = Get-ChildItem -Path $ScriptDir -Filter "*.cer" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($CerFile) {
        Write-Step "Importando certificado de assinatura ($($CerFile.Name)) em TrustedPublisher..."
        try {
            Import-Certificate -FilePath $CerFile.FullName -CertStoreLocation "Cert:\LocalMachine\TrustedPublisher" | Out-Null
            Import-Certificate -FilePath $CerFile.FullName -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null
            Write-Step "Certificado instalado com sucesso."
        } catch {
            Write-Warning "Não foi possível instalar o certificado no LocalMachine (requer privilégios de Administrador): $_"
        }
    }
}

# 2. Instala qualquer arquivo .inf presente na pasta drivers via pnputil
$InfFiles = Get-ChildItem -Path $ScriptDir -Recurse -Filter "*.inf" -ErrorAction SilentlyContinue
if ($InfFiles) {
    foreach ($Inf in $InfFiles) {
        Write-Step "Instalando driver USB via pnputil: $($Inf.FullName)"
        & pnputil.exe /add-driver "$($Inf.FullName)" /install
    }
} else {
    # Procura drivers Apple existentes no DriverStore ou Common Files
    $CommonAppleDirs = @(
        "$env:CommonProgramFiles\Apple\Mobile Device Support\Drivers",
        "${env:ProgramFiles(x86)}\Common Files\Apple\Mobile Device Support\Drivers"
    )
    foreach ($Dir in $CommonAppleDirs) {
        if (Test-Path $Dir) {
            Get-ChildItem -Path $Dir -Filter "*.inf" | ForEach-Object {
                Write-Step "Registrando driver Apple oficial: $($_.FullName)"
                & pnputil.exe /add-driver "$($_.FullName)" /install
            }
        }
    }
}

# 3. Verifica ou registra o serviço Apple Mobile Device / usbmuxd
$Amds = Get-Service -Name "Apple Mobile Device Service" -ErrorAction SilentlyContinue
if ($Amds) {
    Write-Step "Iniciando serviço 'Apple Mobile Device Service'..."
    Start-Service -Name "Apple Mobile Device Service" -ErrorAction SilentlyContinue
} else {
    $UsbmuxExe = Join-Path $BinDir "usbmuxd.exe"
    if (Test-Path $UsbmuxExe) {
        Write-Step "Configurando serviço usbmuxd a partir de $UsbmuxExe..."
        $ExistingMux = Get-Service -Name "usbmuxd" -ErrorAction SilentlyContinue
        if (-not $ExistingMux) {
            & sc.exe create usbmuxd binPath= "`"$UsbmuxExe`"" start= auto DisplayName= "Apple iOS USB Multiplexer (usbmuxd)" | Out-Null
        }
        Start-Service -Name "usbmuxd" -ErrorAction SilentlyContinue
    }
}

# 4. Garante diretório Lockdown do Windows (C:\ProgramData\Apple\Lockdown)
$LockdownDir = Join-Path $env:ProgramData "Apple\Lockdown"
if (-not (Test-Path $LockdownDir)) {
    New-Item -ItemType Directory -Force -Path $LockdownDir | Out-Null
    Write-Step "Diretório de pareamento Lockdown criado em $LockdownDir"
}

Write-Step "Configuração de drivers e serviços concluída!"
exit 0
