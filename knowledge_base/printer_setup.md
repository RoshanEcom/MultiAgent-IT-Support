# Printer Setup

This runbook covers adding network printers, troubleshooting print failures, and
print policies. We use HP and Canon multifunction devices on every floor.

## Available printers by office

### San Francisco (HQ)
| Floor | Name | Color? | Capabilities |
|---|---|---|---|
| 2 | `sf-2-bw-canon` | No | Print, scan-to-email |
| 3 | `sf-3-color-hp` | Yes | Print, scan, copy |
| 4 | `sf-4-bw-canon` | No | Print, scan-to-email |
| 5 | `sf-5-color-hp` | Yes | Print, scan, copy, badge release |

### New York
| Floor | Name | Color? |
|---|---|---|
| 12 | `nyc-12-color-hp` | Yes |
| 14 | `nyc-14-bw-canon` | No |

### Reno
| Floor | Name | Color? |
|---|---|---|
| 1 | `reno-1-color-hp` | Yes |

## Adding a printer (Mac)

1. Connect to office WiFi (`CompanyCorp`).
2. Open System Settings → Printers & Scanners.
3. Click `+` to add a printer.
4. The IP-based "Default" tab usually doesn't show our printers — switch to the
   `IP` tab.
5. Enter the printer name from the table above followed by `.print.company.com`.
   Example: `sf-3-color-hp.print.company.com`.
6. Protocol: select `Line Printer Daemon - LPD`.
7. Use: select the matching driver from the dropdown. If not listed, select
   `Generic PostScript Printer` — works for all our HPs and Canons for basic
   black-and-white. For color or duplex, install the vendor driver from
   Self Service.

## Adding a printer (Windows)

1. Connect to office WiFi.
2. Settings → Bluetooth & devices → Printers & scanners → Add device.
3. Click "Add manually".
4. Select "Add a printer using an IP address or hostname".
5. Device type: TCP/IP Device. Hostname:
   `sf-3-color-hp.print.company.com` (or your printer).
6. Driver: install the matching HP or Canon driver from Company Portal first,
   then it will appear in the driver list.

## Badge-release printing (5th floor SF only)

The 5th floor printer requires badge tap to release jobs (legal/HR uses this floor).

1. Print as normal.
2. Walk up to the printer.
3. Tap your office badge against the reader on the right side of the device.
4. Select your job from the on-screen list and tap Print.
5. Jobs unprinted after 8 hours are auto-deleted for security.

## Scanning to email

All multifunction printers support scan-to-email — but only to your corporate
address. Personal-email addresses are blocked at the printer firmware level.

1. Place document on glass or in feeder.
2. Tap Scan on the touchscreen.
3. Tap your badge to identify yourself; the printer auto-fills your email.
4. Choose color / B&W and PDF / JPEG.
5. Tap Start.

You'll receive the scan within 1-2 minutes.

## Common issues

### "The printer doesn't show up when I add it"

We don't broadcast printers via mDNS/Bonjour for security — that's why the
Default tab is empty. Use the IP tab with the hostname (above).

### "Print job goes to queue but never prints"

Try in this order:
1. Walk to the printer; check for paper jams or out-of-paper.
2. Cancel the job from your computer's print queue and resubmit.
3. Restart the print spooler:
   - Mac: System Settings → Printers → right-click → Reset printing system
     (clears all printers; you'll re-add)
   - Windows: `services.msc` → Print Spooler → Restart
4. If still failing, escalate.

### "Color prints come out black and white"

You probably picked a B&W driver, or you're trying to print to a B&W printer.
Check the printer name — `bw-` in the name means black-and-white only.

### "I get a 'job rejected: department code required' error"

The 4th-floor and 14th-floor printers (cost-tracked for client billing) require
a department code. In Mac print dialog: Show Details → Job Accounting → enter
your 4-digit code. Don't have a code? Ask the Copilot — it's auto-assigned but
sometimes missed for new hires.
