# 📜 Changelog / Histórico de Alterações

Todas as mudanças notáveis neste projeto são documentadas neste arquivo (em **Português** e **English**), seguindo o formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e [Semantic Versioning](https://semver.org/).

---

## [1.2.0] - 2026-10-27

### 🇧🇷 Português (v1.2.0)

#### Adicionado (v1.2.0)

- **Inicialização Instantânea e Arquitetura Assíncrona Não-Bloqueante (Textual Workers)**:
  - Eliminação da chamada síncrona `collector.collect_all()` antes do `app.run()`, permitindo inicialização imediata da janela (< 100 ms).
  - Todas as operações pesadas de I/O (`action_refresh_data`, `action_re_pair`, `action_export_package`, `action_capture_syslog`, `action_pull_crashes`) agora rodam em segundo plano via decorador `@work(thread=True)` do Textual.
  - Controle de concorrência com bloqueio atômico (`threading.Lock` em `_busy`), prevenindo cliques duplicados ou condições de corrida durante extrações periciais.
  - Adicionado novo argumento de linha de comando `--no-auto-collect` para inicializar a interface sem disparar coleta de dados imediata.
- **Otimização de Short-Circuit e Paralelismo Pericial**:
  - Short-circuit imediato quando nenhum dispositivo estiver conectado (`connected_udids` vazio), evitando dezenas de timeouts encadeados de 5 a 8 segundos em 10 domínios e 12 nós do IORegistry.
  - Execução paralela de coletas forenses independentes (`collect_domains`, `collect_ioregistry`, `collect_diagnostics`) com `ThreadPoolExecutor(max_workers=3)`.
  - Agrupamento das consultas PnP e de Serviços no Windows em uma única chamada do PowerShell.
- **Elevação Administrativa Automática e Logs Persistentes de Drivers**:
  - Auto-elevação via UAC (`Start-Process powershell.exe -Verb RunAs`) implementada no script [`install_drivers.ps1`](packaging/windows/install_drivers.ps1) e no atalho de reparo do instalador Inno Setup.
  - Gravação persistente de transcripts de instalação em `%ProgramData%\iOS_Forensics\logs\install_drivers_<timestamp>.log`.
  - Suporte ao parâmetro `-InstallAppleSupport` para instalação automatizada do Apple Devices / iTunes via `winget`.
  - Validação estrita de códigos de retorno do `pnputil.exe` (0, 259, 3010) e rescaneamento forçado de hardware (`/scan-devices`).
- **Suíte de Testes Expandida (`tests/test_forensics.py`)**:
  - Adicionados testes unitários para a versão `1.2.0`, inicialização assíncrona do TUI (`test_tui_app_initialization_async`) e short-circuit sem dispositivo (`test_collect_all_no_device_short_circuit`), totalizando 16 testes passando com 100% de sucesso.

#### Corrigido & Melhorado (v1.2.0)

- **Eliminação de Congelamento e Travamento da Interface**: Resolução definitiva do problema de congelamento da interface gráfica (o app não trava mais o loop de eventos assíncrono do Textual nem gera o aviso "Não Respondendo" no Windows).
- **Remoção de Serviço Windows Incompatível (`usbmuxd`)**: Removida a criação incorreta de serviço NT via `sc.exe create usbmuxd` (que causava erro 1053 e travava o instalador por 30s). O multiplexing USB no Windows é gerenciado pelo Apple Mobile Device Service (AMDS).
- **Otimização de Executável (Desativação de UPX)**: Desativada a compressão UPX (`upx=False`) no arquivo de spec do PyInstaller ([`packaging/windows/ios_forensics.spec`](packaging/windows/ios_forensics.spec)), eliminando atrasos de descompressão na memória e falsos positivos/latência do Windows Defender.

---

### 🇺🇸 English (v1.2.0)

#### Added (v1.2.0)

- **Instant TUI Startup & Asynchronous Non-Blocking Workers (Textual)**:
  - Eliminated synchronous `collector.collect_all()` before `app.run()`, achieving instantaneous application launch (< 100 ms).
  - All heavy forensic I/O actions (`action_refresh_data`, `action_re_pair`, `action_export_package`, `action_capture_syslog`, `action_pull_crashes`) now execute in dedicated background worker threads via Textual's `@work(thread=True)`.
  - Concurrency safety with atomic lock (`threading.Lock` on `_busy`), preventing re-entrance and data corruption during forensic extractions.
  - Added `--no-auto-collect` CLI flag to launch the TUI without triggering an immediate background hardware scan.
- **Short-Circuit Optimization & Parallel Forensic Collection**:
  - Immediate short-circuit when no iOS device is connected (`connected_udids` is empty), avoiding cascading 5-8s timeouts across 10 lockdown domains and 12 IORegistry nodes.
  - Parallel forensic data collection (`collect_domains`, `collect_ioregistry`, `collect_diagnostics`) utilizing `ThreadPoolExecutor(max_workers=3)`.
  - Combined PowerShell PnP and Service queries into a single unified call on Windows.
- **UAC Auto-Elevation & Persistent Driver Installation Logs**:
  - Automatic administrative UAC self-elevation (`Start-Process powershell.exe -Verb RunAs`) in [`install_drivers.ps1`](packaging/windows/install_drivers.ps1) and Inno Setup Start Menu repair shortcuts.
  - Persistent transcript logging to `%ProgramData%\iOS_Forensics\logs\install_drivers_<timestamp>.log`.
  - Added `-InstallAppleSupport` flag to optionally deploy Apple Devices / iTunes via `winget`.
  - Strict return-code validation for `pnputil.exe` (0, 259, 3010) and forced hardware bus rescan (`/scan-devices`).
- **Expanded Test Suite (`tests/test_forensics.py`)**:
  - Added unit tests for version `1.2.0`, async TUI initialization, and no-device short-circuit optimization (16/16 tests passing).

#### Fixed & Improved (v1.2.0)

- **Resolved UI Freezing & Event Loop Starvation**: Completely resolved GUI unresponsive / freezing issues by removing blocking `subprocess.run()` calls from the main thread.
- **Removed Broken NT Service Creation (`usbmuxd`)**: Removed invalid `sc.exe create usbmuxd` (which caused Windows SCM Error 1053 and hung the installer for 30s). USB multiplexing on Windows is natively handled by Apple Mobile Device Service (AMDS).
- **PyInstaller Decompression Optimization (`upx=False`)**: Disabled UPX compression in [`packaging/windows/ios_forensics.spec`](packaging/windows/ios_forensics.spec), eliminating launch decompression latency and reducing Windows Defender real-time scanning overhead.

---

## [1.1.0] - 2026-10-27

### 🇧🇷 Português (v1.1.0)

#### Adicionado (v1.1.0)

- **Manifesto de Cadeia de Custódia (`manifest_sha256.txt`)**: Geração automática de hashes SHA-256 para todos os arquivos extraídos durante a exportação do pacote pericial (`export_full_forensic_package`), implementado na auditoria do `@jules` ([PR #3](https://github.com/RLuf/ios_fosensics/pull/3)).
- **Documentação Bilíngue Completa (PT-BR / EN) e Capturas de Tela TUI (`docs/assets/*.svg`)**:
  - Novo [`README.md`](README.md) bilíngue com prints reais das 6 abas da interface TUI.
  - Novos guias técnicos e de uso em [`./docs/`](docs/INDEX.md): [`INDEX.md`](docs/INDEX.md), [`USAGE_GUIDE.md`](docs/USAGE_GUIDE.md), [`FORENSIC_ARCHITECTURE.md`](docs/FORENSIC_ARCHITECTURE.md), [`WINDOWS_INSTALLER_AND_DRIVERS.md`](docs/WINDOWS_INSTALLER_AND_DRIVERS.md) e [`AI_CODE_REVIEW.md`](docs/AI_CODE_REVIEW.md).
- **Diretrizes de Agentes e Regra de Ouro**: Criados [`AGENTS.md`](AGENTS.md) e [`AGENTES.md`](AGENTES.md) documentando a Regra de Ouro de backup prévio em `archived/` e sincronização obrigatória de documentação.
- **Expansão da Suíte de Testes (`tests/test_forensics.py`)**: Cobertura ampliada de 5 para 13 testes unitários automatizados (incluindo mocks de extração AFC, SQLite `ZASSET`, Lockdown, `run_cmd` e geração de pacote forense).

#### Corrigido & Melhorado (v1.1.0)

- **Segurança SQLite (`collect_afc_forensics`)**: Escape seguro de identificadores de tabelas (`safe_t = t.replace('"', '""')`) e tratamento específico de `sqlite3.Error`.
- **Resiliência de Timestamps no Windows**: Proteção contra `OverflowError` e `OSError` ao converter `BootPathUpdated` e `TimeIntervalSince1970` no Windows (`msvcrt`), além de timestamps CoreData explícitos em UTC.
- **Tipagem e Tratamento de Exceções**: Modernização de type hints (`dict`, `list`, `ClassVar`, `bytes | None`) e substituição de `except Exception` genéricos por exceções específicas (`plistlib.InvalidFileException`, `UnicodeDecodeError`, `OSError`).

---

### 🇺🇸 English (v1.1.0)

#### Added (v1.1.0)

- **Forensic Chain-of-Custody Manifest (`manifest_sha256.txt`)**: Automatic SHA-256 hash manifest generation for all exported files in `export_full_forensic_package`, contributed via `@jules` audit ([PR #3](https://github.com/RLuf/ios_fosensics/pull/3)).
- **Full Bilingual Documentation (PT-BR / EN) & High-Resolution TUI Screenshots (`docs/assets/*.svg`)**:
  - Updated [`README.md`](README.md) with visual previews of all 6 forensic tabs.
  - Comprehensive technical documentation suite in [`./docs/`](docs/INDEX.md).
- **AI Agent Guidelines & Golden Rule**: Added [`AGENTS.md`](AGENTS.md) and [`AGENTES.md`](AGENTES.md) enforcing the `archived/` backup Golden Rule.
- **Expanded Unit Test Suite (`tests/test_forensics.py`)**: Increased from 5 to 13 unit tests covering AFC extraction, SQLite `ZASSET` parsing, Lockdown records, and package export.

#### Fixed & Changed (v1.1.0)

- **SQLite Identifier Escaping**: Properly escaped table names in `collect_afc_forensics` (`safe_t = t.replace('"', '""')`) and narrowed exception handling to `sqlite3.Error`.
- **Windows Timestamp Safety**: Guarded `fromtimestamp()` conversions against `OverflowError`/`OSError` on Windows and enforced explicit UTC timezone on CoreData timestamps.

---

## [1.0.0] - 2026-10-27

### 🇧🇷 Português / 🇺🇸 English (v1.0.0)

- **Lançamento Inicial (`v1.0.0`) / Initial Release**:
  - Suíte interativa TUI em Python (`Textual` + `Rich`) para perícia forense e diagnóstico USB em dispositivos iOS (`ios_forensics_tui.py`).
  - Adaptação multiplataforma completa para **Windows 10/11 (x64)**, **Linux** e **macOS**.
  - Pipeline automatizado no GitHub Actions ([`.github/workflows/windows-release.yml`](.github/workflows/windows-release.yml)) gerando executável `PyInstaller`, instalador `Inno Setup` (`iOS_Forensics_Setup_v1.0.0_x64.exe`), pacote portátil `.zip`, integração de binários `libimobiledevice`/`usbmuxd` Win64, scripts de instalação de drivers USB Apple (`pnputil`) e assinatura digital Authenticode SHA-256 (`signtool.exe`).
