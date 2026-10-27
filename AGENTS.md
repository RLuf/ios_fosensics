# 🤖 AGENTS.md — Diretrizes e Regras para Agentes de IA (AI Agents Guidelines)

> **Nota:** Este arquivo está sincronizado com [`AGENTES.md`](AGENTES.md) (Português / English). Qualquer alteração nas regras de engenharia deve ser refletida em ambos.

---

## 🏆 1. REGRA DE OURO (GOLDEN RULE) — Preservação e Backup em `archived/`

1. **Nunca modifique ou apague um arquivo diretamente sem backup prévio:**
   - Antes de modificar, sobrescrever, refatorar ou remover qualquer arquivo existente no repositório, **SEMPRE** crie a pasta `archived/` (caso ainda não exista), garanta que `archived/` esteja listada no [`.gitignore`](.gitignore) e **copie/mova a versão anterior do arquivo para `archived/<YYYYMMDD_HHMMSS>_<nome_do_arquivo>`**.
2. **`archived/` no `.gitignore`:**
   - O diretório `archived/` é estritamente local para segurança operacional e rollback imediato, jamais devendo ser comitado no histórico público do Git.

---

## 📚 2. Sincronização Obrigatória de Documentação e Arquivos Base

Sempre que qualquer modificação de código, empacotamento, workflow ou arquitetura for realizada, o agente **DEVE** criar, revisar e atualizar em conformidade:

- [`.gitignore`](.gitignore) — Garantindo que `archived/`, artefatos temporários (`build/`, `dist/`, `forensics_iphone_*/`) e chaves privadas (`*.pfx`, `*.p12`, `*.key`) estejam ignorados.
- [`AGENTS.md`](AGENTS.md) & [`AGENTES.md`](AGENTES.md) — Diretrizes operacionais para agentes de IA (`@jules`, `@codex`, `@gemini-code-assist`, Antigravity, Claude Code).
- [`CHANGELOG.md`](CHANGELOG.md) — Registro cronológico bilíngue (PT-BR / EN) de todas as versões, correções de auditoria e melhorias.
- [`README.md`](README.md) — Página inicial do repositório bilíngue (**Português & English**), contendo capturas de tela (prints em `docs/assets/`), guia rápido de uso, arquitetura e links para a documentação técnica.
- **Documentação Técnica e de Uso em [`./docs/`](docs/INDEX.md)**:
  - [`docs/INDEX.md`](docs/INDEX.md) — Índice geral da documentação (PT-BR & EN).
  - [`docs/USAGE_GUIDE.md`](docs/USAGE_GUIDE.md) — Manual completo de uso da interface TUI e linha de comando (`--cli-export`).
  - [`docs/FORENSIC_ARCHITECTURE.md`](docs/FORENSIC_ARCHITECTURE.md) — Arquitetura das 6 camadas forenses (USB/usbmuxd, Lockdown, IORegistry, NVRAM/FMI, SmartBattery/GasGauge, AFC/SQLite/EXIF e manifesto SHA-256).
  - [`docs/WINDOWS_INSTALLER_AND_DRIVERS.md`](docs/WINDOWS_INSTALLER_AND_DRIVERS.md) — Guia técnico do instalador Windows (`Inno Setup` + `PyInstaller`), provisionamento de drivers USB Apple (`pnputil`) e assinatura Authenticode (`signtool.exe`).
  - [`docs/AI_CODE_REVIEW.md`](docs/AI_CODE_REVIEW.md) — Histórico e fluxo de revisão multi-agente (`@jules`, `@codex`, `@gemini-code-assist`).

---

## 🔬 3. Padrões de Código, Segurança Forense e Qualidade (CI/CD)

1. **Compatibilidade Multiplataforma (Windows x64, Linux, macOS):**
   - Todas as chamadas externas devem passar por `run_cmd()` em [`ios_forensics_tui.py`](ios_forensics_tui.py), utilizando `CREATE_NO_WINDOW` no Windows e tratando `subprocess.TimeoutExpired` e `(OSError, ValueError)` de forma segura.
2. **Cadeia de Custódia Forense (`manifest_sha256.txt`):**
   - Toda exportação pericial gerada por `export_full_forensic_package()` deve produzir o arquivo `manifest_sha256.txt` contendo o hash SHA-256 de todos os artefatos coletados (`forensic_report.json`, fotos DCIM, bancos SQLite e plists Lockdown).
3. **Segurança em Consultas SQLite:**
   - Ao inspecionar bancos SQLite extraídos do iOS via AFC, sempre escape identificadores de tabelas (`safe_t = t.replace('"', '""')`) e trate `sqlite3.Error` explicitamente.
4. **Linter e Testes Automatizados:**
   - Antes de qualquer commit/push, execute:
     ```bash
     python -m ruff check ios_forensics_tui.py tests/
     python -m pytest -v
     ```
5. **Revisão Multi-Agente no GitHub:**
   - Em Pull Requests e Releases relevantes, cite `@jules` (`@google-labs-jules`), `@codex` (`@codex review`) e `@gemini` (`@gemini-code-assist` / `/gemini review`) e aplique as labels `jules` e `ai-review`.
