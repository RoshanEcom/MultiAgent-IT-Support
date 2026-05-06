# Architecture

## High-level system

See [system_architecture.mmd](system_architecture.mmd) for the diagram.

The system is a single LangGraph state machine. The user's message enters through
either the Streamlit chat UI or the CLI. A LangGraph runtime drives a `GraphState`
through four agent nodes (Intake → Knowledge | Workflow → Escalation if needed) and
returns a `final_answer` plus a trace of what each agent did.

```
User → UI/CLI → LangGraph Runtime
                    │
                    ├── Intake Agent      (classify)
                    ├── Knowledge Agent   (RAG over runbooks)
                    ├── Workflow Agent    (MCP tool calls)
                    └── Escalation Agent  (Jira incident + summary)
                            │
                            ↓
                       MCP Tool Registry
                            │
                ┌───────────┼─────────────┬──────────────┐
                ↓           ↓             ↓              ↓
              Jira       IDP (mock)    Logs (mock)   Catalog (mock)
```

## State

`src/state.py` defines `GraphState` (a Pydantic model). Every node receives the
current state, mutates the relevant fields, and returns it. The fields:

| Field | Owner | Purpose |
|---|---|---|
| `messages` | UI / all | Conversation history |
| `user` | UI | User identity (id, department, office) |
| `intent` | Intake | Classified `request_type`, `system`, `severity`, `confidence` |
| `entities` | Intake | Extracted slot values (software name, channel name, etc.) |
| `retrieved_docs` | Knowledge | RAG hits with snippets and citations |
| `knowledge_answer` | Knowledge | Synthesized informational answer |
| `actions` | Workflow | Planned and executed action records |
| `tool_results` | Workflow / Escalation | Raw responses from MCP tool calls |
| `escalation_required` | Workflow / Intake | Set when something can't be auto-resolved |
| `escalation_ticket_id` | Workflow / Escalation | Jira key returned from `jira.create_ticket` |
| `final_answer` | Knowledge / Workflow / Escalation | The user-facing reply |
| `trace` | All | Append-only log of node entries/exits, for observability |

## Agents

### Intake (`src/agents/intake.py`)

- LLM call with structured output (`IntakeSchema`) — single round-trip.
- Returns `request_type ∈ {informational, action, incident, unclear}`,
  `category` (e.g. `software_license`, `hardware`, `access`, `email`, `printer`, `av`),
  `system`, `severity`, extracted `entities`, and `confidence`.
- Confidence below 0.5 forces routing through the Escalation agent rather than guessing.

### Knowledge (`src/agents/knowledge.py`)

- Runs only when `request_type` is `informational` or when an incident benefits
  from runbook context.
- Embeds the user's question with OpenAI embeddings, retrieves top-5 chunks from
  Chroma, and synthesizes an answer with `gpt-4o-mini`.
- The system prompt explicitly instructs the LLM to answer **only from the context**
  and to say "I don't know based on the runbooks" if the context doesn't cover the
  question — this is what keeps hallucination rate down. If the LLM emits the
  unknown sentinel, routing falls through to Escalation.
- Always returns citations alongside the answer (file name + chunk index).

### Workflow (`src/agents/workflow.py`)

- Runs when `request_type` is `action` or `incident`.
- Uses a deterministic `plan_actions(state)` function (not an LLM) to map intent
  to a list of `Action` records. Keeping the planner deterministic means the
  audit trail is reviewable and the action set is bounded.
- For each action, calls a named MCP tool through the registry. Catches
  exceptions per-action; a single failure escalates rather than aborting the graph.
- Always emits a `jira.create_ticket` action at the end of any successful workflow,
  so there is an audit record even when no human ever sees it.

### Escalation (`src/agents/escalation.py`)

- Runs when:
  - Intake confidence < 0.5, OR
  - Knowledge agent emitted "I don't know", OR
  - Any workflow action failed, OR
  - Severity is `high`.
- Uses the LLM to produce a human-readable summary that covers original request,
  intent classification, retrieved docs, tool results, and suggested next steps.
- Calls `jira.create_incident` (a higher-priority Jira issue type than the audit
  tickets the Workflow agent creates).

## Routing (`src/graph.py`)

```
                          ┌──────────────┐
                          │   intake     │
                          └──────┬───────┘
                ┌────────────────┼────────────────┐
        informational       action/incident     unclear/low-conf
                │                │                │
                ↓                ↓                ↓
          ┌──────────┐     ┌──────────┐     ┌────────────┐
          │knowledge │     │ workflow │     │ escalation │
          └────┬─────┘     └────┬─────┘     └──────┬─────┘
               │                │                  │
       answer ✓│                │ all-success      │
               │                │                  │
               ↓                ↓                  ↓
              END             END                END
               │                │
       answer ✗│        any-fail / high sev
               └────────────────┴──→ escalation
```

Conditional edges live in `src/graph.py`; each routing function is a pure inspection
of `GraphState` so they're trivial to unit-test.

## RAG layer (`src/rag/`)

- **Source documents:** markdown files under `knowledge_base/`. Markdown was chosen
  over PDF so the runbooks are reviewable in PRs and trivially editable; the loader
  treats each `##` heading as a chunk boundary in addition to character-based splitting.
- **Chunking:** `RecursiveCharacterTextSplitter` with chunk_size=1000 and overlap=200.
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dim; cheap and fast enough
  for this corpus size).
- **Vector store:** Chroma in persistent mode at `./.chroma`. No separate server
  process; the index is a sqlite + parquet directory.
- **Retrieval:** top-k=5 with metadata-filter support (e.g., restrict to a specific
  runbook when the Intake agent is highly confident about the category).

## MCP tool layer (`src/mcp/`)

The MCP layer is intentionally MCP-*shaped* rather than wire-protocol-MCP. It
ships a uniform client interface (`MCPClient.call(tool_name, **kwargs) -> dict`)
backed by a local `ToolRegistry`. Each registered tool declares its name and
parameters; the client validates inputs, dispatches the call, and returns a
structured result.

| Tool | Implementation | What it does |
|---|---|---|
| `jira.create_ticket` | Real Atlassian REST API | Creates a Task issue in the configured project as the audit record for an automated action. |
| `jira.create_incident` | Real Atlassian REST API | Creates an Incident-type issue with high priority for human handoff. |
| `idp.provision_software` | Mock | Simulates provisioning a software license via Okta/Azure AD app assignment. |
| `idp.add_to_group` | Mock | Simulates adding a user to a Slack channel / mailing list / shared drive. |
| `catalog.lookup_hardware` | Mock | Looks up a hardware SKU by description. |
| `catalog.place_order` | Mock | Simulates placing a hardware order with shipping info. |
| `logs.get_recent` | Mock | Returns synthetic A/V or system log events for the last N hours. |

If `JIRA_API_TOKEN` is empty, the Jira tools fall back to a console-logging mock
that returns plausible ticket IDs (`IT-MOCK-1`, `IT-MOCK-2`, …) so the system runs
end-to-end with only an OpenAI key configured. This is the demo path.

### Why MCP-shaped instead of full wire MCP for v1

A real MCP server adds a JSON-RPC transport (stdio or SSE), connection lifecycle,
and capability negotiation — meaningful surface area for v1. The local registry
keeps the same call signature and tool descriptor shape, so swapping in
`mcp.client.Client` later is a one-file change in `src/mcp/client.py`. The
*conceptual* MCP integration — uniform tool access regardless of the underlying
system — is fully demonstrated.

## Observability

Every node appends a `TraceEvent` to `state.trace` on entry and exit, with
timing information. The Streamlit UI renders this as a sidebar so the user
(and grader) can see exactly which agents fired, what the Intake classified,
which docs were retrieved, and which tools ran.
