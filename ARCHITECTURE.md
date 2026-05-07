# IT Support Copilot — System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                 │
│                       Streamlit (Python, single-page app)                   │
│  ┌─────────────────────────────┐    ┌────────────────────────────────────┐  │
│  │   📝 Ticket Submission Form │    │   📊 Result + Satisfaction Survey  │  │
│  │   • Free-text description   │    │   • Color-coded by outcome         │  │
│  │   • Submitter context       │    │   • Agent trace (collapsible)      │  │
│  │   • Sample-prompt hints     │    │   • 1-5 star rating + comment      │  │
│  │   • Session ticket history  │    │   • Submit-another-ticket flow     │  │
│  └─────────────────────────────┘    └────────────────────────────────────┘  │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                      │
│                LangGraph Runtime · build_app().invoke(state)                │
│           Stateful graph traversal with conditional routing edges           │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MULTI-AGENT ORCHESTRATION                            │
│                                                                             │
│   ┌──────────────────┐                                                      │
│   │   🎯 INTAKE      │  ← Entry point: classifies user intent              │
│   │      AGENT       │    Routes to: knowledge | workflow | escalation     │
│   └────────┬─────────┘    Detects multi-turn "didn't work" follow-ups      │
│            │                                                                │
│   ┌────────┴────────────────────────────────────────────┐                   │
│   │                        │                            │                   │
│   ▼                        ▼                            ▼                   │
│ ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐                │
│ │ 📚 KNOWLEDGE │    │ ⚡ WORKFLOW   │    │ 🚨 ESCALATION    │                │
│ │    AGENT     │    │    AGENT     │    │     AGENT        │                │
│ ├──────────────┤    ├──────────────┤    ├──────────────────┤                │
│ │ • RAG search │    │ • Plan       │    │ • Diagnostic     │                │
│ │ • Synthesize │    │   actions    │    │   summary for    │                │
│ │   answer     │    │ • Execute    │    │   on-call        │                │
│ │ • Cite       │    │   MCP tools  │    │ • High-priority  │                │
│ │   sources    │    │ • Audit      │    │   Jira incident  │                │
│ │ • Self-      │    │   ticket     │    │ • Friendly       │                │
│ │   service    │    │ • Move       │    │   user message   │                │
│ │   first      │    │   to Done    │    │ • Move to        │                │
│ │              │    │              │    │   In Progress    │                │
│ └──────────────┘    └──────────────┘    └──────────────────┘                │
│        │                   │                     │                          │
└────────┼───────────────────┼─────────────────────┼──────────────────────────┘
         │                   │                     │
         ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA & SERVICES                                  │
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌─────────────────────┐    │
│  │  🗄️ Chroma Vector  │  │  🔌 MCP Tool       │  │  🤖 OpenAI API      │    │
│  │     Store (local)  │  │     Registry       │  │                     │    │
│  ├────────────────────┤  ├────────────────────┤  ├─────────────────────┤    │
│  │ • 84 chunks        │  │ • jira.create_     │  │ • gpt-4o-mini       │    │
│  │ • 8 markdown       │  │   ticket           │  │ • Intent classify   │    │
│  │   runbooks         │  │ • jira.create_     │  │ • Answer synthesis  │    │
│  │ • text-embedding-  │  │   incident         │  │ • Escalation        │    │
│  │   3-small (1536d)  │  │ • jira.transition_ │  │   summary           │    │
│  │ • Persistent       │  │   issue            │  │ • text-embedding-   │    │
│  │   on disk          │  │ • idp.* (mock)     │  │   3-small           │    │
│  │                    │  │ • catalog.* (mock) │  │                     │    │
│  │                    │  │ • logs.* (mock)    │  │                     │    │
│  └────────────────────┘  └─────────┬──────────┘  └─────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│                          ┌─────────────────────┐                            │
│                          │  🎫 Atlassian Jira  │                            │
│                          │   Cloud REST API    │                            │
│                          │  TIC project board  │                            │
│                          └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Request Flow

```
User submits ticket
         │
         ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐
│ Intake Agent│ ──▶ │ Classify    │ ──▶ │ Route to Specialist     │
│ (LLM call)  │     │ Intent +    │     │ Agent based on          │
│             │     │ Entities    │     │ request_type + flags    │
└─────────────┘     └─────────────┘     └────────────┬────────────┘
                                                     │
                    ┌────────────────────────────────┼─────────────────────────────────┐
                    │                                │                                 │
                    ▼                                ▼                                 ▼
           ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
           │ Knowledge Agent │             │ Workflow Agent  │             │ Escalation Agent│
           │                 │             │                 │             │                 │
           │ 1. Embed query  │             │ 1. Plan actions │             │ 1. Build engineer│
           │ 2. Chroma top-5 │             │    deterministic│             │    handoff with │
           │ 3. Synthesize   │             │ 2. Call MCP     │             │    full context │
           │    grounded     │             │    tools each   │             │ 2. Create high- │
           │    answer       │             │ 3. Audit ticket │             │    priority     │
           │ 4. Cite sources │             │ 4. Move to Done │             │    Jira ticket  │
           │ 5. Audit ticket │             │                 │             │ 3. Move to In   │
           │ 6. Move to Done │             │                 │             │    Progress     │
           └────────┬────────┘             └────────┬────────┘             └────────┬────────┘
                    │                               │                               │
                    │  (no answer in runbooks)      │  (action failed / high sev)   │
                    └──────────────┐                └──────────────┐                │
                                   ▼                               ▼                ▼
                         (re-routes to escalation)       (re-routes to escalation)  │
                                   │                               │                │
                                   └───────────────────────────────┴────────────────┘
                                                       │
                                                       ▼
                                          ┌─────────────────────┐
                                          │ Final answer +      │
                                          │ Jira reference      │
                                          └──────────┬──────────┘
                                                     │
                                                     ▼
                                              User sees result
                                              + satisfaction survey
```

## Conditional Routing Rules

The graph in `src/graph.py` wires four nodes with three conditional routers:

| From | Condition | To |
|------|-----------|-----|
| `intake` | `follow_up_after_failed_help == True` | `escalation` |
| `intake` | `confidence < 0.5` or `request_type == "unclear"` | `escalation` |
| `intake` | `request_type == "informational"` | `knowledge` |
| `intake` | `request_type ∈ {action, incident}` | `workflow` |
| `knowledge` | `knowledge_unknown` (LLM emitted "I_DONT_KNOW") | `escalation` |
| `knowledge` | answer succeeded | `END` |
| `workflow` | `workflow_no_plan` (no automation matches) | `knowledge` (fallback) |
| `workflow` | `escalation_required` (action failed / severity high) | `escalation` |
| `workflow` | all actions succeeded, low/medium severity | `END` |
| `escalation` | always | `END` |

The Workflow → Knowledge fallback edge is what lets messages like "set up email forwarding for me" still reach the right runbook even though they sound action-shaped.

## Agent Responsibilities

| Agent | File | What it does | LLM call? |
|-------|------|---------------|-----------|
| **Intake** | `src/agents/intake.py` | Structured-output classification: `request_type`, `category`, `system`, `severity`, `confidence`, `follow_up_after_failed_help`, `entities`. Multi-turn aware. | Yes |
| **Knowledge** | `src/agents/knowledge.py` | RAG over Chroma. Synthesizes answer with citations or emits "I don't know" sentinel. Creates audit ticket and moves it to Done. | Yes |
| **Workflow** | `src/agents/workflow.py` | Deterministic action planner (no LLM) that maps intent to a list of MCP tool calls. Executes them, opens an audit ticket, transitions to Done. | No |
| **Escalation** | `src/agents/escalation.py` | LLM-generated structured handoff (problem, classification, prior conversation, automation steps, diagnostic data, suggested next steps). Creates a high-priority Jira ticket and transitions to In Progress. | Yes |

## Local Deployment

This project runs as a single Python process. No containers, no databases to provision, no external services to spin up — only Python, a venv, and an internet connection for the OpenAI and Jira APIs.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Single Python Process                        │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ Streamlit Server │  │ LangGraph Runtime│  │ Chroma       │   │
│  │ Port: 8501       │  │ (in-process)     │  │ (in-process, │   │
│  │ (browser UI)     │  │                  │  │  on disk)    │   │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘   │
│           │                     │                   │           │
│           └─────────────────────┴───────────────────┘           │
│                                 │                               │
│                                 ▼                               │
│                       ┌──────────────────┐                      │
│                       │ External APIs    │                      │
│                       │ • OpenAI         │                      │
│                       │ • Atlassian Jira │                      │
│                       └──────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

For production-scale deployment options (Docker, Kubernetes, multiple replicas, managed vector store), see [SCALING.md](SCALING.md).

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Streamlit 1.39 (Python) |
| **AI/LLM** | OpenAI `gpt-4o-mini`, `text-embedding-3-small` |
| **Orchestration** | LangGraph 1.x with conditional state-graph routing |
| **Vector store** | Chroma 1.x (persistent, local) |
| **Tool protocol** | MCP-shaped tool registry (uniform `client.call_tool(name, **params)` interface, swap-ready for real MCP servers) |
| **Ticketing** | Atlassian Jira Cloud REST API v3 |
| **Validation** | Pydantic 2 (typed `GraphState`, structured LLM outputs) |
| **Testing** | pytest + custom eval harness (latency p50/p95, triage accuracy, kind-match) |

## Observability

Each agent node wraps with `@traced(node_name)`, which appends `enter` and `exit` `TraceEvent`s to `state.trace` with millisecond-precision timing. The Streamlit UI renders these in the "How we figured this out" expander so the user (and grader) can see exactly which agents fired and how long each took. The same trace data can be aggregated to produce the metrics in [docs/success_metrics.md](docs/success_metrics.md).
