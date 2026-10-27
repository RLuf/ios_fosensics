# 🤖 AGENTES.md — Diretrizes e Regras de Execução para Agentes de IA (PT-BR / EN)

> Espelho oficial em Português de [`AGENTS.md`](AGENTS.md) e [`GEMINI.md`](GEMINI.md). Todas as regras abaixo devem ser seguidas rigorosamente na ordem de execução definida.

---

## 📋 Ordem Obrigatória de Execução (Passo a Passo)

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
2. **Interface TUI Não-Bloqueante (Textual Async Workers):**
   - A inicialização da aplicação TUI (`main()`) nunca deve executar chamadas síncronas de I/O de dispositivo antes do `app.run()`.
   - Toda coleta, diagnóstico, pareamento ou download deve rodar em workers de thread em segundo plano (`@work(thread=True)`) com proteção de lock (`threading.Lock`), mantendo a interface 100% responsiva (sem congelamento ou lag).
   - Quando nenhum dispositivo estiver conectado (`idevice_id -l` vazio), execute short-circuit para evitar dezenas de timeouts encadeados.
3. **Provisionamento e Elevação de Drivers no Windows:**
   - Scripts de instalação/reparo de drivers (`install_drivers.ps1`) devem conter auto-elevação administrativa obrigatória (`Start-Process powershell.exe -Verb RunAs`), gravação de log persistente em `%ProgramData%\iOS_Forensics\logs\` e evitar criar serviços NT incompatíveis via `sc.exe`.
4. **Integridade e Cadeia de Custódia Forense:**
   - Escape identificadores SQLite (`safe_t = t.replace('"', '""')`) e mantenha a geração automática do manifesto `manifest_sha256.txt` em todas as exportações periciais.
5. **Validação Local com Linter e Testes:**
   - Execute `ruff check ios_forensics_tui.py tests/` e `pytest -v` antes de comitar.

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
