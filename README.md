# Local Coding Agent

A multi-provider multi-agent coding assistant: LangGraph + Ollama / OpenAI / OpenAI-compatible cloud APIs / Anthropic + MCP stdio.
Includes workspace file tools, conservative terminal execution, Git inspection/staging,
Milvus Lite + independently configurable local/cloud embeddings, and Planner/Coder/Reviewer/Tester workflow.

## Requirements

- Python 3.11+
- Git
- One chat provider: Ollama, OpenAI, an OpenAI-compatible cloud endpoint, or Anthropic
- One embedding provider: Ollama, OpenAI, or an OpenAI-compatible embedding endpoint

For the local default configuration:

```bash
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
ollama serve
```

Cloud providers require their API keys in `.env`; do not commit `.env` to Git.

## Install

```bash
git clone <your-repo>
cd coding-agent
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\\Scripts\\activate
pip install -e .
pip install -e ".[rag]"
cp .env.example .env
mkdir -p workspace data
```

RAG dependencies are installed by `pip install -e ".[rag]"`.

Milvus Lite uses a local database file (`MILVUS_URI=./data/milvus.db`); no separate Milvus server is needed.


## 多模型与云端模型配置

主模型和 Embedding 模型完全独立配置。修改 `.env` 后重启 `langgraph dev`，无需修改 Agent 代码。

### 主模型支持

| `LLM_PROVIDER` | 说明 | 关键配置 |
|---|---|---|
| `ollama` | 本地 Ollama | `LLM_MODEL`、`LLM_BASE_URL` |
| `openai` | OpenAI 官方 API | `LLM_MODEL`、`LLM_API_KEY` |
| `openai_compatible` | DeepSeek、阿里云百炼兼容模式、硅基流动、OpenRouter、vLLM、LM Studio 等 | `LLM_MODEL`、`LLM_BASE_URL`、`LLM_API_KEY` |
| `anthropic` | Claude API | `LLM_MODEL`、`LLM_API_KEY` |

示例：切换到 DeepSeek：

```dotenv
LLM_PROVIDER=openai_compatible
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=你的_DEEPSEEK_API_KEY
```

示例：切换到 OpenAI：

```dotenv
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=你的_OPENAI_API_KEY
```

示例：切换到 Claude：

```dotenv
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5
LLM_API_KEY=你的_ANTHROPIC_API_KEY
```

### Embedding 支持

| `EMBEDDING_PROVIDER` | 说明 | 关键配置 |
|---|---|---|
| `ollama` | 本地 Ollama Embeddings | `EMBEDDING_MODEL`、`EMBEDDING_BASE_URL` |
| `openai` | OpenAI Embeddings | `EMBEDDING_MODEL`、`EMBEDDING_API_KEY` |
| `openai_compatible` | 兼容 OpenAI Embeddings API 的云端服务或自建服务 | `EMBEDDING_MODEL`、`EMBEDDING_BASE_URL`、`EMBEDDING_API_KEY` |

例如，主模型使用 Claude，向量模型使用 OpenAI：

```dotenv
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5
LLM_API_KEY=你的_ANTHROPIC_API_KEY

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=你的_OPENAI_API_KEY
```

例如，主模型与 Embedding 都使用硅基流动兼容接口：

```dotenv
LLM_PROVIDER=openai_compatible
LLM_MODEL=Qwen/Qwen3-8B
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=你的_SILICONFLOW_API_KEY

EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=你的_SILICONFLOW_API_KEY
```

注意事项：

- 云端模型需要可用的 API Key、模型权限和网络访问；具体模型名称以服务商控制台为准。
- `openai_compatible` 要求服务商提供兼容 Chat Completions 或 Embeddings 的 API；并非所有云模型都兼容。
- Coder 依赖工具调用能力，主模型必须支持 tool/function calling。部分服务商的模型或套餐可能不支持，切换后应先运行 MCP 工具调用测试。
- 切换主模型或 Embedding 模型后重启 LangGraph Server，使配置生效。
- 旧配置 `OLLAMA_MODEL`、`OLLAMA_BASE_URL`、`OLLAMA_EMBEDDING_MODEL`、`OLLAMA_TEMPERATURE` 仍兼容；如果设置了新变量 `LLM_MODEL` / `EMBEDDING_MODEL`，新变量优先。
- 默认 Milvus collection 名称会根据 Embedding provider 和 model 自动生成（旧配置中的 `MILVUS_COLLECTION=code_chunks` 也会自动迁移为带模型标识的名称），例如 `code_chunks_openai_text_embedding_3_small`，防止不同向量维度写入同一 collection。若手动设置 `MILVUS_COLLECTION`，必须确保该 collection 中的向量与当前 Embedding 模型维度兼容。
- 不同 Embedding 模型之间不能直接混用旧向量。切换模型后应使用新 collection 重新执行 `index_code`；不要将旧 collection 指向新的向量模型。

## Start

CLI:

```bash
coding-agent
```

Optional legacy REST API for debugging (not the native AgentChatUI streaming endpoint):

```bash
coding-agent-api
# API: http://127.0.0.1:8000
```

Check:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"thread_id":"demo","message":"分析 workspace 项目并提出改进建议"}'
```

## MCP servers

`config/mcp_servers.json` starts four stdio MCP servers:
- filesystem: list/read/write/search files
- terminal: allowlisted single-command execution and pytest
- git: status/diff/log/stage
- knowledge: index and semantic search

MCP server stdout is reserved for protocol traffic. Use stderr for diagnostics.

## RAG workflow

1. Add source code under `workspace/`.
2. Ask the agent: `调用 index_code 建立代码索引`.
3. Ask questions; Coder can call `search_code`.

Supported file suffixes: `.py .js .ts .tsx .jsx .java .go .rs .md .txt`.
The sample chunking is character-based for clarity; use language-aware splitting for production.

## AgentChatUI 原生流式接入（推荐）

本项目提供 LangGraph Server 入口，AgentChatUI 可以直接连接 LangGraph API，不需要 OpenAI 兼容层或自定义 SSE 协议。图状态使用标准 `messages` 字段；模型调用产生的 `on_chat_model_stream` 事件会由 LangGraph Server 实时转发给 UI。Planner、Coder、Reviewer、Tester 的最终消息也会进入对话历史。

### 1. 安装 LangGraph 本地开发服务

`langgraph-cli[inmem]` 已加入项目依赖。升级安装：

```bash
source .venv/bin/activate
pip install -e .
```

### 2. 启动本地 Agent API Server

在项目根目录执行（确保 Ollama 已启动，`.env` 已配置）：

```bash
langgraph dev --host 127.0.0.1 --port 2024
```

启动后，LangGraph API 地址为 `http://127.0.0.1:2024`，图 ID 为 `coding_agent`。本项目通过 `langgraph.json` 将图注册为 `coding_agent`。服务端会管理会话线程和 checkpoint；MCP stdio 工具客户端在服务进程内复用。

### 3. 连接 AgentChatUI

可以使用官方托管 UI：<https://agentchat.vercel.app/>，或本地启动官方前端：

```bash
git clone https://github.com/langchain-ai/agent-chat-ui.git
cd agent-chat-ui
pnpm install
pnpm dev
```

在 UI 初始连接页填写：

- **Deployment URL**：`http://127.0.0.1:2024`
- **Assistant / Graph ID**：`coding_agent`
- **LangSmith API Key**：本地开发服务通常留空

如果使用托管 UI，浏览器必须能够访问运行 LangGraph Server 的机器地址；`127.0.0.1` 指的是浏览器所在机器。跨设备访问时，应将服务绑定到可访问的局域网地址，并配置防火墙与认证，不要直接暴露未认证的 Agent API。

### 4. 流式与审批行为

- Ollama ChatModel 显式启用 `streaming=True`，AgentChatUI 可逐 token 显示模型输出。
- AgentChatUI 从标准 `messages` 状态读取对话，并使用 LangGraph Server 的流式运行接口；无需自己拼接 SSE。
- Planner 生成计划后会触发人工审批中断。中断 payload 同时包含 AgentChatUI HITL 使用的 `action_requests` / `review_configs`，以及可读的计划摘要。
- 批准后继续 Coder → Reviewer → Tester；拒绝后结束本轮，不执行代码修改。
- 旧的 `coding-agent-api` / `POST /chat` 仍保留为简单 REST 调试入口，不提供 AgentChatUI 的原生 token streaming。对接 AgentChatUI 时请使用 `langgraph dev`。

## Human approval and safety

This starter includes a conservative terminal allowlist and blocks shell operators. AgentChatUI integration provides plan-level approval before the Coder Agent starts; it is not per-tool approval. Before using on valuable repositories:
- keep the workspace isolated and backed up;
- do not add `rm`, `sudo`, arbitrary shell, network tools or unrestricted command execution;
- consider adding separate `interrupt()` / resume gates around individual write, stage and terminal tools for stricter per-tool approval;
- bind API to localhost only unless authentication and authorization are added.

Git commit, reset, checkout, delete, and file overwrite confirmation are deliberately not exposed as autonomous tools.

## Troubleshooting

- `ImportError: attempted relative import with no known parent package` when starting `langgraph dev`: this project registers the graph by file path (`./src/coding_agent/graph.py:make_graph`). LangGraph may load that file as a top-level module, so imports such as `from .llm import ...` fail. The fixed version uses absolute package imports (`from coding_agent.llm import ...`). After updating, run `pip install -e .` again from the project root and restart `langgraph dev`.

- `model does not support tools`: update Ollama and choose a model build with tool-calling support.
- MCP server fails to start: run its command manually and inspect stderr; keep stdout clean.
- RAG tools unavailable: install `pip install -e ".[rag]"`; for Ollama embeddings, also pull the configured embedding model. For cloud embeddings, verify the API key, base URL, model permission and network access.
- `workspace` is relative to the project launch directory; run commands from the repository root.

## Coding Agent 提示词与执行行为优化

当前版本强化了 Planner / Coder / Reviewer / Tester 四个角色的职责：

- Planner 输出可执行步骤和验收标准，不再只给概念性建议。
- Coder 被明确要求先 `list_files` / `read_file`，再通过 `write_file` 修改真实工作区文件，并在完成后复读文件、运行测试；不能只在聊天中贴代码。
- Reviewer 获得 `list_files`、`read_file`、`search_files`、`git_diff` 只读工具，能够核对实际代码，而不是只根据 Coder 的自述审查。
- Tester 必须运行真实命令，报告命令、退出码和结果；环境问题与代码失败分开说明。

提示词位于 `src/coding_agent/graph.py` 的 `PLANNER_PROMPT`、`CODER_PROMPT`、`REVIEWER_PROMPT`、`TESTER_PROMPT`。可按项目技术栈继续调整验收命令。

**注意：** 提示词能显著改善 7B 模型的执行纪律，但不能保证模型每次都正确调用工具。若模型仍频繁只回复方案，建议换用工具调用能力更稳定的模型，或在工作流层增加“未产生文件修改/未运行验证则退回 Coder”的程序化检查与修复循环。
