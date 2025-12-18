# SQLRAG / Project Management AI Assistant

A LangGraph-powered FastAPI service and Next.js frontend that delivers a chat-based project management assistant. The agent can read project/task/team data, propose writes that require explicit approval, and orchestrate multi-step workflows with durable state and auditability.

## Repository layout
- `backend/` — FastAPI service, LangGraph agent, tools, database layer, and eval harness.  
- `frontend/` — Next.js UI shell for login and future chat surface.  
- `docs/` — Product/design documentation (`design_document.md`, `architecture_diagram.md`, `loom_script.md`).  
- `data/` — Placeholder for datasets or seeded content.  
- `docker-compose.yml` — Spins up API + DB + frontend for local dev.  
- `Dockerfile` — Backend container image.  
- `Makefile` — Common tasks (setup, run, tests).  
- `sqlrag.db` — SQLite database (created in dev) used by default configuration.

## Backend (FastAPI + LangGraph)
### Application entrypoint
- `backend/app/main.py` — Creates FastAPI app, sets up logging/middleware, initialises LangGraph with checkpointing, runs DB migrations/seed, exposes health/readiness, and mounts API router. Uses `AsyncSqliteSaver` for durable graph checkpoints with in-memory fallback.

### API layer
- `backend/app/api/routers.py` — Routes for `/auth/login` (email-based lookup, issues JWT), `/chat` (runs the LangGraph app per thread_id/user), and `/chat/resume` (handles approval continue). Applies request validation, per-route rate limits, and role checks before executing write flows.

### Core services
- `backend/app/core/config.py` — Pydantic settings (DB URLs, LLM keys, timeouts, origins, checkpoint path) with helpers to normalise sync/async drivers and derive allowed origins.  
- `backend/app/core/auth.py` — JWT helpers to create tokens and dependency `get_current_user` that decodes/validates JWT and fetches user from DB.  
- `backend/app/core/middleware.py` — Request ID injection, logging middleware, and global exception handler mapping internal errors to HTTP responses.  
- `backend/app/core/logging_config.py` — Structured logging setup and logger factory.  
- `backend/app/core/exceptions.py` — Custom exception types for LLM/SQLRAG errors.  
- `backend/app/core/limiter.py` — slowapi configuration for per-endpoint rate limiting.  
- `backend/app/core` also centralises settings import (`settings`) used across modules.

### Agent (LangGraph)
- `backend/app/agent/prompts.py` — System prompt encoding roles, safety rules, two-phase writes, and workflow guidance.  
- `backend/app/agent/state.py` — Typed `AgentState` (messages, user_info, intent, proposed_plan, clarification_needed, approved, approval_token) and Pydantic models for `UserInfo` and `ProposedChange`.  
- `backend/app/agent/router.py` — Intent classifier node using chat model to return one of READ_QUERY / WRITE_PROPOSAL / WORKFLOW / CLARIFY; defaults safely on errors.  
- `backend/app/agent/llm.py` — Chat model factory (prefers Azure OpenAI, falls back to OpenAI) with request timeouts and error wrapping.  
- `backend/app/agent/tools_read.py` — Read tools: `get_tasks`, `get_projects`, `get_team_members` (SQLAlchemy queries with filters, caps, sanitised LIKE), and `get_financial_data` (delegates to financial RAG helper). Returns JSON-safe dict/list with structured errors.  
- `backend/app/agent/tools_write.py` — Write tools: `create_project`, `create_task`, `update_project`, `update_task`; apply allowlists, existence checks, commits, and structured error returns.  
- `backend/app/agent/graph.py` — Defines `StateGraph` nodes: `session_guard`, `router`, `read_executor`, `read_tools`, `read_continue`, `write_planner`, `write_executor`, `write_tools`, `write_continue`; routes on intent; loops tool execution; interrupts before `write_executor` to enforce approvals; compiles graph with configurable checkpointer.

### Database layer
- `backend/app/db/models.py` — SQLAlchemy ORM for `TeamMember`, `Project`, `Task` with relationships and defaults.  
- `backend/app/db/session.py` — Creates async session factory from settings, health-check helpers.  
- `backend/app/db/seed.py` — Seeds demo data when enabled.  
- `backend/sqlrag.db` — Default SQLite database created during dev (can swap to Postgres via env overrides).

### Auth and approval flow
- Users authenticate via email lookup (`/auth/login`) to receive JWT.  
- Chat requests attach `thread_id` and JWT; graph state keyed by `user_id:thread_id`.  
- Approval: when graph is interrupted before `write_executor`, API returns `approval_required` payload with token; `/chat/resume` validates token and role before continuing execution.

### Evals and tests
- `backend/app/evals/cases.yaml` — Intent-classification golden cases.  
- `backend/app/evals/runner.py` — Async runner to execute the cases against the router; exits non-zero on failure.  
- `backend/tests/test_chat_sql.py`, `backend/tests/test_retrieval.py` — Legacy smoke tests for SQL chat path; skipped unless DB/LLM env vars set. Extend with new tests for LangGraph behaviours as needed.

## Frontend (Next.js)
- `frontend/app/page.tsx` — Landing page with CTA to login.  
- `frontend/app/layout.tsx`, `frontend/app/globals.css` — App shell and global styles.  
- `frontend/components.json` — shadcn/ui component registry.  
- `frontend/lib/utils.ts` — UI utility helpers.  
- `frontend/Dockerfile`, `frontend/package*.json`, `frontend/tsconfig.json`, `frontend/postcss.config.mjs` — Build tooling and dependencies.  
- Static assets under `frontend/public/`.  
- Frontend currently provides scaffolding; chat/approval UI can be extended to call backend endpoints.

## Docs
- `docs/design_document.md` — Full system design, user journeys, LangGraph architecture, safety, evals, and trade-offs.  
- `docs/architecture_diagram.md` — Component list, trust boundaries, data flows, and Mermaid diagram.  
- `docs/loom_script.md` — 5–8 minute demo script with talking points and prompts.

## Tooling and ops
- `Makefile` — Convenience targets (setup, run, test, validate).  
- `docker-compose.yml` — Orchestrates backend, frontend, and supporting services for local runs.  
- `Dockerfile` — Backend container with FastAPI app.  
- `.env` (create from `backend/env.example`) — Holds DB and LLM credentials.  
- `data/` — Placeholder for supplemental datasets; not used directly by runtime yet.

## How the pieces work together (high level request flow)
1. User logs in via `/auth/login`; JWT encodes user id/role.  
2. UI sends `/chat` with `thread_id` and message; FastAPI validates JWT, rate-limits, and invokes LangGraph with state seeded from user info.  
3. Graph routes intent.  
   - READ_QUERY/CLARIFY → `read_executor` → `read_tools` as needed → `read_continue` until tool calls finish → response.  
   - WRITE_PROPOSAL/WORKFLOW → `write_planner` drafts Proposed Change Plan → graph interrupts before `write_executor`; API returns approval payload.  
4. On approval, UI calls `/chat/resume` with token; graph resumes at `write_executor`, executes write tools (with retries), logs audit info, and responds with final status.  
5. All interactions logged with trace/user context; state checkpointed per thread for durability.

## Configuration essentials
- Default DB is SQLite (`sqlrag.db`). Override with Postgres via `DATABASE_*` or `DATABASE_URL`.  
- LLM configuration: prefer Azure (`AZURE_OPENAI_*`); fallback to `OPENAI_API_KEY` + `OPENAI_MODEL`.  
- Checkpoint location: `CHECKPOINT_PATH` (defaults to `checkpoints/langgraph.db`).  
- CORS origins: `ALLOWED_ORIGINS`.  
- Rate limits: defined in `core/limiter.py` and applied per route.

## Extending the system
- Add new read/write capabilities by defining LangChain tools in `agent/tools_*.py` and binding them in `graph.py`.  
- Introduce new intents or workflows by adjusting `agent/router.py` prompt examples and `route_from_intent` branches.  
- Swap checkpoint store by passing a different LangGraph checkpointer to `create_graph` in `main.py`.  
- Integrate external systems (e.g., Jira/Slack) via new tool modules and minimal graph changes.
