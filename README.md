# IT Support Copilot — Multi-Agent AI Helpdesk

A multi-agent Agentic AI system that handles common IT support requests
end-to-end: classify → answer-from-runbook OR run-automation → escalate-to-human
when needed. Built for the *Multi-Agent AI System for IT Support* capstone.

Positioned as a lightweight, self-hostable prototype of enterprise tools like
Glean Assistant or Moveworks.

## What it actually does

Type something like:

- *"I need a Figma license for design work"* → classified as a software license request, the Workflow agent provisions it (mock IDP) and opens a Jira ticket as the audit record.
- *"How do I set up my email signature?"* → classified as informational, the Knowledge agent retrieves the relevant runbook chunks and answers with citations.
- *"My laptop battery dies after 30 min, I'm in NYC office"* → classified as a hardware request, the Workflow agent checks the catalog, places an order, and creates a tracking Jira ticket.
- *"Conference Room B projector is showing 'no signal' before my 3pm demo"* → classified high-severity incident, fetches recent A/V logs, and escalates to a human with a full diagnostic summary.

## The four agents

| Agent | Job | Key tools |
|---|---|---|
| **Intake** | Classify the request: type (informational / action / incident), system, severity, entities, confidence. | OpenAI structured output |
| **Knowledge** | RAG over markdown runbooks. Answers informational questions with citations. | OpenAI embeddings + Chroma + LLM synthesis |
| **Workflow** | Plans + executes a sequence of MCP tool calls (provision license, order hardware, grant access, create Jira ticket). | MCP-style tool registry |
| **Escalation** | Builds an engineer-ready diagnostic summary and opens a Jira incident when a request can't be auto-resolved. | Jira MCP tool |

LangGraph wires them together with conditional routing — see [docs/architecture.md](docs/architecture.md).

## Tech stack

- **Orchestration:** LangGraph
- **LLM:** OpenAI `gpt-4o-mini`
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Vector store:** Chroma (local, persistent — no separate process)
- **Tool protocol:** MCP-style tool registry. Real Jira REST API for ticketing; mock IDP / logs / catalog tools for the rest. Designed to be swapped for real MCP servers without changing agent code.
- **Knowledge base:** Markdown runbooks under `knowledge_base/`
- **UI:** Streamlit chat app

## Quickstart

```bash
# 1. Install
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 2. Configure
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# Then edit .env — at minimum, paste in OPENAI_API_KEY.
# Jira creds are optional; without them the system falls back to console-logged
# tickets with simulated IDs so you can still demo end-to-end.

# 3. Build the vector index from the runbooks
python scripts/ingest_kb.py

# 4. Run it
streamlit run app/streamlit_app.py
# or one-shot CLI:
python -m src.main "I need a Figma license"
```

## Project layout

```
.
├── README.md
├── requirements.txt
├── .env.example
├── docs/                      Product brief, architecture, wireframes, metrics
├── knowledge_base/            Source-of-truth runbooks (markdown)
├── src/
│   ├── config.py              Env + settings
│   ├── state.py               Pydantic GraphState
│   ├── llm.py                 OpenAI client factories
│   ├── rag/                   Ingestion + retrieval
│   ├── mcp/                   MCP-style tool registry + tool implementations
│   ├── agents/                Intake / Knowledge / Workflow / Escalation
│   ├── graph.py               LangGraph wiring + routing
│   └── main.py                CLI entry point
├── app/streamlit_app.py       Chat UI for the demo
├── scripts/ingest_kb.py       One-shot KB build
└── tests/
    ├── test_scenarios.py      End-to-end scenario tests
    └── eval_metrics.py        Latency + accuracy harness
```

See [docs/product_brief.md](docs/product_brief.md) for use cases and success metrics
and [docs/architecture.md](docs/architecture.md) for the system design.
