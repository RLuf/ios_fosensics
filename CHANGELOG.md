# 📜 Changelog / Histórico de Alterações

Todas as mudanças notáveis neste projeto são documentadas neste arquivo (em **Português** e **English**), seguindo o formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e [Semantic Versioning](https://semver.org/).

---

## [1.1.0] - 2026-10-27

### 🇧🇷 Português

#### Adicionado (Added)
- **Manifesto de Cadeia de Custódia (`manifest_sha256.txt`)**: Geração automática de hashes SHA-256 para todos os arquivos extraídos durante a exportação do pacote pericial (`export_full_forensic_package`), implementado na auditoria do `@jules` ([PR #3](https://github.com/RLuf/ios_fosensics/pull/3)).
- **Documentação Bilíngue Completa (PT-BR / EN) e Capturas de Tela TUI (`docs/assets/*.svg`)**:
  - Novo [`README.md`](README.md) bilíngue com prints reais das 6 abas da interface TUI.
  - Novos guias técnicos e de uso em [`./docs/`](docs/INDEX.md): [`INDEX.md`](docs/INDEX.md), [`USAGE_GUIDE.md`](docs/USAGE_GUIDE.md), [`FORENSIC_ARCHITECTURE.md`](docs/FORENSIC_ARCHITECTURE.md), [`WINDOWS_INSTALLER_AND_DRIVERS.md`](docs/WINDOWS_INSTALLER_AND_DRIVERS.md) e [`AI_CODE_REVIEW.md`](docs/AI_CODE_REVIEW.md).
- **Diretrizes de Agentes e Regra de Ouro**: Criados [`AGENTS.md`](AGENTS.md) e [`AGENTES.md`](AGENTES.md) documentando a Regra de Ouro de backup prévio em `archived/` e sincronização obrigatória de documentação.
- **Expansão da Suíte de Testes (`tests/test_forensics.py`)**: Cobertura ampliada de 5 para 13 testes unitários automatizados (incluindo mocks de extração AFC, SQLite `ZASSET`, Lockdown, `run_cmd` e geração de pacote forense).

#### Corrigido & Melhorado (Fixed & Improved)
- **Segurança SQLite (`collect_afc_forensics`)**: Escape seguro de identificadores de tabelas (`safe_t = t.replace('"', '""')`) e tratamento específico de `sqlite3.Error`.
- **Resiliência de Timestamps no Windows**: Proteção contra `OverflowError` e `OSError` ao converter `BootPathUpdated` e `TimeIntervalSince1970` no Windows (`msvcrt`), além de timestamps CoreData explícitos em UTC.
- **Tipagem e Tratamento de Exceções**: Modernização de type hints (`dict`, `list`, `ClassVar`, `bytes | None`) e substituição de `except Exception` genéricos por exceções específicas (`plistlib.InvalidFileException`, `UnicodeDecodeError`, `OSError`).

### 🇺🇸 English

#### Added
- **Forensic Chain-of-Custody Manifest (`manifest_sha256.txt`)**: Automatic SHA-256 hash manifest generation for all exported files in `export_full_forensic_package`, contributed via `@jules` audit ([PR #3](https://github.com/RLuf/ios_fosensics/pull/3)).
- **Full Bilingual Documentation (PT-BR / EN) & High-Resolution TUI Screenshots (`docs/assets/*.svg`)**:
  - Updated [`README.md`](README.md) with visual previews of all 6 forensic tabs.
  - Comprehensive technical documentation suite in [`./docs/`](docs/INDEX.md).
- **AI Agent Guidelines & Golden Rule**: Added [`AGENTS.md`](AGENTS.md) and [`AGENTES.md`](AGENTES.md) enforcing the `archived/` backup Golden Rule.
- **Expanded Unit Test Suite (`tests/test_forensics.py`)**: Increased from 5 to 13 unit tests covering AFC extraction, SQLite `ZASSET` parsing, Lockdown records, and package export.

#### Fixed & Changed
- **SQLite Identifier Escaping**: Properly escaped table names in `collect_afc_forensics` (`safe_t = t.replace('"', '""')`) and narrowed exception handling to `sqlite3.Error`.
- **Windows Timestamp Safety**: Guarded `fromtimestamp()` conversions against `OverflowError`/`OSError` on Windows and enforced explicit UTC timezone on CoreData timestamps.

---

## [1.0.0] - 2026-10-27

### 🇧🇷 Português / 🇺🇸 English
- **Lançamento Inicial (`v1.0.0`) / Initial Release**:
  - Suíte interativa TUI em Python (`Textual` + `Rich`) para perícia forense e diagnóstico USB em dispositivos iOS (`ios_forensics_tui.py`).
  - Adaptação multiplataforma completa para **Windows 10/11 (x64)**, **Linux** e **macOS**.
  - Pipeline automatizado no GitHub Actions ([`.github/workflows/windows-release.yml`](.github/workflows/windows-release.yml)) gerando executável `PyInstaller`, instalador `Inno Setup` (`iOS_Forensics_Setup_v1.0.0_x64.exe`), pacote portátil `.zip`, integração de binários `libimobiledevice`/`usbmuxd` Win64, scripts de instalação de drivers USB Apple (`pnputil`) e assinatura digital Authenticode SHA-256 (`signtool.exe`).
