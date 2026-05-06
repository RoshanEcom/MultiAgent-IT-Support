# Password Reset and Account Lockout

This runbook covers what to do when you can't sign in: forgotten password,
account locked, MFA not working, or temporary password expired. Most cases
self-resolve in under five minutes through Okta's self-service flow.

## Self-service password reset (most common)

Use this when you know your username but forgot your password.

1. Go to **https://company.okta.com**
2. On the sign-in page, click **"Need help signing in?"** (under the password
   field), then **"Forgot password?"**.
3. Enter your corporate email (`firstname.lastname@company.com`).
4. Choose how you want to verify your identity:
   - **Okta Verify push** (recommended) — approve the prompt on your phone
   - **SMS** — receive a 6-digit code (deprecated for new hires; works for
     existing accounts)
   - **Security question** — answer the question you set during onboarding
5. After verifying, set a new password. Requirements:
   - At least 12 characters
   - At least one uppercase, one lowercase, one digit, one symbol
   - Cannot match any of your last 5 passwords
6. Sign in with your new password. SSO will propagate to all apps within
   5 minutes.

## Account locked (too many failed attempts)

After 5 wrong password attempts, Okta locks the account for **30 minutes**.

- **If you can wait:** the lock auto-clears after 30 minutes. Try again then.
- **If you can't wait** (e.g., interview in 15 minutes, customer call): open
  the IT Support Copilot. Tell it you're locked out and time-pressured. The
  Copilot can request an immediate unlock from IT.

While waiting, **do not** keep retrying — that resets the 30-minute timer.

## MFA device lost or not working

If you lost your phone or it broke and you can't approve push notifications:

1. Use a **backup method** if you set one up at enrollment:
   - 6-digit codes from a recovery sheet (PDF you saved)
   - SMS to your registered phone (only if your number still works)
2. If no backup method works: contact the IT Copilot. You'll need to verify
   your identity through your manager via Slack DM or live video call before
   IT can reset MFA. Plan for ~15 minutes minimum.

## Temporary password expired

When IT (or the Copilot's `idp.reset_password` automation) issues a temporary
password, it's valid for **24 hours** and must be changed at first sign-in.
If it expired:

1. Contact the IT Copilot to request a new temporary password.
2. The system will verify your identity (Slack/Workday match) and issue a
   fresh temporary credential.

## Suspicious activity / suspected account compromise

If you got an alert about an unfamiliar sign-in location, or you suspect
someone else has your password:

1. **Do not** try to fix it yourself. Don't change your password yet.
2. Contact IT immediately via the Copilot. State: *"I think my account is
   compromised."* This is treated as a security incident and routed to the
   on-call security engineer, not a regular IT ticket.
3. While waiting, do not access sensitive systems or open links from any
   email that looks suspicious.

## What if Okta's self-service doesn't work

These are the most common reasons self-service fails — and what to try next.

| Symptom | Likely cause | What to do |
|---|---|---|
| "We don't recognize this email" | Account doesn't exist yet, or wrong email | Verify the spelling. New hires: your account is created on your first day, not before. |
| "Verification failed" with Okta Verify | Phone offline / app not installed | Switch to SMS if available, or contact IT. |
| New password rejected | Doesn't meet complexity, or matches a past password | Try a longer password with more variety; avoid reusing anything from the last 5. |
| Page hangs or 500 error | Okta service incident | Check status.okta.com. If Okta is down, IT cannot bypass it. Wait. |
| Reset succeeded but apps still rejecting | SSO sync delay | Wait 5 minutes, sign out completely, sign back in. |
| Locked out repeatedly even with correct password | Stale session in another device | Sign out everywhere from Okta dashboard → Settings → Sign out other sessions. |

If you've tried the relevant fix above and it still doesn't work, that's the
moment to escalate to IT. The Copilot will create a high-priority ticket and
attach what you've already tried.

## What IT can and can't do

| Request | IT can help? | Notes |
|---|---|---|
| Force-unlock your account before 30 min | Yes | Requires verification through your manager |
| Issue a temporary password | Yes | 24h validity; you change at first sign-in |
| Reset MFA enrollment | Yes | Requires live identity verification |
| Tell you what your old password was | **No** | We don't store passwords in plaintext, ever |
| Bypass MFA "just for today" | **No** | Compliance hard rule, no exceptions |
| Sign in as you to test | **No** | Same reason as above |
