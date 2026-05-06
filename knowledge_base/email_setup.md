# Email Setup

This runbook covers email signatures, forwarding rules, out-of-office
configuration, and distribution-list management. We use Microsoft 365 / Outlook
as the corporate email platform.

## Email signatures

Required signature format for all employees:

```
Your Name
Your Title  |  Department
Company Name
```

Optional additions (kept short — don't add quotes, images, or social links):
- Pronouns
- Office location
- Calendly / scheduling link

### Setting your signature in Outlook (web)

1. Open Outlook web (`outlook.office.com`).
2. Settings (gear icon, top right) → "View all Outlook settings" → Mail →
   Compose and reply.
3. In the Email signature section, paste your signature using the format above.
4. Check both "Automatically include my signature on new messages" and
   "Automatically include my signature on messages I forward or reply to".
5. Save.

### Setting your signature in Outlook (desktop)

1. File → Options → Mail → Signatures.
2. Click New, name it "Default", paste the signature.
3. Set as default for both New messages and Replies/forwards.
4. OK.

### Setting your signature in Apple Mail

Apple Mail isn't supported for corporate accounts. Use Outlook desktop or web.

## Email forwarding

### Forwarding to another corporate address

Allowed without restriction. Common for managers covering for direct reports
during PTO, or for shared-team mailboxes.

1. Outlook web → Settings → Mail → Forwarding.
2. Enable "Enable forwarding".
3. Enter the target `@company.com` address.
4. Choose whether to keep a copy in your inbox (recommended).
5. Save.

### Forwarding to a personal address — NOT PERMITTED

Forwarding company email to personal addresses (Gmail, Yahoo, iCloud, Outlook.com,
etc.) is **not permitted** under our data-handling policy. This is a hard rule
because:
- Personal accounts aren't covered by our data-loss-prevention scanning.
- Personal accounts often have weaker MFA than our corporate setup.
- We can't legally hold messages for litigation if they leave our environment.

The mail server enforces this — attempts to set up personal-address forwarding
will silently fail, and the security team will get an alert.

If you have a legitimate need to access work email from a personal device,
install the Outlook mobile app and sign in with SSO. The app keeps your data
in a managed container.

### Forwarding rules (filters)

Outlook's Rules feature lets you forward specific messages (e.g., notifications
from a system to a team channel). The same restrictions apply — destinations
must be `@company.com`.

## Out-of-office (OOO)

1. Outlook web → Settings → Mail → Automatic replies.
2. Toggle "Automatic replies on".
3. Set start and end dates.
4. Write the OOO message. Recommended template:

   > I'm out of office from [start] to [end] and will respond when I return.
   > For urgent matters, contact [coverage person] at [coverage@company.com].

5. Choose whether to send replies to people outside the organization (default
   is on; turn off if you communicate with sensitive external parties).
6. Save.

### Delegating your inbox during OOO

If you need someone to manage your inbox while you're out (vs. just auto-replying):

1. Outlook web → Settings → Mail → Sync email → Manage delegates.
2. Add the delegate by email address.
3. Choose access level:
   - **Inbox only** — can read and reply
   - **Full mailbox** — can also see calendar, contacts, sent items
4. Save.

Delegates can send messages on your behalf — they appear with "Sent on behalf
of [your name]". Choose carefully and remove access when no longer needed.

## Distribution lists

You can be added to / removed from distribution lists through the IT Support
Copilot — see `access_requests.md` for the eligibility matrix.

To create a new distribution list:
1. Open the Copilot.
2. Say: *"Create a distribution list for the Q3 launch team."*
3. The Copilot creates a Jira ticket assigned to IT (we don't auto-create lists
   to avoid sprawl).
4. Approval comes back within 1 business day. The list will be named
   `project-q3-launch@company.com`.

## Common issues

### "I'm not receiving emails from external senders"

Check the Junk folder first. If not there:
1. Outlook web → Settings → Mail → Junk email → Safe senders. Add the sender's
   domain.
2. Some marketing emails are blocked at the gateway. If the email is from a
   legitimate vendor, escalate — IT can whitelist the sender.
3. If you're missing emails from a specific colleague, check whether you have a
   blocking rule (Settings → Mail → Rules).

### "My signature has weird formatting / extra characters"

Outlook web's rich-text editor doesn't handle pasted formatting well. Best
approach:
1. Type the signature plain in TextEdit / Notepad.
2. Paste into Outlook's signature editor.
3. Apply formatting (bold, italics) inside Outlook.

### "I want to send mail as a shared mailbox (e.g., support@)"

You need delegate access first — see "Delegating your inbox" but in reverse
(the mailbox owner adds you). Then in Outlook, when composing, click "From" and
select the shared address.
