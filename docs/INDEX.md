# 📚 Índice da Documentação / Documentation Index (`./docs/`)

**🇧🇷 Português** | **[🇺🇸 English](#-english--documentation-index)**

Bem-vindo à documentação técnica e operacional do **iOS Forensics & USB Debug TUI Suite (`ios_forensics`)**.

---

## 🇧🇷 Português — Mapa da Documentação

| Documento | Descrição | Público-Alvo |
| :--- | :--- | :--- |
| **[`README.md`](../README.md)** | Visão geral do projeto, capturas de tela (prints) da interface TUI, início rápido e links das Releases | Todos os usuários |
| **[`docs/USAGE_GUIDE.md`](USAGE_GUIDE.md)** | Guia completo de operação da TUI, atalhos de teclado, modo `--cli-export` e estrutura do pacote pericial | Peritos Forenses / Analistas |
| **[`docs/FORENSIC_ARCHITECTURE.md`](FORENSIC_ARCHITECTURE.md)** | Arquitetura técnica das 6 camadas forenses (USB/usbmuxd, Lockdown, IORegistry, NVRAM/FMI, Bateria/GasGauge, AFC/SQLite/EXIF e `manifest_sha256.txt`) | Engenheiros / Peritos |
| **[`docs/WINDOWS_INSTALLER_AND_DRIVERS.md`](WINDOWS_INSTALLER_AND_DRIVERS.md)** | Documentação do empacotamento Windows (`PyInstaller` + `Inno Setup`), drivers USB Apple (`pnputil`), `usbmuxd` e assinatura Authenticode (`signtool.exe`) | DevSecOps / Administradores Windows |
| **[`docs/AI_CODE_REVIEW.md`](AI_CODE_REVIEW.md)** | Relatório da auditoria automatizada multi-agente (`@jules`, `@codex`, `@gemini-code-assist`) e melhorias implementadas na PR #3 | Desenvolvedores / Auditores |
| **[`AGENTS.md`](../AGENTS.md) / [`AGENTES.md`](../AGENTES.md)** | Regra de Ouro (`archived/`) e diretrizes obrigatórias para agentes de IA e contribuidores | Agentes de IA / Mantenedores |
| **[`CHANGELOG.md`](../CHANGELOG.md)** | Histórico detalhado de versões (`v1.0.0` → `v1.1.0`) em Português e Inglês | Todos os usuários |

---

## 🇺🇸 English — Documentation Index

| Document | Description | Target Audience |
| :--- | :--- | :--- |
| **[`README.md`](../README.md)** | Project homepage, high-resolution TUI screenshots, quick start, and Windows Release links | All users |
| **[`docs/USAGE_GUIDE.md`](USAGE_GUIDE.md)** | Complete TUI user manual, keyboard bindings, `--cli-export` mode, and forensic export package structure | Forensic Analysts / Operators |
| **[`docs/FORENSIC_ARCHITECTURE.md`](FORENSIC_ARCHITECTURE.md)** | Deep-dive into the 6 forensic extraction layers (USB/usbmuxd, Lockdown, IORegistry, NVRAM/FMI, SmartBattery, AFC/SQLite/EXIF, and `manifest_sha256.txt`) | Security Engineers / Examiners |
| **[`docs/WINDOWS_INSTALLER_AND_DRIVERS.md`](WINDOWS_INSTALLER_AND_DRIVERS.md)** | Windows packaging architecture (`PyInstaller` + `Inno Setup`), Apple USB driver provisioning (`pnputil`), `usbmuxd` service, and Authenticode SHA-256 signing | DevSecOps / Windows Admins |
| **[`docs/AI_CODE_REVIEW.md`](AI_CODE_REVIEW.md)** | Multi-agent code review report (`@jules`, `@codex`, `@gemini-code-assist`) and PR #3 enhancements | Developers / Auditors |
| **[`AGENTS.md`](../AGENTS.md) / [`AGENTES.md`](../AGENTES.md)** | Golden Rule (`archived/` backup before modification) and AI agent guidelines | AI Agents / Maintainers |
| **[`CHANGELOG.md`](../CHANGELOG.md)** | Bilingual release history (`v1.0.0` → `v1.1.0`) | All users |
