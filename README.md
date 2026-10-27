# 📱 iOS Forensics & USB Debug TUI Suite (`ios_forensics`)

[![Windows Installer & Release](https://github.com/RLuf/ios_fosensics/actions/workflows/windows-release.yml/badge.svg)](https://github.com/RLuf/ios_fosensics/actions/workflows/windows-release.yml)
[![AI Code Review & Quality Gate](https://github.com/RLuf/ios_fosensics/actions/workflows/ai-code-review.yml/badge.svg)](https://github.com/RLuf/ios_fosensics/actions/workflows/ai-code-review.yml)

Suíte interativa em **TUI (Textual + Rich)** para **Perícia Forense Digital, Diagnóstico de Hardware e Inspeção Profunda USB em Dispositivos Apple iOS (iPhone / iPad)**, compatível com **Windows 10/11 (x64)**, **Linux** e **macOS**.

---

## ✨ Recursos Forenses

1. **Resumo & Pareamento (`lockdownd` / `usbmuxd`)**
   - Identificação completa (UDID, ECID em hex, versão do iOS, iBoot, `ActivationState`, `PasswordProtected`, fuso e relógio interno).
   - Inspeção automática de certificados de pareamento em `C:\ProgramData\Apple\Lockdown` (Windows) ou `/var/lib/lockdown` (Linux).
2. **Auditoria de Hardware & Seriais (`IORegistry`)**
   - Extração e decodificação de data/fábrica de seriais de componentes internos: Placa Lógica (`MLBSerialNumber`), Bateria (`AppleSmartBattery`), Display/Touch (`raw-panel-serial-number`), Vidro Frontal (`coverglass-serial-number`), FaceID Flood Illuminator (`rosaline-serial-num`), Sensor ALS e Chip USB Tristar/Hydra.
3. **NVRAM Decodificada, iCloud (FMI / Activation Lock) & Telefonia SIM**
   - Decodificação de variáveis Base64 e Binary Plist da NVRAM (`fm-activation-locked`, `fm-account-masked`, `fm-spstatus`, `fm-spkeys`, `usbcfwflasherResult`).
   - Histórico em cache do último SIM Card (`ICCID`, `IMSI`, operadora `MCC/MNC`, `IMEI 1/2`, `MEID`, endereços MAC Wi-Fi/Bluetooth).
4. **Telemetria Química de Bateria & Barramento USB**
   - Saúde nominal vs. capacidade de projeto, contagem de ciclos, tensão (mV), corrente instantânea (mA), temperatura da célula e detalhes do adaptador USB.
   - Diagnóstico PnP no Windows (`VID_05AC` / `Apple Mobile Device Service`) e `lsusb`/`dmesg` no Linux.
5. **Sistema de Arquivos AFC, EXIF de Fotos & Bancos SQLite**
   - Varredura de `/DCIM/100APPLE`, extração de metadados EXIF de imagens e análise automática de tabelas SQLite (`Photos.sqlite`, `downloads.28.sqlitedb`, `mediaanalysis.db`, incluindo `ZASSET`).
6. **Crash Reports & Live Syslog**
   - Extração de relatórios de diagnóstico (`idevicecrashreport`) e captura ao vivo do `idevicesyslog`.
7. **Exportação de Pacote Pericial (`[E]` ou `--cli-export`)**
   - Gera diretório datado com `forensic_report.json`, fotos do `DCIM`, bancos SQLite e plists de Lockdown.

---

## 🪟 Instalador e Release para Windows (x64)

O workflow [`.github/workflows/windows-release.yml`](.github/workflows/windows-release.yml) automatiza todo o ciclo de build e distribuição para Windows:

- **Executável Nativo (`PyInstaller`)**: Compila `ios_forensics.exe` com metadados PE (`version_info.txt`).
- **Binários `libimobiledevice` + `usbmuxd` (Win64)**: Empacota automaticamente `ideviceinfo.exe`, `idevicepair.exe`, `idevicediagnostics.exe`, `idevicesyslog.exe`, `idevicecrashreport.exe`, `afcclient.exe`, `usbmuxd.exe` e DLLs em `bin/`.
- **Drivers USB Apple & Serviço (`install_drivers.ps1`)**: Instala drivers `.inf` via `pnputil.exe`, registra/inicia o serviço `Apple Mobile Device Service` / `usbmuxd` e prepara `C:\ProgramData\Apple\Lockdown`.
- **Assinatura Digital Authenticode (`sign_artifacts.ps1`)**: Assina `ios_forensics.exe` e o instalador final `iOS_Forensics_Setup_v1.0.0_x64.exe` via `signtool.exe` (SHA-256 + RFC3161 Timestamp DigiCert), suportando certificado corporativo via GitHub Secrets (`WINDOWS_PFX_BASE64` / `WINDOWS_PFX_PASSWORD`) ou gerando certificado Authenticode acompanhado da chave pública `.cer`.
- **Instalador Inno Setup (`installer.iss`)**: Gera `iOS_Forensics_Setup_v1.0.0_x64.exe` + pacote portátil `.zip` + `SHA256SUMS.txt`.

---

## 🚀 Como Executar

### No Windows (Instalador)
Baixe `iOS_Forensics_Setup_v1.0.0_x64.exe` na aba [**Releases**](https://github.com/RLuf/ios_fosensics/releases), execute como Administrador e abra **iOS Forensics TUI Suite** pelo Menu Iniciar ou Área de Trabalho.

### Via Python (Linux / Windows / macOS)
```bash
pip install -r requirements.txt
python ios_forensics_tui.py

# Modo de exportação rápida via linha de comando (sem abrir a TUI):
python ios_forensics_tui.py --cli-export
```

---

## 🤖 Conferência e Revisão de Código (AI Code Review)

Este repositório inclui integração e solicitação de conferência técnica por:
- **Jules** (`@jules` / `@google-labs-jules`)
- **Codex** (`@codex`)
- **Gemini** (`@gemini` / `@gemini-code-assist`)
