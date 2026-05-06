# Success Metrics

These metrics drive the post-pilot review and any "ship it / kill it" decision.
The four-bucket framing — **resolution**, **quality**, **speed**, **satisfaction** —
maps to what end users, IT engineers, and management each care about.

## 1. Resolution

| Metric | Target | Source |
|---|---|---|
| **Deflection rate** | ≥ 60% of in-scope requests resolved without a human IT engineer | `final_answer` set by Knowledge or Workflow agent (not Escalation) ÷ total conversations |
| **First-time-fix rate** | ≥ 90% of auto-resolved tickets have no follow-up message from the user within 24h | Conversation continuation tracking |
| **Escalation rate** | ≤ 40% (inverse of deflection) | Count of Escalation-agent terminations |
| **False-escalation rate** | ≤ 10% — tickets escalated that the engineer marks "I would have wanted the bot to handle this" | Engineer triage tag in Jira |

## 2. Quality

| Metric | Target | Source |
|---|---|---|
| **Triage accuracy** | ≥ 85% on `request_type` + `category` against gold set | `tests/eval_metrics.py` against `tests/gold_set.json` |
| **Hallucination rate (Knowledge)** | ≤ 5% — answers containing claims not present in retrieved context | Manual review of 50 Knowledge-agent answers per week |
| **Citation correctness** | 100% — every cited chunk actually appears in `retrieved_docs` | Automated check during scenario tests |
| **Workflow correctness** | 100% — actions executed match the planned action list | Audit log compare against `state.actions` |
| **Escalation summary completeness** | ≥ 90% on a 4-point rubric: (a) original request, (b) automation steps taken, (c) diagnostic data attached, (d) suggested next steps | Manual review of 20 escalations per week |

## 3. Speed

| Metric | Target | Source |
|---|---|---|
| **First-response latency** | p50 < 4s, p95 < 10s | Wall-clock around `app.invoke()`, recorded into `state.trace` |
| **Per-agent latency** | Intake p95 < 1.5s, Knowledge p95 < 4s, Workflow p95 < 5s, Escalation p95 < 4s | `TraceEvent.duration_ms` |
| **End-to-end latency** | p95 < 10s for any single-agent path; p95 < 15s for chained paths | Sum of `TraceEvent.duration_ms` |

## 4. Satisfaction

| Metric | Target | Source |
|---|---|---|
| **Post-resolution thumbs** | ≥ 4.0 / 5 average (👍 = 5, 👎 = 1) | UI feedback widget |
| **Repeat usage** | ≥ 30% of pilot users return within 7 days | Distinct `user_id` count over rolling 7-day window |
| **NPS (quarterly survey)** | ≥ 30 | Out-of-band survey after 90 days |

## Reporting cadence

- **Live dashboard:** deflection rate, p95 latency, satisfaction average — refreshed every conversation
- **Weekly:** all of the above + manual sample of 20 escalations and 50 informational answers for quality scoring
- **Monthly:** breakdown by category (software_license, hardware, access, email, printer, av) — surfaces categories where the bot is weak so we can extend the runbooks or tighten the workflow planner
- **Quarterly:** NPS survey + decision review (expand scope / hold / sunset)

## How `tests/eval_metrics.py` connects

`tests/eval_metrics.py` runs the full graph against `tests/gold_set.json` (a hand-labeled
set of 25 representative requests across all in-scope categories). It reports:

- Triage accuracy (per-field and overall)
- Per-conversation latency
- Whether the expected `final_answer_kind` (informational / action_completed /
  escalated) was reached

It is the regression gate before any change to agent prompts or routing logic.
