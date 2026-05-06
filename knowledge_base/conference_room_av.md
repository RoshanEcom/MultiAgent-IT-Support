# Conference Room A/V

This runbook covers projector / display setup, video calls, and common A/V
failures in conference rooms. Most rooms use a Logitech Tap controller with a
Zoom Rooms appliance; the larger boardrooms have Crestron systems.

## Room types

| Room class | Display | Camera | Controller | Capacity |
|---|---|---|---|---|
| Huddle (4-6 ppl) | 55" TV | Logitech Rally Bar Mini | Tap | 4-6 |
| Standard (8-12 ppl) | 75" TV | Logitech Rally Bar | Tap | 8-12 |
| Boardroom | Dual 86" TVs + projector | Logitech Sight + ceiling mics | Crestron panel | 14-20 |
| Auditorium | Projector + 200" screen | PTZ camera | Crestron panel + mixer | 50+ |

## Starting a meeting

### Standard / Huddle rooms (Tap controller)

1. Tap the screen to wake.
2. Two options:
   - **Scheduled meeting:** appears on the home screen if calendar invite
     included the room. Tap to join.
   - **Ad-hoc:** tap "Join with Meeting ID", enter the 9-11 digit Zoom ID.
3. Camera, mic, and display activate automatically.
4. To share your laptop screen: plug in the HDMI cable on the table, then tap
   "Share Content" on the controller.
5. Wireless screen-share: open Zoom on your laptop, click Share → Direct Share
   to Zoom Room → enter the 4-digit code on the room TV.

### Boardroom (Crestron)

1. Touch the Crestron panel on the table to wake.
2. Press "Begin Meeting".
3. Choose source: "Room Camera + Zoom" for a video call, "Laptop HDMI" for a
   presentation only.
4. The room may take 30-60 seconds to switch sources (initial display calibration).

## Common issues

### "No signal" on display before a meeting

This is the most common A/V escalation. Try in this order — each takes <30
seconds:

1. **Reseat the HDMI cable** on the desk-side input. About 40% of "no signal"
   cases are a half-seated cable.
2. **Power-cycle the display** with the physical button at the bottom-right
   bezel. Wait 15 seconds, power back on.
3. **Restart the Tap controller**: press and hold the power button on the
   underside for 10 seconds. The controller and the appliance restart together;
   takes ~90 seconds.
4. **Switch displays** if available — most boardrooms have two displays and the
   Crestron can route to either.
5. If still showing "no signal", **escalate**. Tell the Copilot the room name
   and what you've tried. The Copilot will pull the recent A/V logs and route
   to on-call IT — for in-progress meetings this is high-priority.

### "Camera/mic not working"

Mic and camera live on the Logitech Bar — separate from the display.

1. Check the Tap controller — if the camera icon shows a slash, tap to enable.
2. Wave your hand in front of the camera. Logitech bars have a privacy shutter
   that closes after 5 minutes of no motion; should auto-open.
3. If unmuted in Zoom but participants can't hear: check the Zoom client mic
   selection (should be "Logitech Bar").
4. Reboot the Logitech Bar by unplugging the USB-C cable from its back for 10
   seconds.

### "Calendar invite shows the room as 'Tentative'"

Room availability shows in the calendar but the room may decline if double-booked
or out of service. Check the resource availability when scheduling — the room
shows "Free" only if actually available.

If the room incorrectly declined a recurring meeting:
1. Open the Copilot: *"Conference Room B keeps declining my recurring 1:1."*
2. The Copilot pulls the room's calendar and identifies the conflict.
3. Either reschedule or escalate to facilities for room reassignment.

### "Zoom Room is showing the wrong calendar"

Each Zoom Room is paired to a specific room calendar. If a Zoom Room shows
meetings from a different room, the device pairing is wrong:
1. Tell the Copilot the room name and what calendar it's showing.
2. The Copilot checks the device-pairing record and either re-pairs (5 min) or
   escalates.

### "Wireless screen-share fails (Zoom direct-share)"

1. Make sure your laptop is on `CompanyCorp` WiFi (Guest network can't reach
   the Zoom devices).
2. The 4-digit code on the room TV is case-sensitive — type exactly as shown.
3. Restart Zoom on your laptop.
4. If still failing, fall back to HDMI cable on the table.

### "Crestron panel is frozen / black"

Crestron panels occasionally hang — usually fine to power-cycle:
1. The reset button is on the bottom edge of the panel (small pinhole).
2. Press with a paperclip for 3 seconds.
3. Wait 60 seconds for restart.
4. If room is mid-meeting and you can't reset, escalate immediately — facilities
   has manual override for AV in the boardrooms.

## Booking rooms

Rooms are bookable through Outlook calendar — add the room as a resource in
your meeting invite. The Copilot can also book on your behalf:

> *"Book a 6-person huddle room in SF for tomorrow 2-3pm."*

The system finds an available room matching size + time + office and adds it to
your existing invite or creates one.
