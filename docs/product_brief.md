# Product Brief — IT Support Copilot

## Problem statement

Mid-size companies (200–2000 employees) run IT helpdesks that drown in repetitive,
low-complexity tickets. A typical week's queue is dominated by:

- Software license requests (Figma, JetBrains, Adobe, etc.)
- Hardware requests and replacements (laptops, monitors, peripherals)
- Access requests (mailing lists, shared drives, Slack channels)
- New-hire setup walkthroughs
- "How do I…" questions answered by existing runbooks
- Conference room A/V issues 10 minutes before a meeting

The first four are **action requests** with deterministic workflows. The fifth is
**informational** and answerable from existing documentation. The sixth is an
**incident** where speed and context handoff matter most. Today, all of them get
the same human-triaged treatment, which costs ~10 minutes of a Tier-1 agent's time
each, and pushes resolution time for the genuinely hard tickets to the back of the queue.

## Target users

| Persona | Frequency | What they want |
|---|---|---|
| End user (employee) | Daily | A self-service answer or action that completes in under a minute, without learning the IT portal's taxonomy. |
| Tier-1 IT agent | Continuous | Their queue filtered down to tickets that genuinely need a human; rich context attached when they do. |
| IT manager | Weekly review | Auditable trail of automated actions, per-category resolution metrics, deflection rate. |

## Use cases (in scope for v1)

1. **Software license provisioning** — `"I need a Figma license"` → look up the
   software catalog, provision via mock IDP, open a Jira ticket as the audit record.
2. **Hardware request** — `"My laptop battery dies after 30 minutes"` → look up
   the user's office, place a catalog order, create a Jira ticket with shipping/pickup info.
3. **Access request** — `"Add me to the #data-platform Slack channel"` → look up
   the channel, run the membership-grant tool, confirm.
4. **Informational query** — `"How do I set up email forwarding to my personal account?"`
   → RAG retrieval over the email-setup runbook, answer with citations. (And: catch
   policy violations like forwarding to non-corporate addresses.)
5. **New-hire onboarding** — `"I just started, what do I need to set up?"` →
   retrieve the new-hire runbook, present a personalized checklist.
6. **Printer setup** — `"How do I add the 3rd-floor color printer?"` → RAG.
7. **Conference room A/V incident** — `"Conference Room B projector shows 'no signal'
   and I have a demo in 10 minutes"` → fetch recent A/V logs, escalate to on-call IT
   with full context (room, time, recent log events, user).

## Out of scope (v1)

- Anything requiring physical access (badge issues, locked-out-of-office)
- Security incidents (account compromise, phishing reports) — too high stakes for
  a v1 prototype to handle without human review at every step
- HR/payroll/benefits questions — different ownership and access model

## Success metrics

| Metric | Target | How measured |
|---|---|---|
| **Deflection rate** — % of incoming requests resolved without a human IT agent | ≥ 60% across in-scope categories | Count of conversations where `final_answer` set by Knowledge or Workflow agent (not Escalation) ÷ total |
| **Triage accuracy** — % of requests where intent + system + severity match a hand-labeled gold set | ≥ 85% | Run `tests/eval_metrics.py` against `tests/gold_set.json`; agreement scored against expected fields |
| **First-response latency** — time from user message to first agent reply | p50 < 4 s, p95 < 10 s | Wall-clock around `app.invoke()`; recorded into `state.trace` |
| **Escalation quality** — when a ticket *is* escalated, the human-readable summary covers (a) user's original request, (b) automation steps already taken, (c) relevant log/diagnostic data, (d) suggested next steps | ≥ 90% on a 4-point rubric | Sample 20 escalations/week, manually score |
| **User satisfaction** | ≥ 4.0 / 5 | Post-resolution thumbs / 1–5 prompt in the chat UI |
| **Hallucination rate (Knowledge agent)** — answers containing claims not supported by retrieved context | ≤ 5% | Sample 50 informational answers/week, manually verify against citations |

## Design principles

1. **Always cite sources for informational answers.** The Knowledge agent attaches
   the runbook chunks it used. If retrieval returns nothing relevant, the agent says
   "I don't know" and routes to escalation rather than hallucinating.
2. **Every automated action creates an audit record.** The Workflow agent always
   opens a Jira ticket alongside the IDP/catalog call so a human can review what
   the system did on their behalf.
3. **Escalate with full context, not just the original message.** When the
   Escalation agent fires, it sends the human everything the system already learned —
   intent classification, retrieved docs, tool results — so the engineer doesn't
   start from zero.
4. **Make the model swap-able.** All LLM calls go through `src/llm.py`; switching
   from `gpt-4o-mini` to a local Llama model shouldn't require touching agent code.
5. **Treat the tool layer as MCP-shaped.** Even though v1 ships a local registry,
   the call signature mirrors MCP so that real MCP servers (e.g., Atlassian's MCP
   server, GitHub MCP server) drop in later without changing agent logic.
