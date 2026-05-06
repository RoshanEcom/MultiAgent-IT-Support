"""Mock observability tool — generates plausible recent log events for incident
context. Real implementations would call Datadog, Splunk, etc."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

# Templates per service so the Escalation agent can produce convincing context.
LOG_TEMPLATES = {
    "av": [
        "HDMI handshake failed for room {room}: EDID negotiation timeout",
        "Display source switched: HDMI1 → HDMI2 ({room})",
        "Logitech Bar reported camera privacy shutter closed ({room})",
        "Tap controller heartbeat lost for {room} ({lost_for}s); recovered",
        "Zoom Room appliance restarted ({room}, reason: scheduled)",
        "EDID renegotiated successfully ({room})",
    ],
    "printer": [
        "Print spooler error code 0x80070005 on {host}",
        "Paper jam detected: {host} tray 2",
        "Toner low: {host} ({color}) at 8%",
        "Job rejected: department code missing ({host}, user={user_id})",
    ],
    "network": [
        "DHCP lease expired for {user_id}@{office}",
        "WiFi association timeout: SSID=CompanyCorp ({user_id})",
        "Switch port flap detected: {host} port {port}",
    ],
    "sso": [
        "Okta MFA push timeout for {user_id}",
        "SSO session expired for {user_id} on {app}",
        "User-agent change detected for {user_id}: re-prompted MFA",
    ],
}


def _format_template(template: str, ctx: dict[str, Any]) -> str:
    safe_ctx = {
        "room": ctx.get("room", "Unknown Room"),
        "host": ctx.get("host", "host-unknown"),
        "color": ctx.get("color", "K"),
        "user_id": ctx.get("user_id", "unknown.user"),
        "office": ctx.get("office", "SF"),
        "app": ctx.get("app", "Salesforce"),
        "port": ctx.get("port", random.randint(1, 48)),
        "lost_for": ctx.get("lost_for", random.randint(5, 30)),
    }
    try:
        return template.format(**safe_ctx)
    except KeyError:
        return template


def logs_get_recent(
    *,
    service: str = "av",
    hours: int = 2,
    user_id: str = "",
    room: str = "",
    host: str = "",
) -> dict[str, Any]:
    templates = LOG_TEMPLATES.get(service.lower())
    if not templates:
        return {"error": f"Unknown log service '{service}'. Known: {list(LOG_TEMPLATES)}"}

    ctx = {"user_id": user_id, "room": room, "host": host}
    now = datetime.now(timezone.utc)
    n_events = random.randint(3, 6)
    events = []
    for i in range(n_events):
        ts = now - timedelta(minutes=random.randint(2, hours * 60))
        events.append(
            {
                "ts": ts.isoformat(timespec="seconds"),
                "service": service,
                "message": _format_template(random.choice(templates), ctx),
            }
        )
    events.sort(key=lambda e: e["ts"])

    return {
        "service": service,
        "window_hours": hours,
        "event_count": len(events),
        "events": events,
        "summary": f"Retrieved {len(events)} {service} log events from the last {hours}h.",
    }
