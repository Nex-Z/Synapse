# Synapse

**Transform your traditional project's REST APIs into MCP Servers in seconds.**

[简体中文](README.md) | [English](README_en.md)

Synapse is a zero-intrusion API adapter that directly parses OpenAPI/Swagger documentation to dynamically generate service endpoints compliant with the Model Context Protocol (MCP). No business logic modification, no gateway migration—just one command to instantly empower AI agents with the ability to operate your existing business systems.

---

## 🚀 Why Synapse?

- **🤝 Broad Ecosystem Compatibility.** Seamlessly integrate as long as you have Swagger/OpenAPI documentation.

- **🔌 Say Goodbye to Manual Encapsulation.** Quickly assemble interfaces from your services into an immediately usable MCP Server.

- **🛡️ Zero-Intrusion Architecture.** No need to migrate gateways or modify existing business code. It acts as a "sidecar," so your architecture doesn't need a major overhaul for AI.

- **⚡️ Speed & Lightweight.** No complex external dependencies, and no need to deploy heavy gateway services.

## ✨ Key Features

*   **Dynamic Protocol Conversion:** Real-time transformation of OpenAPI schemas into MCP tool definitions, handling complex parameters and references automatically.
*   **Visual Management Console:** A modern, responsive dashboard (Vue 3 + Naive UI) to manage microservices, compose toolkits, and monitor system status.
*   **Logical Orchestration:**
    *   **Combinations:** Group specific endpoints from different services into logical units (e.g., "Customer Support Kit").
    *   **MCP Servers:** Package combinations into distinct MCP servers with unique prefixes (e.g., `http://.../mcp/finance`).
*   **Real-time Updates:** SSE-based notifications ensure connected AI clients receive tool updates instantly without polling or restarting.
*   **Robust Security:** RBAC with JWT authentication for management interfaces (`admin`/`user` roles), while keeping MCP protocol endpoints optimized for agent access.
*   **Flexible Persistence:** Ships with SQLite for zero-config setup, but easily scales to enterprise SQL databases via SQLAlchemy & Alembic.

## 🛠️ Tech Stack

*   **Backend:** Python 3.12+, FastAPI
*   **Frontend:** Vue 3, TypeScript, Vite, Naive UI
*   **Protocol:** Model Context Protocol (MCP) v1 (HTTP + SSE transport).

## Demo

<img src="docs/home.png" alt="Home">
<img src="docs/server_manager.png" alt="Service Management">
<img src="docs/mcp_combination.png" alt="MCP Combination">
<img src="docs/mcp_manager.png" alt="MCP Management">

## 🐳 Docker Quick Start

```bash
# Clone the project
git clone https://github.com/yourname/Synapse.git
cd Synapse

# One-click launch
docker compose up -d

# Visit http://localhost:8000
# Default credentials: admin / admin123
```

---

## ⚡ Quick Start

### Prerequisites
*   **Python 3.12+** (Recommended to use `uv` package manager)
*   **Node.js 20+** (Recommended to use `pnpm`)

### 1. Backend Setup
```bash
cd backend
uv sync

# Default Admin: admin / admin123
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
pnpm install
pnpm run dev
```
Access the dashboard at `http://localhost:5173`.

## 🔌 Client Integration

Connect your AI tools to Synapse's MCP Servers in seconds.

**Endpoint Format:** `http://ip:port/mcp/{server_prefix}`

### MCP Configuration

Add this to your MCP settings:

```json
{
  "mcpServers": {
    "name-prefix": {
      "type": "sse",
      "url": "http://ip:port/mcp/synapse"
    }
  }
}
```
*Note: Replace `synapse` in the URL with the specific prefix of the MCP Server you created in the Synapse dashboard.*

---

## 🗺️ Roadmap

- [x] OpenAPI 3.0 / Swagger 2.0 parsing support
- [x] Visual service orchestration
- [x] Orchestration as MCP Service
- [x] Multi-database persistence support
- [x] Docker one-click deployment image
- [ ] Support more authentication methods (OAuth2, API Key)
- [ ] Intelligent parameter parsing optimization

## ❓ FAQ

Q: How is this different from Nacos 3.X / Higress?
> A: Different positioning. Nacos/Higress are heavy infrastructure gateways designed for service governance and high-concurrency traffic. Synapse is a lightweight adapter designed to solve the problem of "how to quickly turn existing project APIs into AI Tools." Synapse can run locally without altering your existing infrastructure.
