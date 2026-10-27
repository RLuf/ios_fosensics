# 🤖 AGENTES.md — Diretrizes e Regras de Ouro do Projeto (PT-BR / EN)

> Este documento é o espelho oficial em Português de [`AGENTS.md`](AGENTS.md). Todas as ferramentas e agentes autônomos (`@jules`, `@codex`, `@gemini-code-assist`, Antigravity, Cursor, Claude Code) que operam neste repositório devem seguir estritamente as regras abaixo.

---

## 🏆 1. REGRA DE OURO — Backup Obrigatório em `archived/`

1. **Backup antes de qualquer modificação ou exclusão:**
   - Sempre crie a pasta `archived/` na raiz do projeto e certifique-se de que `archived/` está declarada no [`.gitignore`](.gitignore).
   - **Antes de editar, sobrescrever ou apagar qualquer arquivo**, faça uma cópia ou mova o arquivo original para `archived/<timestamp>_<nome_arquivo>`.
2. **Isolamento do Git:**
   - A pasta `archived/` nunca deve ser enviada ao controle de versão remoto, servindo como cofre local de recuperação imediata.

---

## 📝 2. Manutenção Contínua de Documentação

Qualquer evolução no código-fonte ([`ios_forensics_tui.py`](ios_forensics_tui.py)), nos scripts de empacotamento Windows ([`packaging/windows/`](packaging/windows/)) ou nos workflows ([`.github/workflows/`](.github/workflows/)) exige a revisão e atualização simultânea de:

1. [`.gitignore`](.gitignore)
2. [`AGENTS.md`](AGENTS.md) e [`AGENTES.md`](AGENTES.md)
3. [`CHANGELOG.md`](CHANGELOG.md)
4. [`README.md`](README.md) (Bilíngue PT-BR / EN, com prints atualizados da TUI em `docs/assets/`)
5. Toda a árvore [`./docs/`](docs/INDEX.md):
   - [`docs/INDEX.md`](docs/INDEX.md)
   - [`docs/USAGE_GUIDE.md`](docs/USAGE_GUIDE.md)
   - [`docs/FORENSIC_ARCHITECTURE.md`](docs/FORENSIC_ARCHITECTURE.md)
   - [`docs/WINDOWS_INSTALLER_AND_DRIVERS.md`](docs/WINDOWS_INSTALLER_AND_DRIVERS.md)
   - [`docs/AI_CODE_REVIEW.md`](docs/AI_CODE_REVIEW.md)

---

## 🛡️ 3. Checklist de Qualidade e Auditoria Forense

- **Zero Erros no Ruff & Pytest**: `python -m ruff check ios_forensics_tui.py tests/` e `python -m pytest -v` devem passar com 100% de êxito no Linux e no Windows.
- **Integridade Probatória**: Verificar que `manifest_sha256.txt` (na exportação de perícia) e `SHA256SUMS.txt` (na Release do GitHub) são gerados corretamente.
- **Conferência por IA**: Citar `@jules`, `@codex` e `@gemini-code-assist` nas revisões de código.
