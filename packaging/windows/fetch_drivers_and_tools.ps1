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
    "https://github.com/libimobiledevice-win32/imobiledevice-net/releases/download/v1.3.17/iMobileDevice-net.1.3.17.nupkg"
)

$ZipPath = Join-Path $env:TEMP "libimobiledevice-win64.zip"
$ExtractTmp = Join-Path $env:TEMP "imobile_extract_tmp"
if (Test-Path $ExtractTmp) { Remove-Item -Recurse -Force $ExtractTmp }
New-Item -ItemType Directory -Force -Path $ExtractTmp | Out-Null

$Downloaded = $false
foreach ($Url in $ImobileUrls) {
    try {
        Write-Host "Baixando de $Url ..."
        Invoke-WebRequest -Uri $Url -OutFile $ZipPath -UseBasicParsing -TimeoutSec 90
        if ((Test-Path $ZipPath) -and ((Get-Item $ZipPath).Length -gt 100000)) {
            $Downloaded = $true
            break
        }
    } catch {
        Write-Warning "Falha ao baixar de $Url : $_"
    }
}

if (-not $Downloaded) {
    throw "Não foi possível baixar o pacote libimobiledevice Win64!"
}

Expand-Archive -Path $ZipPath -DestinationPath $ExtractTmp -Force
Get-ChildItem -Path $ExtractTmp -Recurse -Include "*.exe","*.dll" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $BinDir -Force
}
Write-Host "Binários libimobiledevice extraídos em $BinDir" -ForegroundColor Green

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
$BundledFiles = Get-ChildItem -Path $BinDir
Write-Host "Total de arquivos em bin/: $($BundledFiles.Count)" -ForegroundColor Green
$BundledFiles | Select-Object -First 25 Name, Length | Format-Table -AutoSize
$global:LASTEXITCODE = 0
