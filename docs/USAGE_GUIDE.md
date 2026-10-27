# 📖 Guia de Uso e Operação Pericial / Usage & Forensic Operations Guide

**🇧🇷 Português** | **[🇺🇸 English](#-english--usage--forensic-operations-guide)**

---

## 🇧🇷 Português — Guia de Uso

### 1. Pré-requisitos e Instalação

#### No Windows 10 / 11 (x64) — Recomendado
1. Acesse a página de [**Releases**](https://github.com/RLuf/ios_fosensics/releases) e baixe o instalador assinado `iOS_Forensics_Setup_v1.1.0_x64.exe` (ou a versão portátil `.zip`).
2. Execute o instalador como **Administrador** e mantenha marcadas as opções:
   - *Instalar/Reparar Drivers USB Apple (VID_05AC) e Serviço usbmuxd*
   - *Instalar Certificado de Assinatura Authenticode nos Editores Confiáveis*
3. Conecte o iPhone/iPad via cabo USB (Lightning ou USB-C) e inicie o **iOS Forensics TUI Suite** pelo Menu Iniciar ou Área de Trabalho.

#### No Linux (Debian / Ubuntu / Proxmox)
```bash
sudo apt-get install -y libimobiledevice-utils usbmuxd ideviceinstaller python3-pip
pip install -r requirements.txt
python3 ios_forensics_tui.py
```

---

### 2. Atalhos de Teclado e Ações Interativas na TUI

| Tecla | Botão na Interface | Função Executada |
| :---: | :--- | :--- |
| **`R`** | `🔄 [R] Atualizar` | Executa nova varredura completa via USB (`ideviceinfo`, `IORegistry`, `NVRAM`, `AFC`, `SQLite`) |
| **`P`** | `🔑 [P] Re-Parear (Trust)` | Executa `idevicepair pair` e `idevicepair validate` para estabelecer/verificar confiança com o host |
| **`E`** | `💾 [E] Exportar Perícia` | Gera o pacote pericial completo (`forensic_report.json` + fotos `DCIM` + bancos `SQLite` + plists `Lockdown` + `manifest_sha256.txt`) |
| **`S`** | `📡 [S] Amostra Syslog` | Captura 4 segundos de logs em tempo real do `idevicesyslog` e exibe na Aba 6 |
| **`C`** | `💥 [C] Baixar Crashes` | Extrai relatórios de diagnóstico e crash do iOS (`idevicecrashreport -k`) |
| **`Q`** | `Sair` | Encerra a aplicação TUI com segurança |

---

### 3. Modo de Exportação Rápida via CLI (`--cli-export`)

Para automação forense, triagem em lote ou execução em terminais sem interface interativa:

```bash
# Windows (Executável)
ios_forensics.exe --cli-export

# Linux / macOS / Python
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
1. Download the signed installer `iOS_Forensics_Setup_v1.1.0_x64.exe` (or the portable `.zip` archive) from [**Releases**](https://github.com/RLuf/ios_fosensics/releases).
2. Run the setup as **Administrator** and keep the driver & certificate tasks enabled:
   - *Install/Repair Apple USB Drivers (VID_05AC) and usbmuxd Service*
   - *Install Authenticode Signing Certificate into Trusted Publishers*
3. Connect the target iPhone/iPad via USB and launch **iOS Forensics TUI Suite**.

#### Linux (Debian / Ubuntu / Proxmox)
```bash
sudo apt-get install -y libimobiledevice-utils usbmuxd python3-pip
pip install -r requirements.txt
python3 ios_forensics_tui.py
```

---

### 2. Keyboard Shortcuts & TUI Controls

| Key | UI Button | Action |
| :---: | :--- | :--- |
| **`R`** | `🔄 [R] Atualizar` | Re-runs full USB forensic acquisition (`ideviceinfo`, `IORegistry`, `NVRAM`, `AFC`, `SQLite`) |
| **`P`** | `🔑 [P] Re-Parear (Trust)` | Runs `idevicepair pair` & `idevicepair validate` to establish or verify Lockdown host trust |
| **`E`** | `💾 [E] Exportar Perícia` | Exports a full forensic package (`forensic_report.json`, `DCIM` photos, `SQLite` DBs, `Lockdown` plists, and `manifest_sha256.txt`) |
| **`S`** | `📡 [S] Amostra Syslog` | Captures a 4-second live stream from `idevicesyslog` into Tab 6 |
| **`C`** | `💥 [C] Baixar Crashes` | Pulls crash & diagnostic logs via `idevicecrashreport -k` |
| **`Q`** | `Quit` | Cleanly exits the TUI application |

---

### 3. Headless CLI Export Mode (`--cli-export`)

```bash
ios_forensics.exe --cli-export
```
Automatically collects all forensic layers, writes the timestamped export folder (`Documents\iOS_Forensics_Exports\` on Windows or `/root` / `$HOME` on Linux), computes `manifest_sha256.txt`, and prints a formatted summary in the terminal.
