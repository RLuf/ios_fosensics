# 🤖 GEMINI.md — Regras Globais e de Projeto (Antigravity / Gemini / Jules / Codex)

Siga rigorosamente esta ordem de execução em todas as tarefas de modificação de código, documentação e empacotamento:

1. **Passo 1 — REGRA DE OURO (`archived/`):**
   - Sempre crie a pasta `archived/` e adicione `archived/` ao `.gitignore`.
   - Antes de modificar, sobrescrever ou apagar qualquer arquivo, faça um backup (copie/mova a versão anterior) para `archived/<timestamp>_<arquivo>`.
2. **Passo 2 — Implementação e Testes:**
   - Aplique as alterações de código mantendo compatibilidade multiplataforma e valide com linter (`ruff`) e testes (`pytest`).
3. **Passo 3 — Sincronização de Documentação (Raiz e `./docs/`):**
   - Sempre crie, revise, corrija e atualize em conformidade com as modificações: `.gitignore`, `AGENTS.md`, `AGENTES.md`, `GEMINI.md`, `CHANGELOG.md` e `README.md` (bilíngue Português e Inglês, com prints/screenshots quando conveniente).
   - Em `./docs/`, revise e atualize toda a documentação técnica e de uso existente e crie o que faltar.
4. **Passo 4 — Bump de Versão em Nova Release / Workflow:**
   - Sempre que a entrega gerar nova Release ou acionar workflow de build/release (padrão em atualizações), faça o **bump de versão** em todos os manifestos (`pyproject.toml`, código-fonte, metadados de instalador, workflow e `CHANGELOG.md`) e confira a execução da Release no GitHub.
