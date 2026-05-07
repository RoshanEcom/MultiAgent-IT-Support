# Industry Vendor Research: AI-Powered Employee Support

This document analyzes two leading vendors in the AI-powered employee/IT
support space — **Moveworks** and **Glean** — to understand the competitive
landscape and identify integration opportunities for the IT Support Copilot.
Both companies are venture-backed leaders that productized the same core
patterns this prototype demonstrates (multi-agent orchestration, RAG over
enterprise knowledge, automated workflows), at a vastly larger scale.

---

## Executive Summary

| Vendor | Market Position | Key Strength | Integration Potential |
|--------|----------------|--------------|----------------------|
| **Moveworks** | Enterprise AI Copilot leader | Action automation across IT/HR/finance | High — REST API + native MCP server |
| **Glean** | Enterprise AI search leader | Permission-aware RAG over 100+ apps | High — `glean://` connectors for our RAG layer |

Both vendors validate the architectural choices in this project: Intake +
Knowledge + Workflow + Escalation is, broadly, the same shape Moveworks ships
as their Copilot, and Glean Assistant is the same shape as our Knowledge agent
extended to multi-source search.

---

## 1. Moveworks

### Company Overview

- **Founded:** 2016 by Bhavin Shah, Vaibhav Nivargi, Varun Singh, Jiang Chen
- **Headquarters:** Mountain View, CA
- **Funding:** $315M+ raised across Series A–C (Kleiner Perkins, Lightspeed, Tiger Global, Bain Capital Ventures)
- **Valuation:** ~$2.1B (2021 Series C)
- **Acquisition:** Announced agreement to be acquired by **ServiceNow** in March 2025 for ~$2.85B, integrating Moveworks' AI Copilot into ServiceNow's Now Platform
- **Customers:** Broadcom, DocuSign, Palo Alto Networks, Toyota, Western Digital, Pinterest (~5M+ end users)
- **Core Focus:** Conversational AI Copilot for employee support — IT, HR, facilities, finance

### Key Features

| Feature | Description | Our Equivalent |
|---------|-------------|----------------|
| **Moveworks Copilot** | Slack/Teams-native AI assistant for any employee request | ✅ Streamlit ticket form (single-channel prototype) |
| **Plug-ins / Actions** | 100+ pre-built integrations: ServiceNow, Workday, Okta, Jira, ADP, Concur, etc. Each is a typed action the LLM can call. | ✅ MCP-style tool registry with Jira live + IDP/catalog/logs mocked |
| **Moveworks LLM stack ("MoveLM")** | Internal multi-LLM router that picks the cheapest model per intent | 🟡 Single-model architecture; planned cost work in [SCALING.md](SCALING.md#cost-optimization) |
| **Conversational Analytics** | Per-conversation telemetry surfaced to admins — deflection rate, satisfaction, common requests | ✅ `state.trace` + `feedback.jsonl` give the same primitives at small scale |
| **Triage Agent / Insights** | LLM auto-categorizes incoming tickets across systems and surfaces hot topics | ✅ Intake agent's structured-output classifier |
| **Approval Flows** | Inline manager-approval chains for license / access requests | 🟡 Demonstrated via the `PENDING_MANAGER_APPROVAL` mock state in `idp.provision_software`; production would need real approvals |
| **Multilingual** | 100+ languages out of the box | ❌ English-only prototype (would require translation in Intake and Knowledge prompts) |

### Technical Architecture (inferred from public materials)

```
┌─────────────────────────────────────────────────────────────────┐
│                       Moveworks Platform                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ Conversational   │  │ Triage Agent     │  │ Knowledge    │   │
│  │ Copilot UI       │  │ (intent + entity)│  │ Search       │   │
│  │ (Slack/Teams/Web)│  │                  │  │ (RAG)        │   │
│  └──────────────────┘  └──────────────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ MoveLM Router    │  │ Plug-in Engine   │  │ Approval     │   │
│  │ (multi-LLM mix)  │  │ (typed actions)  │  │ Flows        │   │
│  └──────────────────┘  └──────────────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│         100+ enterprise app integrations (ITSM, IDP, HRIS)      │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Opportunities for Our System

1. **Plug-in API as MCP server** — Moveworks exposes a REST API for triggering
   plug-ins. Wrap it as a single `mcp.moveworks_plugin` tool that the Workflow
   agent can call when the relevant Moveworks instance is configured. Useful
   for orgs who already invested in Moveworks' integration catalog.

2. **Knowledge sync** — Moveworks indexes Confluence/SharePoint/Drive natively.
   Re-using their pre-indexed content via their search API avoids us having to
   build connectors per source.

3. **Hybrid deployment** — Position our prototype as the open-source,
   self-hostable fallback for orgs that can't license Moveworks (sub-1000-
   employee companies, regulated industries with on-prem requirements).

### Pricing Model

- **Per-employee licensing**, ~$30–80/employee/year depending on volume and modules
- Typical floor: **$50K/year minimum contract** (publicly reported)
- Enterprise tier ($100K+) for >5K employees and custom plug-ins

### Strengths vs. Our Solution

| Moveworks Advantage | Our Advantage |
|---------------------|---------------|
| 100+ pre-built enterprise plug-ins | Open-source, fully self-hostable |
| Multi-channel native (Slack, Teams, mobile, email) | Zero per-seat cost |
| Production telemetry at scale (millions of users) | Code is auditable and modifiable |
| Multilingual out of the box | Pluggable LLM — swap OpenAI for Claude / local Llama |
| Approval flows + sophisticated entitlement model | MCP-aligned tool layer, swappable for any MCP server |

---

## 2. Glean

### Company Overview

- **Founded:** 2019 by Arvind Jain (ex-Google search, ex-Rubrik VP Engineering), T.R. Vishwanath, Tony Gentilcore, Piyush Prahladka
- **Headquarters:** Palo Alto, CA
- **Funding:** $615M+ raised across Series A–E (Kleiner Perkins, Sequoia, Lightspeed, General Catalyst, Citi Ventures)
- **Valuation:** ~$7.2B (mid-2024 Series E)
- **Customers:** Databricks, Confluent, Pinterest, Reddit, Sony, Plaid, Grammarly, Duolingo (~600+ enterprises)
- **Core Focus:** Enterprise-wide AI search + assistant grounded in a company's own data

### Key Features

| Feature | Description | Our Equivalent |
|---------|-------------|----------------|
| **Glean Search** | Universal natural-language search across 100+ enterprise apps with permission-aware results | 🟡 RAG over Chroma; single-source (markdown runbooks); needs connector framework for parity |
| **Glean Assistant** | RAG-grounded conversational assistant; cites every fact with a clickable source | ✅ Knowledge agent's grounded-answer pattern with `[1]`/`[2]` citations |
| **Glean Apps (custom GPTs)** | No-code workflow builder backed by Glean's index | 🟡 Closest analog: our Workflow agent, but ours is code-first |
| **Permission-aware retrieval** | Search results respect each source system's ACLs — users only see chunks they're allowed to read | ❌ Not implemented; runbooks are global |
| **Activity-based personalization** | Re-ranks results based on the user's recent documents, calendar, team | ❌ Out of scope for v1 |
| **Real-time indexing** | Sub-minute freshness for new Slack messages, Drive docs, Jira tickets | 🟡 We re-ingest manually via `scripts/ingest_kb.py` |
| **Glean Chat (workplace assistant)** | Combined search + chat surface in browser plugin | ✅ Streamlit chat surface at smaller scale |

### Technical Architecture (inferred from public materials)

```
┌─────────────────────────────────────────────────────────────────┐
│                          Glean Platform                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ Glean Assistant  │  │ Glean Search     │  │ Glean Apps   │   │
│  │ (chat interface) │  │ (universal Q&A)  │  │ (custom GPTs)│   │
│  └──────────────────┘  └──────────────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   Permission-aware retrieval + LLM grounding             │   │
│  │   Query understanding → retrieval → re-rank → cite       │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   Universal search index (vectors + keywords + ACLs)     │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│       100+ source connectors (Drive, Slack, Confluence,         │
│       GitHub, Salesforce, Jira, Notion, OneDrive, etc.)         │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Opportunities for Our System

1. **Glean as a retrieval backend.** Replace our local Chroma + markdown
   runbooks with Glean's search API as the source for the Knowledge agent.
   `src/rag/retriever.py.retrieve()` becomes a thin wrapper over a single
   Glean Search API call — the agent code doesn't change. The win:
   permission-aware results, real-time indexing, hundreds of source systems
   without us writing connectors.

2. **Glean Apps for the Workflow agent.** Customers who already built
   Glean Apps for their own internal workflows can register them as MCP tools
   in our registry, exposing them to the Workflow agent.

3. **Hybrid deployment.** Run our agentic orchestration layer on top of
   Glean's search/index for retrieval, and our own MCP tool layer for action
   execution. Gives the customer Glean's depth of search with our framework's
   action-execution flexibility.

### Pricing Model

- **Per-user/month**, typically **$30–50/user/month** for enterprise tier
- Volume discounts at >5K seats
- Glean Apps included; Glean Assistant requires an additional add-on for some plans

### Strengths vs. Our Solution

| Glean Advantage | Our Advantage |
|-----------------|---------------|
| 100+ source connectors out of the box | No per-user cost; scales by infra spend, not headcount |
| Permission-aware retrieval (compliance-grade) | Self-hostable; sensitive runbooks never leave your infra |
| Real-time index freshness | Code is reviewable in PRs; runbooks are markdown files |
| Universal search beats single-source RAG | Designed around action execution, not just search |
| Mature enterprise admin & analytics console | Uniform MCP tool interface — drop in real MCP servers any time |

---

## Side-by-Side: Moveworks, Glean, and Us

| Dimension | Moveworks | Glean | This Project |
|---|---|---|---|
| Primary surface | Slack/Teams Copilot | Web chat + browser plugin | Streamlit ticket form |
| Core capability | Action automation | Enterprise search | Multi-agent orchestration (both, scaled down) |
| LLM strategy | Multi-LLM "MoveLM" router | Vendor-flexible (OpenAI, Anthropic, Google) | OpenAI gpt-4o-mini, swap-friendly |
| Vector store | Proprietary | Proprietary (vector + keyword hybrid) | Chroma (local) |
| Tool/action layer | 100+ proprietary plug-ins | Glean Apps + REST hooks | MCP-shaped registry, real Jira + mock IDP/catalog/logs |
| Permission model | Source-system ACLs | Source-system ACLs (sophisticated) | Single global runbook visibility |
| Pricing | $50K+/yr enterprise contracts | $30-50/user/month | Self-hosted; OpenAI + Jira API costs only |
| Source code | Closed | Closed | Open (this repo) |
| Time to deploy | Weeks (with vendor implementation team) | Days | < 5 minutes |

---

## Key Differentiators of Our Solution

### 1. MCP-native tool layer

Neither Moveworks nor Glean has publicly committed to the Model Context
Protocol as their tool integration standard. By building our action layer
around MCP from day one, we can drop in any MCP server (the Atlassian MCP
server, the GitHub MCP server, custom company servers) without touching agent
code. This positions the project as a reference implementation for an
emerging open standard.

### 2. Open and forkable

Every classification rule, retrieval prompt, and routing decision lives in
plain Python files reviewable in pull requests. Compliance teams can audit
exactly what the AI does on their behalf — neither vendor offers this.

### 3. Pluggable at every layer

LLM (`src/llm.py`), embeddings (same file), vector store (`src/rag/`),
tool registry (`src/mcp/`) — each is fronted by a thin interface. Swapping
OpenAI for Claude, or Chroma for Pinecone, is a one-file change. Vendors
trade flexibility here for ease of deployment.

### 4. Cost ceiling

Per-conversation cost is bounded by OpenAI API pricing (~$0.001–$0.005 per
turn at current rates). Vendors charge per seat regardless of usage, so a
3000-employee org pays the same whether they get 10 or 10,000 questions/month.

---

## Recommendations

### Short-term integration

1. **Add a Glean Search MCP tool.** A single tool entry in `src/mcp/client.py`
   that calls `POST /api/v1/search` against a configured Glean instance. The
   Knowledge agent can then choose between local runbooks and Glean's index
   per query.
2. **Add a Moveworks plug-in MCP tool.** Same pattern — wraps Moveworks'
   Plug-in Trigger API. Workflow agent fires it when the org has Moveworks
   licensed for the underlying system.
3. **Expose our system as an MCP server itself.** A trivial wrapper turns the
   four agents into an MCP-callable service that Glean Apps or Moveworks
   plug-ins can invoke. Bidirectional integration.

### Long-term strategy

1. **Position as the AI orchestration layer for existing ITSM investments.**
   Don't compete with Moveworks/Glean on integrations or scale — compete on
   transparency, cost, and being the layer that ties them together.
2. **Build a marketplace of MCP tool integrations.** Community-contributed
   tool implementations (Salesforce MCP, Workday MCP, Greenhouse MCP) become
   the project's competitive moat as the MCP ecosystem matures.
3. **Hybrid mode.** Document and test deployment patterns where this project
   acts as the orchestration brain on top of Glean (for retrieval) and
   Moveworks (for some actions), letting customers leverage their existing
   licenses without lock-in.

---

## References

1. Moveworks Documentation: https://www.moveworks.com/us/en/resources/docs
2. Moveworks Engineering Blog: https://www.moveworks.com/us/en/resources/blog
3. ServiceNow's announcement of the Moveworks acquisition (March 2025)
4. Glean Documentation: https://help.glean.com/
5. Glean Engineering Blog: https://www.glean.com/blog
6. Forrester Wave: AI-Powered Knowledge Discovery Solutions (2024)
7. Gartner Hype Cycle for the Digital Workplace (2024)
8. Model Context Protocol specification: https://modelcontextprotocol.io/
