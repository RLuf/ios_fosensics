<#
.SYNOPSIS
    Baixa e prepara os binários Win64 do libimobiledevice / usbmuxd e pacotes de drivers USB Apple
    para empacotamento junto ao instalador Windows do iOS Forensics TUI.
#>
param(
    [string]$OutputDir = "$PSScriptRoot\..\..\build\bundle"
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$BinDir = Join-Path $OutputDir "bin"
$DriversDir = Join-Path $OutputDir "drivers"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
New-Item -ItemType Directory -Force -Path $DriversDir | Out-Null

Write-Host "==> [1/3] Baixando binários libimobiledevice + usbmuxd (Win64)..." -ForegroundColor Cyan
$ImobileUrls = @(
    "https://github.com/libimobiledevice-win32/imobiledevice-net/releases/download/v1.3.17/libimobiledevice.1.2.1-r1122-win-x64.zip",
    "https://github.com/LikiTiki/imobiledevice-win-x64/releases/latest/download/libimobiledevice-win-x64.zip"
)

$ZipPath = Join-Path $env:TEMP "libimobiledevice-win64.zip"
$Downloaded = $false
foreach ($Url in $ImobileUrls) {
    try {
        Write-Host "Tentando $Url ..."
        Invoke-WebRequest -Uri $Url -OutFile $ZipPath -UseBasicParsing -TimeoutSec 60
        if ((Test-Path $ZipPath) -and ((Get-Item $ZipPath).Length -gt 100000)) {
            $Downloaded = $true
            break
        }
    } catch {
        Write-Warning "Falha ao baixar de $Url : $_"
    }
}

if ($Downloaded) {
    Expand-Archive -Path $ZipPath -DestinationPath $BinDir -Force
    Write-Host "Binários libimobiledevice extraídos em $BinDir" -ForegroundColor Green
} else {
    Write-Warning "Usando fallback via NuGet package imobiledevice-x64..."
    $NugetUrl = "https://www.nuget.org/api/v2/package/imobiledevice-x64/1.3.17"
    Invoke-WebRequest -Uri $NugetUrl -OutFile $ZipPath -UseBasicParsing -TimeoutSec 60
    $ExtractTmp = Join-Path $env:TEMP "imobile_nuget"
    Expand-Archive -Path $ZipPath -DestinationPath $ExtractTmp -Force
    Get-ChildItem -Path $ExtractTmp -Recurse -Include "*.exe","*.dll" | Copy-Item -Destination $BinDir -Force
}

Write-Host "==> [2/3] Preparando manifesto de drivers Apple Mobile Device USB (WinUSB / usbaapl64)..." -ForegroundColor Cyan
$DriverReadme = @"
iOS Forensics TUI - Pacote de Drivers Windows (Apple USB & usbmuxd)
===================================================================
Este diretório contém os scripts de provisionamento automático para:
1. Apple Mobile Device USB Driver (VID_05AC)
2. Serviço Apple Mobile Device Service / usbmuxd (Multiplexador USB TCP)
3. Certificado de Assinatura de Código (Authenticode)

Para instalar ou reparar manualmente os drivers como Administrador:
  powershell -ExecutionPolicy Bypass -File .\install_drivers.ps1
"@
Set-Content -Path (Join-Path $DriversDir "README_DRIVERS.txt") -Value $DriverReadme -Encoding UTF8

# Copia o script de instalação de drivers para a pasta empacotada
Copy-Item -Path (Join-Path $PSScriptRoot "install_drivers.ps1") -Destination $DriversDir -Force

Write-Host "==> [3/3] Verificando conteúdo empacotado..." -ForegroundColor Cyan
Get-ChildItem -Path $BinDir | Select-Object Name, Length | Format-Table -AutoSize
