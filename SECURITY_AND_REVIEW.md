# 🔍 Relatório de Auditoria & Conferência de Código (Jules, Codex & Gemini)

Este documento descreve a arquitetura de empacotamento, provisionamento de drivers e assinatura digital da suíte **iOS Forensics TUI (`ios_forensics`)** para conferência automatizada e humana.

## 1. Escopo da Revisão Técnica
- **Jules** (`@jules` / `@google-labs-jules`):
  - Verificar portabilidade Windows/Linux/macOS em `ios_forensics_tui.py` (`configure_runtime_environment`, `get_lockdown_dir`, `run_cmd` com `CREATE_NO_WINDOW`).
- **Codex** (`@codex`):
  - Verificar scripts PowerShell em `packaging/windows/` (`fetch_drivers_and_tools.ps1`, `install_drivers.ps1`, `sign_artifacts.ps1`) e manifesto Inno Setup (`installer.iss`).
- **Gemini** (`@gemini` / `@gemini-code-assist`):
  - Verificar integridade forense dos coletores (`IOSForensicCollector`), decodificação de NVRAM (`bplist00`/Base64), IORegistry, AFC/SQLite e metadados EXIF.

## 2. Verificação de Integridade da Release (`v1.0.0`)
Todos os artefatos Windows x64 são assinados com Authenticode SHA-256 (`signtool.exe` + carimbo de tempo RFC3161 DigiCert) e acompanhados de `SHA256SUMS.txt`.
