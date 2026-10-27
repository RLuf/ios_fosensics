# 📖 Guia de Uso e Operação Pericial / Usage & Forensic Operations Guide

**🇧🇷 Português** | **[🇺🇸 English](#-english--usage--forensic-operations-guide)**

---

## 🇧🇷 Português — Guia de Uso

### 1. Pré-requisitos e Instalação

#### No Windows 10 / 11 (x64) — Recomendado

1. Acesse a página de [**Releases**](https://github.com/RLuf/ios_fosensics/releases) e baixe o instalador assinado `iOS_Forensics_Setup_v1.2.0_x64.exe` (ou a versão portátil `.zip`).
2. Execute o instalador (ou o atalho *Reparar Drivers USB Apple*). O script [`install_drivers.ps1`](../packaging/windows/install_drivers.ps1) agora solicita automaticamente elevação administrativa via UAC:
   - *Instalação de Drivers USB Apple (`VID_05AC`) e rescaneamento via `pnputil.exe`*
   - *Verificação e inicialização do Apple Mobile Device Service (AMDS)*
   - *Gravação persistente de logs em `%ProgramData%\iOS_Forensics\logs\install_drivers_<timestamp>.log`*
   - *Importação do certificado Authenticode nos Editores Confiáveis do Windows*
3. Conecte o iPhone/iPad via cabo USB (Lightning ou USB-C) e inicie o **iOS Forensics TUI Suite**. A abertura é instantânea (< 100 ms), pois a coleta de dados pesada ocorre em threads de fundo.

#### No Linux (Debian / Ubuntu / Proxmox)

```bash
sudo apt-get install -y libimobiledevice-utils usbmuxd ideviceinstaller python3-pip
pip install -r requirements.txt
python3 ios_forensics_tui.py
```

---

### 2. Atalhos de Teclado e Operação Não-Bloqueante

A interface é construída sobre o framework **Textual** e opera em arquitetura assíncrona. Toda operação pesada de I/O roda em segundo plano (`@work(thread=True)`), mantendo o display, rolagem e atalhos 100% responsivos:

| Tecla | Botão na Interface | Função Executada (Background Worker) |
| :---: | :--- | :--- |
| **`R`** | `🔄 [R] Atualizar` | Dispara coleta assíncrona completa (`ideviceinfo`, `IORegistry`, `NVRAM`, `AFC`, `SQLite`) sem travar a interface |
| **`P`** | `🔑 [P] Re-Parear (Trust)` | Executa `idevicepair pair` e `idevicepair validate` em background para estabelecer/verificar confiança com o host |
| **`E`** | `💾 [E] Exportar Perícia` | Exporta o pacote pericial completo e gera o manifesto criptográfico `manifest_sha256.txt` |
| **`S`** | `📡 [S] Amostra Syslog` | Captura 4 segundos de logs em tempo real do `idevicesyslog` em background e exibe na Aba 6 |
| **`C`** | `💥 [C] Baixar Crashes` | Extrai relatórios de diagnóstico e crash do iOS (`idevicecrashreport -k`) |
| **`Q`** | `Sair` | Encerra a aplicação TUI com segurança |

---

### 3. Modos Especiais via CLI

```bash
# Inicialização sem varredura imediata de hardware (triagem rápida ou inspeção visual)
ios_forensics.exe --no-auto-collect
python3 ios_forensics_tui.py --no-auto-collect

# Exportação pericial autônoma em linha de comando (Headless CLI Export)
ios_forensics.exe --cli-export
python3 ios_forensics_tui.py --cli-export
```

#### Estrutura da Pasta Exportada (`forensics_iphone_<UDID>_<TIMESTAMP>/`)

```text
forensics_iphone_00008020-000215342EC1002E_20261027_111500/
├── forensic_report.json       # Dump estruturado completo (Hardware, IORegistry, NVRAM, SIM, Bateria, AFC)
├── manifest_sha256.txt        # Cadeia de custódia com hashes SHA-256 de todos os arquivos exportados
├── DCIM_100APPLE/             # Fotos e vídeos originais extraídos via AFC (/DCIM/100APPLE)
├── SQLite_DBs/                # Bancos SQLite extraídos (Photos.sqlite, downloads.28.sqlitedb, mediaanalysis.db)
└── lockdown/                  # Certificados e registros de pareamento (.plist)
```

---

## 🇺🇸 English — Usage & Forensic Operations Guide

### 1. Prerequisites & Installation

#### Windows 10 / 11 (x64) — Recommended

1. Download the signed installer `iOS_Forensics_Setup_v1.2.0_x64.exe` (or the portable `.zip` archive) from [**Releases**](https://github.com/RLuf/ios_fosensics/releases).
2. Run the installer or the *Repair Apple USB Drivers* Start Menu shortcut. It automatically requests administrative elevation via UAC:
   - *Provisions Apple USB Drivers (`VID_05AC`) and rescans hardware bus with `pnputil.exe`*
   - *Verifies and starts Apple Mobile Device Service (AMDS)*
   - *Writes persistent setup logs to `%ProgramData%\iOS_Forensics\logs\install_drivers_<timestamp>.log`*
   - *Imports the Authenticode code signing certificate into Trusted Publishers*
3. Connect the iPhone/iPad via USB and launch **iOS Forensics TUI Suite**. The window appears instantly (< 100 ms) without freezing.

#### Linux (Debian / Ubuntu / Proxmox)

```bash
sudo apt-get install -y libimobiledevice-utils usbmuxd python3-pip
pip install -r requirements.txt
python3 ios_forensics_tui.py
```

---

### 2. Keyboard Shortcuts & Non-Blocking Worker Controls

Built with **Textual**, all heavy device I/O actions run on background worker threads (`@work(thread=True)`), preventing main thread event loop starvation and UI unresponsiveness:

| Key | UI Button | Action (Background Worker) |
| :---: | :--- | :--- |
| **`R`** | `🔄 [R] Atualizar` | Background full acquisition (`ideviceinfo`, `IORegistry`, `NVRAM`, `AFC`, `SQLite`) |
| **`P`** | `🔑 [P] Re-Parear (Trust)` | Asynchronously executes `idevicepair pair` & `idevicepair validate` |
| **`E`** | `💾 [E] Exportar Perícia` | Asynchronously exports forensic artifacts and computes `manifest_sha256.txt` |
| **`S`** | `📡 [S] Amostra Syslog` | Asynchronously captures a 4-second stream from `idevicesyslog` |
| **`C`** | `💥 [C] Baixar Crashes` | Asynchronously pulls crash & diagnostic logs via `idevicecrashreport -k` |
| **`Q`** | `Quit` | Cleanly exits the TUI application |

---

### 3. CLI Command Options

```bash
# Launch without immediate hardware scan (useful when device is not yet attached)
ios_forensics.exe --no-auto-collect
python3 ios_forensics_tui.py --no-auto-collect

# Headless automated CLI export mode
ios_forensics.exe --cli-export
python3 ios_forensics_tui.py --cli-export
```
