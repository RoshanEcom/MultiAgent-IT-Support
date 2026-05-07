# IT Support Copilot

A multi-agent Agentic AI system for IT helpdesks built on **LangGraph**,
**OpenAI**, **Chroma**, and the **Model Context Protocol (MCP)**. Classifies
incoming requests, answers what it can from runbooks (RAG), executes routine
actions through MCP-style tools, and escalates the rest to a human IT engineer
with full diagnostic context.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-1.x-green)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-black)
![Chroma](https://img.shields.io/badge/Chroma-vectorstore-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39-red)
![MCP](https://img.shields.io/badge/MCP-shaped--registry-purple)

---

## Problem Definition

### User Pain Points

| Pain Point | Impact | Solution |
|------------|--------|----------|
| Long wait times for routine IT requests | Productivity loss | Instant Knowledge-agent answers from runbooks |
| Repetitive tickets (license requests, access, hardware) | IT staff burnout on Tier-1 work | Workflow agent auto-completes via MCP tools |
| Scattered runbooks across wikis / Drive / Slack | User frustration | Unified RAG knowledge base over markdown runbooks |
| No visibility into what the AI did on the user's behalf | Trust gap | Every interaction creates a Jira ticket with full agent trace |
| Escalations arrive without context | Engineers re-ask everything | Escalation agent summarizes problem + steps tried + diagnostic data |

### Success Metrics

- **First-response latency:** p50 < 4s, p95 < 10s (measured live; see `state.trace`)
- **Triage accuracy:** ≥ 85% on the 10-scenario gold set
- **Deflection rate:** ≥ 60% of in-scope tickets resolved without a human
- **Escalation completeness:** every escalation includes problem + classification + automation steps + diagnostic data + suggested next steps
- **User satisfaction:** ≥ 4.0/5 average from the in-app star survey

Full metric definitions and measurement methods in [docs/success_metrics.md](docs/success_metrics.md).

---

## Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│              (Streamlit — ticket form + survey)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        INTAKE AGENT                             │
│   Classifies intent → routes to: knowledge | workflow |         │
│   escalation. Multi-turn aware (detects "didn't work" follow-   │
│   ups and short-circuits to escalation).                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ KNOWLEDGE AGENT │ │ WORKFLOW AGENT  │ │ ESCALATION AGENT│
│                 │ │                 │ │                 │
│ • RAG retrieval │ │ • Plan actions  │ │ • Build engineer│
│ • Synthesize    │ │ • Execute MCP   │ │   handoff       │
│   answer        │ │   tool calls    │ │ • Create high-  │
│ • Cite sources  │ │ • Audit ticket  │ │   priority Jira │
│ • Audit ticket  │ │ • Move to Done  │ │ • Move to In    │
│ • Move to Done  │ │                 │ │   Progress      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                  │
│   Chroma (local) · MCP Tool Registry · OpenAI · Jira REST API   │
└─────────────────────────────────────────────────────────────────┘
```

Full architecture diagram, routing rules, and per-agent responsibilities in
[ARCHITECTURE.md](ARCHITECTURE.md).

### Agent Roles

| Agent | Responsibility | Technology |
|-------|---------------|------------|
| **Intake** | Intent classification (LLM-powered, structured output) | OpenAI gpt-4o-mini + Pydantic schema |
| **Knowledge** | RAG-grounded Q&A from internal runbooks | OpenAI embeddings + Chroma + LLM synthesis |
| **Workflow** | Execute concrete actions (provision license, request hardware, grant access) | Deterministic planner + MCP tool calls |
| **Escalation** | Route to human IT with full context | LLM-summarized handoff + Jira high-priority ticket |

---

## Features

### Core Capabilities

- ✅ **Multi-Agent Orchestration** — four specialized agents wired with LangGraph conditional edges
- ✅ **RAG Knowledge Base** — semantic search over markdown runbooks (84 chunks across 8 documents)
- ✅ **Workflow Automation** — software license provisioning, hardware ordering, group access, log retrieval, ticket creation
- ✅ **MCP-Shaped Tool Layer** — uniform tool registry with real Jira REST integration + mock IDP/catalog/logs (swap-ready for real MCP servers)
- ✅ **Multi-Turn Awareness** — detects "I tried that, it didn't work" follow-ups and escalates with prior conversation attached
- ✅ **Workflow → Knowledge Fallback** — action-flavored requests with no automation route automatically fall back to runbook search
- ✅ **Real Jira Integration** — every interaction lands on the project board with appropriate status (`Done` for AI-resolved, `In Progress` for human-handoff)
- ✅ **Per-Agent Latency Tracking** — `TraceEvent` log captures node entry/exit timings for live observability

### User Experience

- ✅ Single-page Streamlit ticket form with examples in the placeholder
- ✅ Color-coded result panels (answered / action completed / transferred to human)
- ✅ Collapsible "How we figured this out" agent trace under every response
- ✅ 1-5 star satisfaction survey + optional free-text feedback after each ticket
- ✅ Sidebar history of tickets submitted in the current session
- ✅ Submitter context (department, office) flows into agent reasoning

---

## Example Queries

The system understands natural phrasing — you don't need canonical wording.
Below are representative prompts for each path.

### Knowledge Base (RAG) — answer with citations

| Query | Expected Response |
|-------|-------------------|
| "How do I reset my password?" | Self-service Okta steps from `password_reset.md` |
| "I'm locked out, how do I get back in?" | Same — multi-turn aware, escalates only if user follows up that it didn't work |
| "How do I set up email forwarding while on PTO?" | Outlook web steps + corporate-only restriction |
| "How do I forward email to my personal Gmail?" | Correct policy answer: not permitted under data-handling policy |
| "How do I add the 3rd-floor color printer in SF?" | Hostname + LPD setup steps, OS-aware |
| "I just started today, what do I need to set up?" | New-hire week 1 checklist by department |

### Workflow Actions — execute + create Jira audit ticket (Done)

| Query | Expected Action |
|-------|-----------------|
| "I need a Figma license for design work" | `idp.provision_software` → manager-approval pending → Jira audit ticket → Done |
| "Please grant me a Loom license" | Auto-approves immediately → Jira audit ticket → Done |
| "I need a second monitor for my SF desk" | `catalog.lookup_hardware` → `catalog.place_order` → Jira ticket → Done |
| "Add me to the #data-platform Slack channel" | `idp.add_to_group` → Jira audit ticket → Done |

### Escalation — high-severity / not-in-runbook / failed action (In Progress)

| Query | Expected Response |
|-------|-------------------|
| "Conference Room B projector shows 'no signal' and I have a demo in 10 minutes" | Pulls A/V logs → escalates with full diagnostic context → Jira ticket → In Progress |
| Any "how do I X" answer followed by *"I tried that, didn't work"* | Multi-turn handoff including what the user already tried |
| Any out-of-scope request | Escalates with classification confidence noted |

---

## Quick Start

This repo is configured to run end-to-end out of the box with the project
owner's credentials. Trusted clones can use the included `.env` directly. To
run with your own keys, edit `.env` after cloning.

### Prerequisites

- Python 3.11+ (tested on 3.13)
- An OpenAI API key with at least a few dollars of credit
- *(Optional)* A Jira Cloud workspace + API token. Without it, the system
  falls back to a console-mock with simulated ticket IDs.

### Installation

```powershell
# Clone the repo
git clone https://github.com/RoshanEcom/MultiAgent-IT-Support.git
cd MultiAgent-IT-Support

# Create venv and install
python -m venv .venv
.venv\Scripts\Activate.ps1            # Windows PowerShell
# source .venv/bin/activate           # macOS / Linux
pip install -r requirements.txt

# Build the vector index (one-time, ~30 seconds, ~$0.005 of OpenAI credit)
python scripts/ingest_kb.py

# Run the UI
streamlit run app/streamlit_app.py
```

Open http://localhost:8501.

### Configure your own credentials

Edit `.env` and replace `OPENAI_API_KEY`. Generate a key at
https://platform.openai.com/api-keys.

For a clean Jira swap, replace `JIRA_BASE_URL`, `JIRA_EMAIL`,
`JIRA_API_TOKEN`, and `JIRA_PROJECT_KEY` with your own. Or blank them out
entirely to use the console-mock.

### Rebuild the index after editing runbooks

```powershell
python scripts/ingest_kb.py --rebuild
```

---

## Project Structure

```
.
├── README.md                  This file
├── ARCHITECTURE.md            System architecture + routing rules
├── SCALING.md                 Production scaling strategy (Docker / K8s / observability)
├── VENDOR_RESEARCH.md         Moveworks + Glean competitive analysis
├── requirements.txt           Pinned Python deps
├── .env                       Tracked credentials (project owner's)
├── docs/
│   ├── product_brief.md       Use cases, personas, success metrics
│   ├── architecture.md        Deep-dive engineering doc (state, agents, routing)
│   ├── ux_wireframes.md       UI states + design rationale
│   ├── success_metrics.md     4-bucket metrics with measurement methods
│   ├── system_architecture.mmd  Mermaid system diagram
│   └── workflow_sequence.mmd    Mermaid sequence diagram
├── knowledge_base/            Source-of-truth runbooks (markdown, RAG-ingested)
│   ├── access_requests.md
│   ├── conference_room_av.md
│   ├── email_setup.md
│   ├── hardware_requests.md
│   ├── new_hire_setup.md
│   ├── password_reset.md
│   ├── printer_setup.md
│   └── software_licenses.md
├── src/
│   ├── config.py              .env loader + Settings dataclass
│   ├── state.py               Pydantic GraphState + Intent + Action + TraceEvent
│   ├── llm.py                 OpenAI client factories
│   ├── graph.py               LangGraph wiring + conditional routing
│   ├── main.py                CLI entry point (single-shot)
│   ├── rag/
│   │   ├── ingest.py          Markdown → header split → char split → embed → Chroma
│   │   └── retriever.py       Top-k similarity search
│   ├── mcp/
│   │   ├── client.py          MCP-shaped tool client + registry assembly
│   │   ├── registry.py        Tool descriptor + dispatcher
│   │   ├── jira_tool.py       Real Atlassian REST (create, transition)
│   │   ├── idp_tool.py        Mock IDP (provision_software, add_to_group, reset_password)
│   │   ├── catalog_tool.py    Mock hardware catalog (lookup, place_order)
│   │   └── logs_tool.py       Mock observability (get_recent)
│   └── agents/
│       ├── intake.py          Structured-output intent classifier
│       ├── knowledge.py       RAG + synthesis + audit ticket
│       ├── workflow.py        Deterministic planner + MCP execution
│       ├── escalation.py      Engineer handoff + high-priority ticket
│       └── _trace.py          @traced decorator for per-node timing
├── app/
│   └── streamlit_app.py       Ticket-submission UI with survey
├── scripts/
│   └── ingest_kb.py           One-shot vector index builder
└── tests/
    ├── gold_set.json          10 hand-labeled scenario fixtures
    ├── test_scenarios.py      pytest end-to-end scenarios
    └── eval_metrics.py        Latency p50/p95 + accuracy harness
```

---

## Testing

### Run the test suite

```powershell
# End-to-end scenarios (hits real OpenAI; ~30s, ~$0.05)
pytest tests/test_scenarios.py -v

# Eval harness (prints accuracy + latency report)
python tests/eval_metrics.py
```

### Test coverage

- **`test_scenarios.py`** — 10 scenarios across all four agent paths
  (informational, action-completed, action-pending, escalated, multi-turn)
- **`gold_set.json`** — hand-labeled `request_type` + `category` + expected
  `final_answer_kind` per scenario
- **`eval_metrics.py`** — runs every scenario, reports:
  - `request_type` accuracy
  - `category` accuracy
  - `severity` accuracy
  - `final_answer_kind` match rate
  - p50 / p95 / max end-to-end latency

---

## MCP Server

The MCP-shaped tool registry exposes seven tools through a uniform
`client.call_tool(name, **params)` interface. The interface mirrors
`mcp.client.Client` so the local registry can be swapped for a real MCP
client (e.g., Atlassian's MCP server, GitHub MCP server) without changing
agent code.

| Tool | Description |
|------|-------------|
| `jira.create_ticket` | Audit Task ticket (Workflow + Knowledge agents) |
| `jira.create_incident` | High-priority ticket for human handoff (Escalation agent) |
| `jira.transition_issue` | Move ticket to a named status (`Done`, `In Progress`) |
| `idp.provision_software` | Mock — assign a software license from the catalog |
| `idp.add_to_group` | Mock — add user to Slack channel / mailing list / drive |
| `idp.reset_password` | Mock — issue a temporary password |
| `catalog.lookup_hardware` | Mock — find a hardware SKU by free-text description |
| `catalog.place_order` | Mock — place an order, choosing on-site vs ship |
| `logs.get_recent` | Mock — synthetic log events per service for incident context |

The Jira tools hit the real Atlassian REST API when credentials are
configured. They fall back to console-logging mocks otherwise — the system
still runs end-to-end with only an OpenAI key.

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key (LLM + embeddings) | Yes |
| `OPENAI_LLM_MODEL` | Override the chat model (default `gpt-4o-mini`) | No |
| `OPENAI_EMBEDDING_MODEL` | Override the embedding model (default `text-embedding-3-small`) | No |
| `JIRA_BASE_URL` | Atlassian workspace URL (e.g., `https://yourorg.atlassian.net`) | No (mock fallback) |
| `JIRA_EMAIL` | Atlassian account email | No (mock fallback) |
| `JIRA_API_TOKEN` | Atlassian API token | No (mock fallback) |
| `JIRA_PROJECT_KEY` | Project key prefix (e.g., `TIC` → ticket IDs are `TIC-N`) | No (defaults to `IT`) |
| `KB_DIR` | Knowledge base directory | No (defaults to `knowledge_base`) |
| `CHROMA_DIR` | Persistent Chroma directory | No (defaults to `.chroma`) |

---

## Metrics & Validation

The system tracks performance live through `state.trace` (per-node entry/exit
timings) and `feedback.jsonl` (every survey submission with rating, comment,
classification, and outcome). The eval harness aggregates these into a
report:

```
✓ sw-license-figma           rt=action       cat=software_license  sev=medium  kind=action_completed_or_pending  3911ms
✓ sw-license-loom-auto       rt=action       cat=software_license  sev=low     kind=action_completed              4023ms
✓ hw-monitor                 rt=action       cat=hardware          sev=low     kind=action_completed              4188ms
✓ access-slack               rt=action       cat=access            sev=low     kind=action_completed_or_pending   2997ms
✓ info-email-forward         rt=informational cat=email            sev=low     kind=informational                 6840ms
✓ info-printer-add           rt=informational cat=printer          sev=low     kind=informational                 5620ms
✓ incident-av-projector      rt=incident     cat=av                sev=high    kind=escalated                     6701ms
…

  request_type accuracy: 10/10
  category accuracy:     10/10
  final-answer-kind:     10/10

  latency p50: 4188ms
  latency p95: 6840ms
```

Run `python tests/eval_metrics.py` to regenerate.

---

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — system architecture, routing rules, agent responsibilities
- **[SCALING.md](SCALING.md)** — production scaling: Docker, K8s, caching, observability, cost
- **[VENDOR_RESEARCH.md](VENDOR_RESEARCH.md)** — competitive analysis of Moveworks and Glean
- **[docs/product_brief.md](docs/product_brief.md)** — product owner doc: use cases, personas, success metrics
- **[docs/architecture.md](docs/architecture.md)** — deep engineering doc (state, agents, routing details)
- **[docs/ux_wireframes.md](docs/ux_wireframes.md)** — UI states and design rationale
- **[docs/success_metrics.md](docs/success_metrics.md)** — full metrics definitions

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | Streamlit 1.39 (Python) |
| **AI/ML** | OpenAI gpt-4o-mini, text-embedding-3-small |
| **Orchestration** | LangGraph 1.x with conditional state-graph routing |
| **Vector store** | Chroma 1.x (persistent, local) |
| **Tool protocol** | MCP-shaped tool registry, swap-ready for real MCP servers |
| **Ticketing** | Atlassian Jira Cloud REST API v3 |
| **Validation** | Pydantic 2 (typed `GraphState` + structured LLM outputs) |
| **Testing** | pytest + custom eval harness |
