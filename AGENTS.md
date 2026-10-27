# 🤖 AGENTS.md — Diretrizes e Regras de Execução para Agentes de IA (PT-BR / EN)

> Este arquivo está sincronizado com [`AGENTES.md`](AGENTES.md) e [`GEMINI.md`](GEMINI.md). Todas as regras abaixo devem ser aplicadas rigorosamente na ordem definida.

---

## 📋 Ordem Obrigatória de Execução (Step-by-Step)

### Passo 1 — REGRA DE OURO: Backup Prévio em `archived/`
1. **Criação e Ignoramento da Pasta `archived/`:**
   - Antes de modificar, refatorar, sobrescrever ou apagar qualquer arquivo do projeto, garanta que a pasta `archived/` exista na raiz do repositório e que a entrada `archived/` esteja presente no [`.gitignore`](.gitignore).
2. **Backup Obrigatório Antes de Qualquer Alteração:**
   - Faça sempre uma cópia (ou mova o arquivo original) para `archived/<YYYYMMDD_HHMMSS>_<nome_do_arquivo>` **antes** de realizar a edição ou exclusão.
   - O diretório `archived/` nunca deve ser comitado no Git.

---

### Passo 2 — Implementação, Qualidade de Código e Segurança Forense
1. **Compatibilidade Multiplataforma (Windows x64, Linux, macOS):**
   - Utilize `run_cmd()` com `CREATE_NO_WINDOW` no Windows e trate explicitamente `subprocess.TimeoutExpired` e `(OSError, ValueError)`.
2. **Integridade e Cadeia de Custódia Forense:**
   - Escape identificadores SQLite (`safe_t = t.replace('"', '""')`) e mantenha a geração automática do manifesto `manifest_sha256.txt` em todas as exportações periciais.
3. **Validação Local com Linter e Testes:**
   - Execute `python -m ruff check ios_forensics_tui.py tests/` e `python -m pytest -v` antes de comitar.

---

### Passo 3 — Criação, Revisão e Atualização Completa da Documentação
Sempre crie, revise, corrija e atualize todos os arquivos de documentação em conformidade com as modificações realizadas no projeto:
1. **Arquivos na Raiz do Repositório:**
   - [`.gitignore`](.gitignore)
   - [`AGENTS.md`](AGENTS.md), [`AGENTES.md`](AGENTES.md) e [`GEMINI.md`](GEMINI.md)
   - [`CHANGELOG.md`](CHANGELOG.md) (Bilíngue PT-BR / EN)
   - [`README.md`](README.md): Página inicial bilíngue (**Português e Inglês**), atualizada com capturas de tela (prints em `docs/assets/`) sempre que conveniente, além de instruções técnicas e de uso.
2. **Documentação Técnica e de Uso em [`./docs/`](docs/INDEX.md):**
   - Revise, corrija e atualize toda a documentação existente em `./docs/` e crie os documentos que faltarem:
     - [`docs/INDEX.md`](docs/INDEX.md)
     - [`docs/USAGE_GUIDE.md`](docs/USAGE_GUIDE.md)
     - [`docs/FORENSIC_ARCHITECTURE.md`](docs/FORENSIC_ARCHITECTURE.md)
     - [`docs/WINDOWS_INSTALLER_AND_DRIVERS.md`](docs/WINDOWS_INSTALLER_AND_DRIVERS.md)
     - [`docs/AI_CODE_REVIEW.md`](docs/AI_CODE_REVIEW.md)

---

### Passo 4 — Bump de Versão e Geração de Nova Release / Workflow
Sempre que a alteração envolver empacotamento, atualização de workflow CI/CD ou geração de uma nova Release (o que é o fluxo padrão após melhorias ou merges):
1. **Realize o Bump de Versão (Version Bump) Sincronizado:**
   - Incrementar a versão semântica (`MAJOR.MINOR.PATCH`) em:
     - [`pyproject.toml`](pyproject.toml) (`version = "X.Y.Z"`)
     - [`ios_forensics_tui.py`](ios_forensics_tui.py) (`--version`)
     - [`packaging/windows/version_info.txt`](packaging/windows/version_info.txt) (`filevers` / `prodvers` / `FileVersion` / `ProductVersion`)
     - [`.github/workflows/windows-release.yml`](.github/workflows/windows-release.yml) (`release_version` default)
     - [`CHANGELOG.md`](CHANGELOG.md) e [`README.md`](README.md)
2. **Verificação da Release e Conferência Multi-Agente:**
   - Acompanhe a execução do GitHub Actions até o fim (`gh run watch`), valide os artefatos publicados na Release (`.exe`, `.zip`, `.cer`, `SHA256SUMS.txt`) e cite `@jules` (`@google-labs-jules`), `@codex` e `@gemini-code-assist` para conferência quando aplicável.
