# UX Wireframes

The interaction surface is a single chat panel with a collapsible "Agent trace"
sidebar. Three states cover ~95% of conversations: **answered from runbook**,
**action completed**, and **escalated**. Each shows different supporting affordances
so the user knows what just happened on their behalf.

## Design principles for the chat surface

1. **Show what the agents did, but don't make the user read it.** The trace lives
   in a collapsed sidebar by default; the chat reply is a single short paragraph.
2. **Always surface the ticket ID.** Whether the system auto-resolved or escalated,
   the user gets a ticket they can reference. This builds trust ("the system did
   this on my behalf and I have a paper trail").
3. **One-click feedback.** A 👍 / 👎 next to the final answer feeds the
   satisfaction metric. No modal, no required text.
4. **Citations are clickable in informational answers.** Each retrieved doc
   appears as a numbered chip the user can expand to see the runbook snippet.

## State 1 — informational answer (Knowledge agent)

```
┌────────────────────────────────────────────────────────┬──────────────────────┐
│  IT Support Copilot                          [👤 Rosa]  │  Agent Trace      ▾ │
├────────────────────────────────────────────────────────┤                      │
│                                                        │  ✓ Intake (0.4s)    │
│  You                                                   │    informational    │
│  How do I set up email forwarding to my personal       │    email (high conf) │
│  account?                                              │                      │
│                                                        │  ✓ Knowledge (1.8s) │
│  IT Copilot                                            │    5 chunks from    │
│  Forwarding company email to personal addresses isn't  │    email_setup.md   │
│  permitted under our data-handling policy. You can     │                      │
│  set forwarding to *another corporate address* (e.g.,  │                      │
│  during a leave) by going to Outlook → File → Manage  │                      │
│  Rules → Forwarding…                                   │                      │
│                                                        │                      │
│  Sources:                                              │                      │
│  [1] email_setup.md – §Forwarding rules                │                      │
│  [2] email_setup.md – §Out-of-office and delegation    │                      │
│                                                        │                      │
│  Was this helpful?  👍  👎                             │                      │
│                                                        │                      │
├────────────────────────────────────────────────────────┤                      │
│  Type a message…                                  [↵]  │                      │
└────────────────────────────────────────────────────────┴──────────────────────┘
```

## State 2 — action completed (Workflow agent)

```
┌────────────────────────────────────────────────────────┬──────────────────────┐
│  IT Support Copilot                                     │  Agent Trace      ▾ │
├────────────────────────────────────────────────────────┤                      │
│  You                                                   │  ✓ Intake (0.4s)    │
│  I need a Figma license for design work                │    action           │
│                                                        │    software_license │
│  IT Copilot                                            │                      │
│  Done — I've assigned you a Figma Professional license. │  ✓ Workflow (2.1s)  │
│  You should see Figma in your SSO dashboard within a   │    1. catalog.lookup│
│  few minutes. Sign in with your work email.            │       _hardware OK  │
│                                                        │    2. idp.provision │
│  Tracked under ticket [IT-128].                        │       _software OK  │
│                                                        │    3. jira.create   │
│  Was this helpful?  👍  👎                             │       _ticket OK    │
│                                                        │                      │
└────────────────────────────────────────────────────────┴──────────────────────┘
```

## State 3 — escalated to a human

```
┌────────────────────────────────────────────────────────┬──────────────────────┐
│  IT Support Copilot                                     │  Agent Trace      ▾ │
├────────────────────────────────────────────────────────┤                      │
│  You                                                   │  ✓ Intake (0.4s)    │
│  Conference Room B projector shows "no signal" and I   │    incident, av,    │
│  have a demo in 10 minutes                             │    severity=high    │
│                                                        │                      │
│  IT Copilot                                            │  ✓ Workflow (1.2s)  │
│  I've flagged this to the on-call IT engineer with     │    logs.get_recent  │
│  full context (recent A/V log events, room, timing).   │    OK – 4 events    │
│                                                        │                      │
│  Tracking ticket: [IT-129] — high priority             │  ✓ Escalation (1.5s)│
│                                                        │    jira.create_     │
│  In the meantime: try unplugging and reseating the     │       incident OK   │
│  HDMI cable on the desk-side input. The runbook says   │                      │
│  this resolves ~40% of "no signal" cases.              │                      │
│                                                        │                      │
└────────────────────────────────────────────────────────┴──────────────────────┘
```

## Sidebar — expanded "Agent Trace"

```
Agent Trace                                                 ▴
─────────────────────────────────────────────────────────────
▸ Intake                                              0.4s
    request_type:  incident
    category:      av
    system:        Conference Room B
    severity:      high
    confidence:    0.91
    entities:      {room: "Conference Room B",
                    issue: "no signal",
                    deadline_minutes: 10}

▸ Workflow                                            1.2s
    action 1: logs.get_recent(service="av", room="ConfB", hours=2)
        → SUCCESS, 4 events returned

▸ Escalation                                          1.5s
    summary: "User reports projector showing 'no signal' in Conf
              Room B with demo in 10 min. Recent A/V logs show
              HDMI handshake failures at 14:52, 14:55, 14:58…"
    action: jira.create_incident(severity="high")
        → SUCCESS, ticket IT-129 created
─────────────────────────────────────────────────────────────
Total: 3.1s · 3 agents · 2 tool calls
```

## Why these affordances

- **Latency labels per agent** (0.4s, 1.2s, etc.) make slowness debuggable. If the
  system feels slow, you can see *which* agent is the bottleneck.
- **Trace is collapsed by default** because most users don't care; it's there for
  the IT team auditing what the system does on users' behalf, and for grading the
  capstone.
- **The 👍/👎 sits right under the final answer** — no extra page, no required
  comment. This maximizes the satisfaction-metric capture rate.
- **Ticket ID is always present and link-styled** even though we don't render it
  as a real link in the prototype. In a real deployment this would deep-link into
  the user's own Jira ticket so they can comment / add screenshots / cancel.
