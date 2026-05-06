# Software Licenses

This runbook covers how to request and manage software licenses for company-approved
applications. The IT team manages license inventory through Okta and the corporate
software catalog.

## Approved software catalog

The following applications can be self-requested through the IT Support Copilot or
the IT portal. Most provision automatically within 5 minutes; some require manager
approval first.

| Software | License type | Cost center | Auto-approve? | Notes |
|---|---|---|---|---|
| Figma | Professional | Design | No — manager approval | Designers and PMs eligible |
| FigJam | Standalone | Design | Yes | Anyone can request |
| JetBrains All Products | Per-seat | Engineering | No — manager approval | Engineers only |
| Adobe Creative Cloud | Full suite | Marketing/Design | No — manager approval | $80/seat/mo, requires VP signoff |
| Adobe Acrobat Pro | Standalone | Any | Yes | Common — bulk-licensed |
| Notion | Plus | Any | Yes | Default workspace tier |
| Linear | Standard | Engineering/Product | Yes | |
| Loom | Business | Any | Yes | |
| 1Password | Business | Any | Yes | Required for all employees handling credentials |
| Tableau | Creator | Data/Analytics | No — manager approval | $70/seat/mo |
| Zoom | Pro | Any | Yes | Default tier; webinar add-on requires approval |
| Slack | Business+ | All | N/A | Provisioned at hire |

## How to request a license

1. Open the IT Support Copilot (Slack `/it` or web portal).
2. State the software name and your reason. Example: *"I need a Figma license to
   collaborate on the Q3 design review."*
3. The system will:
   - Verify the software is in the approved catalog.
   - Check whether your role/department is eligible.
   - For auto-approve items: provision immediately and create a tracking ticket.
   - For approval-required items: route to your manager via Slack, then provision
     when approved.
4. Once provisioned, the app appears in your Okta dashboard within 5 minutes. Sign
   in using your corporate email — do not create a separate account with the same email.

## Self-service deactivation

If you no longer need a license (e.g., role change, leaving a project), deactivate
it to free up the seat:

1. Open the IT Support Copilot.
2. Say: *"Remove my [software name] license."*
3. The system will revoke access and release the seat.

## Software not in the catalog

If you need software that isn't listed:

1. Submit a request via the Copilot stating the software, vendor, and business
   justification.
2. The system will create a Jira ticket routed to the IT Procurement queue.
3. Procurement reviews vendor terms (data handling, SSO support, security review)
   and responds within 5 business days.
4. Do not download or install paid software using a personal payment method and
   expect reimbursement — this is against finance policy.

## Common issues

### "I requested Figma but it's not in my Okta dashboard"

Wait 10 minutes. If still missing:
- Check spam — Okta sends an enrollment email
- Check the Jira ticket the Copilot created; it will show provisioning status
- If status is "Pending Manager Approval", ping your manager

### "I have a license but the app says my account is over the seat limit"

This usually means a license was assigned but the vendor-side sync hasn't
completed. Sign out completely, wait 5 minutes, sign back in via SSO. If still
broken, escalate.

### "I need a personal license for [X] for personal projects"

The IT team only manages corporate licenses. Personal licenses are your
responsibility and cannot be expensed.
