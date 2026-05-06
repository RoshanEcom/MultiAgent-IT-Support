# New Hire Setup

Welcome! This runbook covers everything a new hire needs to set up in their first
week. The IT Support Copilot can walk you through any of these steps — just ask.

## Day 1 (in-person or remote)

You should receive these on Day 1:
- Laptop (Mac or Windows depending on role)
- Power adapter, USB-C dock, basic peripherals (mouse, headset)
- Welcome packet with your `@company.com` email and Okta enrollment link

If anything is missing, message the Copilot: *"I started today and didn't receive
my [item]"*. The system will check the shipping/inventory record and either
provide a status or open a high-priority ticket.

### First boot checklist

1. **Power on and connect to office WiFi** (`CompanyCorp` for laptops; SSID
   `Guest` for personal devices, password posted in conference rooms).
2. **Sign in with your corporate email** at the OS login prompt. This binds the
   device to Jamf (Mac) or Intune (Windows) for management.
3. **Complete Okta enrollment** — the welcome email has a one-time link. You'll
   set a password and configure MFA (Okta Verify push is preferred; SMS is
   deprecated for new hires).
4. **Install Slack and sign in** at `company.slack.com` with your corporate
   email. Join `#new-hires-{cohort-month}` and `#it-help`.
5. **Install Zoom** from the Self Service app (Mac) or Company Portal (Windows).
   Sign in with SSO.
6. **Verify email in Outlook / Gmail.** Your manager will have already set you
   up on the team mailing list.

## Day 1 — by department

Beyond the universal day-1 setup, ask the Copilot to provision:

| Department | Standard tooling provisioned |
|---|---|
| Engineering | GitHub (eng-everyone team), JetBrains, Linear, Datadog (read) |
| Product | Linear, Notion, Figma, Productboard |
| Design | Figma Pro, FigJam, Adobe CC |
| Sales | Salesforce, Outreach, Gong, ZoomInfo |
| Marketing | HubSpot, Adobe CC, Canva, Asana |
| Finance | NetSuite, Expensify, Concur |
| People Ops | Workday, Greenhouse, Lever |

The Copilot uses the role/department on file in Workday to auto-provision. If
something is missing, ask: *"I'm a new PM and I don't have a Linear license yet."*

## Week 1 checklist

- [ ] Day-1 setup complete (above)
- [ ] MFA configured with at least two methods (push + backup codes)
- [ ] 1Password installed and signed in (everyone needs this — for credential
      sharing within teams)
- [ ] Calendar set up with working hours and time zone
- [ ] Email signature configured (see `email_setup.md`)
- [ ] Joined relevant team Slack channels (your manager will share a list)
- [ ] Completed mandatory security training (link sent by People Ops)
- [ ] Met with your IT buddy (if assigned for your office)

## Common issues for new hires

### "I never got my Okta enrollment email"

Check spam first. If still missing:
1. Tell the Copilot: *"I started today, didn't get Okta enrollment."*
2. The system verifies your hire record in Workday and re-sends the link.
3. If you're not in Workday yet, the system escalates to People Ops.

### "My laptop won't enroll in Jamf/Intune"

Usually a network issue. Try:
1. Switch from `CompanyCorp` WiFi to your phone's hotspot for the initial
   enrollment.
2. Restart and re-attempt.
3. If still failing, escalate — the device may need to be re-prepped.

### "I see the wrong job title in our directory"

Job title comes from Workday. The IT Copilot can't change it directly — open
a ticket with People Ops and they'll update Workday, which syncs to the
directory within 24h.

### "What if I forget my password before Okta is set up?"

Day-1 password resets must be done by IT in person or via verified video call.
Message the Copilot — it will route to the on-call IT person who will verify
your identity through your manager.
