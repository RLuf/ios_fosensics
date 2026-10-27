<#
.SYNOPSIS
    Assina digitalmente os binários (.exe) e o instalador Windows com Authenticode (signtool.exe).
    Suporta certificado PFX via variáveis de ambiente (WINDOWS_PFX_BASE64 / WINDOWS_PFX_PASSWORD)
    ou gera automaticamente um Certificado Code Signing autoassinado para o pacote de Release.
#>
param(
    [Parameter(Mandatory=$true)]
    [string[]]$TargetFiles,
    [string]$CertOutputDir = "$PSScriptRoot\..\..\build\bundle\drivers"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $CertOutputDir | Out-Null
$PfxPath = Join-Path $env:TEMP "ios_forensics_codesign.pfx"
$CerPath = Join-Path $CertOutputDir "RLuf_iOS_Forensics_CodeSign.cer"
$PfxPasswordPlain = if ($env:WINDOWS_PFX_PASSWORD) { $env:WINDOWS_PFX_PASSWORD } else { "iOSForensicsSign2026!" }
$SecurePwd = ConvertTo-SecureString -String $PfxPasswordPlain -Force -AsPlainText

if ($env:WINDOWS_PFX_BASE64) {
    Write-Host "==> Carregando certificado PFX a partir de WINDOWS_PFX_BASE64..." -ForegroundColor Cyan
    $PfxBytes = [Convert]::FromBase64String($env:WINDOWS_PFX_BASE64)
    [IO.File]::WriteAllBytes($PfxPath, $PfxBytes)
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPasswordPlain, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable)
    [IO.File]::WriteAllBytes($CerPath, $Cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))
} elseif (-not (Test-Path $PfxPath)) {
    Write-Host "==> Gerando Certificado Authenticode Code Signing (CN=RLuf iOS Forensics Open Source)..." -ForegroundColor Cyan
    $Cert = New-SelfSignedCertificate `
        -Subject "CN=RLuf iOS Forensics Open Source, O=RLuf Security & Forensics, C=BR" `
        -Type CodeSigningCert `
        -KeySpec Signature `
        -KeyLength 2048 `
        -HashAlgorithm SHA256 `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(3)

    Export-PfxCertificate -Cert $Cert -FilePath $PfxPath -Password $SecurePwd | Out-Null
    Export-Certificate -Cert $Cert -FilePath $CerPath | Out-Null
    try {
        Import-Certificate -FilePath $CerPath -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null
        Import-Certificate -FilePath $CerPath -CertStoreLocation "Cert:\LocalMachine\TrustedPublisher" | Out-Null
    } catch {
        Write-Warning "Aviso ao importar certificado no LocalMachine: $_"
    }
}

# Localiza signtool.exe no Windows SDK
$SignTool = Get-ChildItem -Path "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Recurse -Filter "signtool.exe" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "x64" } |
    Sort-Object FullName -Descending |
    Select-Object -First 1

foreach ($File in $TargetFiles) {
    if (-not (Test-Path $File)) {
        throw "Arquivo não encontrado para assinatura: $File"
    }
    Write-Host "==> Assinando $File ..." -ForegroundColor Green
    if ($SignTool) {
        & $SignTool.FullName sign /f "$PfxPath" /p "$PfxPasswordPlain" /fd SHA256 /tr "http://timestamp.digicert.com" /td SHA256 /d "iOS Forensics TUI Suite" "$File"
        if ($LASTEXITCODE -ne 0) {
            & $SignTool.FullName sign /f "$PfxPath" /p "$PfxPasswordPlain" /fd SHA256 /d "iOS Forensics TUI Suite" "$File"
        }
    } else {
        $LoadedCert = Get-PfxCertificate -FilePath $PfxPath -Password $SecurePwd
        Set-AuthenticodeSignature -FilePath $File -Certificate $LoadedCert -HashAlgorithm SHA256 | Out-Null
    }

    $Sig = Get-AuthenticodeSignature -FilePath $File
    if (-not $Sig.SignerCertificate) {
        throw "Assinatura falhou para $File"
    }
    Write-Host "    Assinado com sucesso ($($File | Split-Path -Leaf)): Status=$($Sig.Status) | Thumbprint=$($Sig.SignerCertificate.Thumbprint)" -ForegroundColor Cyan
}
$global:LASTEXITCODE = 0
