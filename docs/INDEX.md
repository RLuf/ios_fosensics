# 📚 Índice da Documentação / Documentation Index (`./docs/`)

**🇧🇷 Português** | **[🇺🇸 English](#-english--documentation-index)**

Bem-vindo à documentação técnica e operacional do **iOS Forensics & USB Debug TUI Suite (`ios_forensics`)**.

---

## 🇧🇷 Português — Mapa da Documentação

| Documento | Descrição | Público-Alvo |
| :--- | :--- | :--- |
| **[`README.md`](../README.md)** | Visão geral do projeto, capturas de tela (prints) da interface TUI, início rápido e links das Releases | Todos os usuários |
| **[`docs/USAGE_GUIDE.md`](USAGE_GUIDE.md)** | Guia completo de operação da TUI, inicialização assíncrona instantânea, `--no-auto-collect`, atalhos e estrutura do pacote pericial | Peritos Forenses / Analistas |
| **[`docs/FORENSIC_ARCHITECTURE.md`](FORENSIC_ARCHITECTURE.md)** | Arquitetura técnica das 6 camadas forenses, modelo de concorrência com workers em thread (`@work(thread=True)`), paralelismo e `manifest_sha256.txt` | Engenheiros / Peritos |
| **[`docs/WINDOWS_INSTALLER_AND_DRIVERS.md`](WINDOWS_INSTALLER_AND_DRIVERS.md)** | Documentação do empacotamento Windows (`PyInstaller` sem UPX + `Inno Setup`), auto-elevação UAC, logs de drivers em `%ProgramData%` e AMDS | DevSecOps / Administradores Windows |
| **[`docs/AI_CODE_REVIEW.md`](AI_CODE_REVIEW.md)** | Relatório da auditoria automatizada multi-agente (`@jules`, `@codex`, `@gemini-code-assist`), diagnóstico de travamentos e correções da v1.2.0 | Desenvolvedores / Auditores |
| **[`AGENTS.md`](../AGENTS.md) / [`AGENTES.md`](../AGENTES.md)** | Regra de Ouro (`archived/`) e diretrizes obrigatórias para agentes de IA e contribuidores | Agentes de IA / Mantenedores |
| **[`CHANGELOG.md`](../CHANGELOG.md)** | Histórico detalhado de versões (`v1.0.0` → `v1.1.0` → `v1.2.0`) em Português e Inglês | Todos os usuários |

---

## 🇺🇸 English — Documentation Index

| Document | Description | Target Audience |
| :--- | :--- | :--- |
| **[`README.md`](../README.md)** | Project homepage, high-resolution TUI screenshots, quick start, and Windows Release links | All users |
| **[`docs/USAGE_GUIDE.md`](USAGE_GUIDE.md)** | Complete TUI user manual, instant async startup, `--no-auto-collect`, keyboard bindings, and export structure | Forensic Analysts / Operators |
| **[`docs/FORENSIC_ARCHITECTURE.md`](FORENSIC_ARCHITECTURE.md)** | Deep-dive into 6 forensic layers, async thread worker concurrency model (`@work(thread=True)`), short-circuiting, and `manifest_sha256.txt` | Security Engineers / Examiners |
| **[`docs/WINDOWS_INSTALLER_AND_DRIVERS.md`](WINDOWS_INSTALLER_AND_DRIVERS.md)** | Windows packaging architecture (`PyInstaller` without UPX + `Inno Setup`), UAC driver self-elevation, `%ProgramData%` logs, and AMDS service | DevSecOps / Windows Admins |
| **[`docs/AI_CODE_REVIEW.md`](AI_CODE_REVIEW.md)** | Multi-agent code review report (`@jules`, `@codex`, `@gemini-code-assist`), lag/freeze RCA, and v1.2.0 fixes | Developers / Auditors |
| **[`AGENTS.md`](../AGENTS.md) / [`AGENTES.md`](../AGENTES.md)** | Golden Rule (`archived/` backup before modification) and AI agent guidelines | AI Agents / Maintainers |
| **[`CHANGELOG.md`](../CHANGELOG.md)** | Bilingual release history (`v1.0.0` → `v1.1.0` → `v1.2.0`) | All users |
