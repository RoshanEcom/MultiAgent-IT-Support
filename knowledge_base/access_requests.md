# Access Requests

This runbook covers requesting access to Slack channels, mailing lists, shared
drives, GitHub repositories, and internal tools. Most access can be granted
automatically through Okta group membership; some requires data-owner approval.

## Slack channels

### Public channels
You can join any public channel directly in Slack — no IT request needed. Type
`/join #channel-name`.

### Private channels
1. Open the IT Support Copilot.
2. Say: *"Add me to the #data-platform Slack channel for the Q3 migration project."*
3. The system will:
   - Look up the channel owner.
   - For owner-managed channels: route a request to the owner via Slack.
   - For Okta-managed channels: add you immediately and confirm.
4. Some channels (e.g., `#exec-staff`, `#legal-confidential`) require VP approval
   regardless of method.

## Mailing lists / Google Groups

| Group pattern | Auto-join? | Notes |
|---|---|---|
| `team-*@company.com` | Manager approval | One per team |
| `project-*@company.com` | Project lead approval | Time-bounded |
| `announce-*@company.com` | Yes | Announcement-only, low traffic |
| `social-*@company.com` | Yes | Hobby groups |
| `oncall-*@company.com` | Engineering manager approval | Pages on rotation |

To request: *"Add me to project-payments-q3 mailing list."*

## Shared drives (Google Drive)

Drives are organized by department. Cross-department access requires the data
owner's approval.

| Drive | Default access | Request via |
|---|---|---|
| `[Department] - Public` | All-hands | Auto |
| `[Department] - Internal` | Department members | Manager approval |
| `[Department] - Confidential` | Named members only | Data owner approval |
| `Finance - Books` | Finance team only | CFO approval |
| `Legal - Contracts` | Legal team only | GC approval |
| `HR - Personnel files` | HR + named managers | CHRO approval |

Request via the Copilot: *"I need access to the Finance - Q3 Forecast drive."*
Be specific about which folder and why — vague requests get bounced.

## GitHub repositories

GitHub access is managed through the `engineering-*` Okta groups. Most engineering
repos are visible to all employees in the `eng-everyone` team (read access).
Write access requires:
- Membership in the team that owns the repo, OR
- Explicit add by a CODEOWNER

To request: *"I need write access to the payments-api repo for the on-call rotation."*

The system will:
1. Look up the repo's CODEOWNERS file.
2. Open a Jira ticket assigned to the appropriate team lead.
3. Add you to the repo's GitHub team after approval.

## Production systems (datadog, snowflake, AWS, etc.)

Production-system access is **never** auto-provisioned. All requests:
1. Require manager approval.
2. Require security-team review.
3. Are logged and audited quarterly.
4. Are time-bounded by default (90 days for read, 30 days for write).

Process: open the Copilot, describe what you need access to and why. The system
will create an `IT-SECURITY` ticket and route through the standard approval flow.
Expect 2-3 business days.

## Removing access

When you change roles or no longer need access:
- Tell the Copilot: *"Remove my access to [system/group/drive]."*
- Or, your manager can request bulk removal during a role change.
- HR triggers automatic removal of all access on your last day at the company.

## Common issues

### "I was added to the group but I still can't see the docs"

Group membership propagates through Okta → Google Workspace within 15 minutes.
Sign out of Google completely, sign back in. If still broken after 30 minutes,
escalate.

### "I need access urgently and the data owner is on PTO"

Out-of-office approvals can be escalated to the data owner's manager via the
Copilot. State the urgency (e.g., "production incident", "time-sensitive deal").
The system will route appropriately.

### "I keep getting permission-denied errors but the IT system says I have access"

This is usually a session/cookie issue. Try:
1. Sign out and sign back in to the affected service.
2. Clear cookies for the service's domain.
3. Try in a private/incognito window.

If the error persists, escalate with the exact error message and a screenshot.
