# 🤖 AGENTES.md — Diretrizes e Regras de Execução para Agentes de IA (PT-BR / EN)

> Espelho oficial em Português de [`AGENTS.md`](AGENTS.md) e [`GEMINI.md`](GEMINI.md). Todas as regras abaixo devem ser seguidas rigorosamente na ordem de execução definida.

---

## 📋 Ordem Obrigatória de Execução (Passo a Passo)

### Passo 1 — REGRA DE OURO: Backup Prévio em `archived/`
1. **Criação e Ignoramento da Pasta `archived/`:**
   - Antes de modificar, refatorar, sobrescrever ou apagar qualquer arquivo, crie a pasta `archived/` na raiz do projeto (caso ainda não exista) e certifique-se de que `archived/` esteja declarada no [`.gitignore`](.gitignore).
2. **Backup Antes de Qualquer Edição ou Exclusão:**
   - Copie ou mova o arquivo em questão para `archived/<YYYYMMDD_HHMMSS>_<nome_do_arquivo>` **antes** de aplicar qualquer modificação.

---

### Passo 2 — Implementação, Qualidade de Código e Segurança
1. **Multiplataforma e Resiliência:**
   - Manter compatibilidade total entre Windows 10/11 (x64), Linux e macOS.
2. **Validação Automatizada:**
   - Executar linter (`ruff check`) e suíte de testes unitários (`pytest -v`) garantindo zero erros.

---

### Passo 3 — Criação, Revisão e Atualização Completa da Documentação
Sempre crie, revise, corrija e atualize os arquivos de documentação em conformidade com as modificações realizadas:
1. **Na Raiz do Repositório:**
   - [`.gitignore`](.gitignore)
   - [`AGENTS.md`](AGENTS.md), [`AGENTES.md`](AGENTES.md) e [`GEMINI.md`](GEMINI.md)
   - [`CHANGELOG.md`](CHANGELOG.md) (Bilíngue PT-BR / EN)
   - [`README.md`](README.md): Página inicial bilíngue (**Português e Inglês**), com prints/capturas de tela atualizados (`docs/assets/`) quando conveniente, além de guias técnicos e de uso.
2. **Em [`./docs/`](docs/INDEX.md):**
   - Revisar, corrigir e atualizar toda a documentação existente e criar o que faltar (`INDEX.md`, `USAGE_GUIDE.md`, `FORENSIC_ARCHITECTURE.md`, `WINDOWS_INSTALLER_AND_DRIVERS.md`, `AI_CODE_REVIEW.md`).

---

### Passo 4 — Bump de Versão e Geração de Nova Release / Workflow
Sempre que a tarefa envolver geração de nova Release ou execução de workflow de empacotamento (fluxo padrão após correções e melhorias):
1. **Fazer o Bump de Versão (Version Bump):**
   - Atualizar a versão semântica (`X.Y.Z`) de forma consistente em [`pyproject.toml`](pyproject.toml), [`ios_forensics_tui.py`](ios_forensics_tui.py), [`packaging/windows/version_info.txt`](packaging/windows/version_info.txt), [`.github/workflows/windows-release.yml`](.github/workflows/windows-release.yml), [`CHANGELOG.md`](CHANGELOG.md) e [`README.md`](README.md).
2. **Conferência no GitHub:**
   - Verificar se o workflow do GitHub Actions concluiu com sucesso e se a nova Release foi publicada com todos os artefatos assinados e somas SHA-256.
