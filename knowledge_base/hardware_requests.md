# Hardware Requests and Replacements

This runbook covers laptops, monitors, peripherals, and accessories. The IT team
keeps a small on-site inventory at each office; specialty items ship from the
central warehouse in Reno.

## What you can self-request

| Item | Eligibility | Lead time | Notes |
|---|---|---|---|
| External mouse (Logitech MX Master 3S) | Anyone | Same day at office, 3-day ship | |
| Mechanical keyboard (Keychron K2) | Anyone | Same day | Limited stock per office |
| 27" 4K monitor (Dell U2723QE) | Anyone | Same day at office, 5-day ship | One per employee |
| USB-C dock (CalDigit TS4) | Anyone | 5-day ship | Required for monitor connections |
| Headset (Jabra Evolve2 65) | Anyone | Same day | |
| Webcam (Logitech Brio) | Eng/Sales | 5-day ship | Built-in laptop camera is preferred for most |
| Standing desk converter | Anyone | 10-day ship | Manager approval required |
| Laptop stand | Anyone | Same day | |
| Laptop battery replacement | Anyone — battery health <70% | Same week | See "Laptop battery" section below |
| Full laptop replacement | Manager approval, ≥2yr-old machine | 2 weeks | See "Laptop replacement" section |

## How to request hardware

1. Open the IT Support Copilot.
2. Describe what you need and your office location. Example: *"I need a second
   monitor for my desk in the SF office."*
3. The system will:
   - Look up the item in the catalog.
   - Check your office's on-hand inventory.
   - Place an order or reserve a same-day pickup.
   - Create a Jira ticket as the audit record with the SKU, ETA, and pickup/shipping
     instructions.
4. For ship-to-home, confirm your shipping address in the Copilot reply. The
   system uses the address on file in Workday by default.

## Laptop battery

A laptop battery is replaceable when:
- macOS reports battery health < 70% (System Settings → Battery → Battery Health)
- Windows reports `powercfg /batteryreport` design-vs-full-charge ratio < 70%
- The battery shows visible swelling — this is **urgent**, stop using the laptop
  immediately and contact IT before traveling

Replacement process:
1. Request via the Copilot. Mention battery health % if you know it.
2. For Macs: IT ships a Genius Bar appointment slip; or for offices with on-site
   IT, drop off your laptop in the morning, pick up by 5pm same day.
3. For ThinkPads: batteries are user-replaceable; IT ships the part and a
   short video. Keep the old battery for return shipping.

## Laptop replacement (full machine)

Standard refresh cycle is 3 years. Out-of-cycle replacement requires manager
approval and one of:
- Demonstrated performance issue (build times, video calls)
- Hardware failure not covered by battery/SSD swap
- Role change requiring different platform (e.g., Mac → Windows for .NET work)

Process:
1. Open the Copilot, describe the situation. The system collects manager,
   department, and current machine model.
2. The Copilot creates a `IT-LAPTOP` ticket and routes to your manager for
   approval.
3. After approval, IT ships the new machine within 2 weeks. You'll get an email
   with setup instructions and a deadline to return the old machine (typically 14
   days after receiving the new one).
4. Use the company's migration assistant for data transfer; do not back up to
   personal drives.

## Returning hardware

When leaving the company or returning a replaced item:
- Pack in the original box if you still have it; otherwise IT will send packaging.
- Include all accessories that came with the device (charger, dongles).
- Ship via the prepaid label IT sends. Do not write off lost equipment as
  "personal use".

## Common issues

### "My new monitor shows no signal"

Try in this order:
1. Check the cable: USB-C to USB-C requires a Thunderbolt-rated cable, not a
   power-only one.
2. Check the dock: the CalDigit TS4 needs its own power brick connected before
   monitors will work.
3. Power-cycle the monitor (some Dells require this after cable change).
4. If still no signal, escalate.

### "My headset audio is choppy on Zoom"

Bluetooth headsets often degrade when many devices are connected. Try the wired
USB-A dongle that came with the Jabra. If choppy persists, escalate — could be
a driver issue.

### "My standing desk won't move"

Most standing desks have a child-lock toggle (hold the down arrow for 5 seconds
to disable). If that doesn't work, the desk needs an in-person fix from facilities,
not IT.
