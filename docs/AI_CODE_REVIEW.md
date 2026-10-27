# 🤖 Auditoria e Conferência de Código por IA / AI Code Review Report (`@jules`, `@codex`, `@gemini`)

**🇧🇷 Português** | **[🇺🇸 English](#-english--ai-code-review--audit-report)**

---

## 🇧🇷 Português — Relatório da Conferência Multi-Agente

O repositório utiliza o workflow [`.github/workflows/ai-code-review.yml`](../.github/workflows/ai-code-review.yml) e issues/PRs dedicadas ([Issue #1](https://github.com/RLuf/ios_fosensics/issues/1), [PR #3](https://github.com/RLuf/ios_fosensics/pull/3)) para acionar a conferência técnica por três agentes:

- **Jules** (`@jules` / `@google-labs-jules`)
- **Codex** (`@codex`)
- **Gemini** (`@gemini` / `@gemini-code-assist`)

### O que o Jules (`@google-labs-jules`) auditou e implementou na PR #3

1. **Cadeia de Custódia SHA-256 (`manifest_sha256.txt`)**:
   - Na função `export_full_forensic_package()`, adicionou a geração automática do arquivo `manifest_sha256.txt` contendo o hash SHA-256 de cada evidência exportada (`forensic_report.json`, fotos DCIM, bancos SQLite e plists de pareamento).
2. **Escape Seguro de Identificadores SQLite**:
   - Na função `collect_afc_forensics()`, adicionou sanitização de identificadores de tabelas (`safe_t = t.replace('"', '""')`) antes de `SELECT COUNT(*) FROM "{safe_t}";` e substituiu `except Exception:` por `except sqlite3.Error:`.
3. **Proteção de Timestamps no Windows e UTC Explícito**:
   - Adicionou tratamento contra `(ValueError, OSError, OverflowError)` na conversão do `BootPathUpdated` da bateria e `TimeIntervalSince1970`, prevenindo falhas do `fromtimestamp()` na CRT do Windows (`msvcrt`).
   - Atualizou o cálculo de datas CoreData (`ZASSET`) para usar `datetime.UTC` explicitamente.
4. **Modernização de Tipagem e Limpeza Estática (`ruff`)**:
   - Atualizou anotações de tipos para `dict`, `list`, `tuple`, `ClassVar[list[Binding]]` e `bytes | None`.
   - Removeu chamada duplicada a `lsusb -d 05ac:` e imports ociosos.
5. **Ampliação de Testes Unitários (`tests/test_forensics.py`)**:
   - Expandiu a suíte de 5 para **13 testes unitários**, cobrindo `run_cmd` (sucesso, timeout e erro), pareamento Lockdown, extração AFC/SQLite com banco real em diretório temporário e verificação do `manifest_sha256.txt`.

---

### Auditoria e Correções da Versão 1.2.0 (Diagnóstico de Atraso, Travamento e Drivers)

Em resposta aos problemas reportados na execução do `.exe` e na instalação de drivers, uma nova auditoria conjunta multi-agente (`@jules`, `@codex`, `@gemini-code-assist`) identificou as seguintes causas raízes e implementou as correções definitivas:

#### 1. Causa Raiz do Atraso na Abertura e Congelamento da TUI

- **Problema 1 (Startup Delay):** O `main()` executava `collector.collect_all(deep_afc=True)` de forma puramente síncrona antes de instanciar o app Textual. Quando nenhum aparelho estava conectado ou o `usbmuxd` demorava a responder, o coletor insistia em consultar 10 domínios do lockdown e 12 nós do IORegistry com timeouts encadeados de 5 a 8 segundos cada. O usuário ficava esperando de 30 a mais de 180 segundos antes que qualquer janela aparecesse.
- **Problema 2 (UI Freezing / Event Loop Starvation):** Ações de interface (`action_refresh_data`, `action_re_pair`, `action_capture_syslog`, `action_pull_crashes`) executavam comandos bloqueantes `subprocess.run()` diretamente na thread do loop de eventos assíncrono do Textual. Isso travava o redesenho de tela e o processamento de cliques/teclado, levando o Windows a declarar a janela como "Não Respondendo".
- **Solução Implementada:**
  - A inicialização no `main()` não executa mais chamadas de rede ou I/O antes do `app.run()`, permitindo renderização imediata (< 100 ms).
  - Todas as rotinas de I/O de dispositivo foram convertidas em workers de segundo plano com o decorador `@work(thread=True)` e lock de concorrência (`threading.Lock` em `_busy`).
  - Adicionado short-circuit em `collect_all()` quando nenhum dispositivo está conectado (`connected_udids` vazio).
  - Paralelismo pericial com `ThreadPoolExecutor(max_workers=3)`.
  - Adicionada flag CLI `--no-auto-collect`.

#### 2. Causa Raiz das Falhas no Instalador e Drivers

- **Problema 1 (Falta de Elevação UAC):** O instalador e o atalho de reparo chamavam `install_drivers.ps1` sem auto-verificação de permissões administrativas. Se executado sem "Executar como Administrador", os comandos `Import-Certificate`, `pnputil` e manipulação de serviços falhavam silenciosamente com *Acesso Negado*.
- **Problema 2 (Travamento de 30s por Serviço Inválido):** O script executava `sc.exe create usbmuxd binPath= ...`. O binário `usbmuxd.exe` da libimobiledevice é um executável de console comum, sem interface com o Windows Service Control Manager (SCM). O Windows aguardava 30 segundos pelo handshake do serviço e matava o processo com o **Erro 1053**, congelando o instalador por meio minuto. No Windows, o serviço correto de multiplexação é o Apple Mobile Device Service (AMDS).
- **Solução Implementada:**
  - Auto-elevação UAC com `Start-Process powershell.exe -Verb RunAs` e checagem `Test-IsAdmin`.
  - Transcript persistente em `%ProgramData%\iOS_Forensics\logs\install_drivers_<timestamp>.log`.
  - Remoção de criação inválida de serviço NT e exclusão de serviços legados quebrados.
  - Validação de códigos de retorno do `pnputil` e rescaneamento com `/scan-devices`.
  - Suporte ao parâmetro `-InstallAppleSupport` via `winget`.

#### 3. Desativação de UPX no PyInstaller

- A flag `upx=True` causava descompressão lenta da imagem na inicialização e disparava alertas heurísticos no Microsoft Defender. Alterado para `upx=False` em [`packaging/windows/ios_forensics.spec`](../packaging/windows/ios_forensics.spec).

---

## 🇺🇸 English — AI Code Review & Audit Report

### Version 1.1.0 Review (PR #3)

Through [Issue #1](https://github.com/RLuf/ios_fosensics/issues/1) and [PR #3](https://github.com/RLuf/ios_fosensics/pull/3), **Jules** (`@google-labs-jules`), alongside the **Codex** (`@codex`) and **Gemini** (`@gemini-code-assist`) review workflows, audited the codebase and delivered key production improvements:

| Area | Finding | Fix Implemented in PR #3 |
| :--- | :--- | :--- |
| **Forensic Integrity** | Exported folders lacked an internal hash manifest | Added automatic `manifest_sha256.txt` generation in `export_full_forensic_package()` |
| **SQLite Parsing** | Table names in `SELECT COUNT(*)` were unescaped | Added double-quote escaping (`safe_t = t.replace('"', '""')`) and `sqlite3.Error` handling |
| **Windows CRT Safety** | `datetime.fromtimestamp()` on invalid epochs raises `OSError`/`OverflowError` on Windows | Added explicit `(ValueError, OSError, OverflowError)` guards and `datetime.UTC` timezone |
| **Type Annotations & Linting** | Legacy `typing.Dict`/`List` and broad `except Exception:` blocks | Modernized to PEP 585/604 types and specific exception classes |
| **Test Coverage** | 5 basic unit tests | Expanded to **13 unit tests** in [`tests/test_forensics.py`](../tests/test_forensics.py) |

---

### Version 1.2.0 Review (Driver Elevation & TUI Lag/Freezing RCA)

Following issues with slow UI launch, frozen screens, and driver installation errors, a multi-agent investigation identified the following root causes:

| Problem | Root Cause | Solution Implemented in v1.2.0 |
| :--- | :--- | :--- |
| **Slow Startup (30s–3min)** | `main()` executed blocking `collect_all()` before `app.run()`. Empty device lists incurred 20+ timeouts across domains and IORegistry nodes. | Startup is now instant (<100ms) with no pre-flight blocking I/O; short-circuit optimization returns immediately when no device is detected. |
| **UI Lag & "Not Responding"** | Button handlers executed blocking `subprocess.run()` calls on Textual's main event loop thread. | Converted all I/O actions to background thread workers (`@work(thread=True)`) with atomic locks (`threading.Lock` on `_busy`). |
| **Silent Driver Setup Failure** | Setup and repair shortcuts ran without administrative privilege verification. | Added mandatory UAC auto-elevation check (`Test-IsAdmin`) and self-elevation via `Start-Process powershell.exe -Verb RunAs`. |
| **Installer 30s Hang (Error 1053)** | `sc.exe create usbmuxd` registered a console binary as an NT service. Windows SCM timed out waiting for service handshake. | Removed invalid NT service creation in favor of native Apple Mobile Device Service (AMDS) and added cleanup of legacy broken services. |
| **Executable Decompression Lag** | UPX binary packing caused runtime decompression latency and aggressive Windows Defender heuristic scans. | Set `upx=False` in `ios_forensics.spec`. |
| **Unit Test Coverage** | Needed tests for async initialization, version bump, and short-circuit. | Added 3 tests in `tests/test_forensics.py`, totaling **16 tests passing (100%)**. |
