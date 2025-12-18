# Loom Video Script (5–8 minutes)

## 0:00–0:30 – Intro and goal
- Screen: README top-level view of repo.  
- Say: “This is the Project Management AI Assistant built with Python, FastAPI, and LangGraph. It reads project data, proposes writes with explicit approval, and runs multi-step workflows. I’ll show architecture, a quick demo, and how we evaluate reliability.”

## 0:30–1:30 – Repo tour
- Screen: tree showing `backend/app/agent`, `backend/app/db/models.py`, `backend/app/agent/graph.py`, `frontend`.  
- Say: “Data model mirrors Projects, Tasks, Team Members. Graph nodes live in `backend/app/agent/graph.py` with router, planner, approval gate, and tool executors. Tools are typed SQLAlchemy functions; no free-form SQL.”

## 1:30–2:30 – Architecture walkthrough
- Screen: `docs/architecture_diagram.md` mermaid block or rendered diagram.  
- Say: “FastAPI fronts the LangGraph runtime. Checkpointer is SQLite for durability. Approval is enforced via `interrupt_before=['write_executor']`. Read path loops through read tools; write path is two-phase with Proposed Change Plan and audit log. Observability hooks emit trace_id, tool names, latencies.”

## 2:30–4:30 – Live demo (three prompts)
- Screen: Running app or API client.  
- Prompt 1 (Read): “Show in-progress tasks for alice@org.” Narrate: “Router marks READ; read executor calls `get_tasks`; summarises and suggests pagination.”  
- Prompt 2 (Write approval): “Rename Mobile Revamp to Mobile Reboot and mark blocked.” Show Proposed Change Plan JSON with diff and “Approve? yes/no”. Click/enter approval; show final write result and audit log snippet.  
- Prompt 3 (Workflow): “Kick off a website refresh with standard design/build/QA tasks; assign design to Sara, QA to Ron, due in 3 weeks.” Show planner output with bundled approval. Approve; show sequential tool calls and created IDs. Mention retry/backoff handling if a tool temporarily fails.

## 4:30–6:00 – Code deep dive
- Screen: `backend/app/agent/graph.py` and `state.py`.  
- Say: “State includes messages, user_info, intent, proposed_plan, approved flag, approval_token. Nodes: session_guard enforces auth; router calls classifier; write_planner prepares plan; write_executor runs after approval. Read and write tool loops handle multi-call interactions. Tools have allowlists and structured errors.”

## 6:00–7:00 – Evals and safety
- Screen: `docs/design_document.md` evaluation section or test harness snippet.  
- Say: “We run golden conversations with mocked tools. CI fails if routing accuracy or tool-call correctness drops below 95 percent or any approval leakage occurs. We classify transient vs permanent failures and retry only transient. PII is redacted in logs; audit log captures approval_token, user_id, action.”

## 7:00–7:45 – Trade-offs and scalability
- Screen: Slides or markdown bullets.  
- Say: “Chose LangGraph for stateful routing and approval interrupts; simpler loops would not persist state. Two-phase approval adds latency but prevents accidental writes. We can scale horizontally because state is in the checkpointer/DB; integrations like Jira/Asana are new tools without graph changes.”

## 7:45–8:00 – Closing
- Screen: Terminal with `uvicorn` ready or metrics dashboard.  
- Say: “You’ve seen the architecture, safety rails, demo paths, and evals. Next steps are richer entity resolution and HA checkpointer. Thanks for watching.”
