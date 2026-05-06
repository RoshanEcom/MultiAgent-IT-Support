"""Mock hardware catalog + ordering. Mirrors knowledge_base/hardware_requests.md."""
from __future__ import annotations

import itertools
import time
from typing import Any

# Per-office on-hand inventory (so the demo can simulate "out of stock at NYC, ships from Reno")
HARDWARE_CATALOG = {
    "mouse": {
        "sku": "LOG-MX3S",
        "name": "Logitech MX Master 3S Mouse",
        "ship_days": 3,
        "stock": {"SF": 12, "NYC": 0, "Reno": 40},
    },
    "keyboard": {
        "sku": "KEY-K2",
        "name": "Keychron K2 Mechanical Keyboard",
        "ship_days": 5,
        "stock": {"SF": 4, "NYC": 2, "Reno": 25},
    },
    "monitor": {
        "sku": "DELL-U2723QE",
        "name": "Dell 27\" 4K Monitor U2723QE",
        "ship_days": 5,
        "stock": {"SF": 6, "NYC": 3, "Reno": 30},
    },
    "dock": {
        "sku": "CALDIGIT-TS4",
        "name": "CalDigit TS4 USB-C Dock",
        "ship_days": 5,
        "stock": {"SF": 3, "NYC": 1, "Reno": 18},
    },
    "headset": {
        "sku": "JABRA-EVO65",
        "name": "Jabra Evolve2 65 Headset",
        "ship_days": 5,
        "stock": {"SF": 8, "NYC": 4, "Reno": 22},
    },
    "webcam": {
        "sku": "LOG-BRIO",
        "name": "Logitech Brio Webcam",
        "ship_days": 5,
        "stock": {"SF": 2, "NYC": 1, "Reno": 15},
    },
    "laptop_stand": {
        "sku": "STND-RAIN",
        "name": "Rain Design mStand Laptop Stand",
        "ship_days": 3,
        "stock": {"SF": 5, "NYC": 3, "Reno": 20},
    },
    "battery": {
        "sku": "BATT-REPLACE",
        "name": "Laptop battery replacement service",
        "ship_days": 2,
        "stock": {"SF": 999, "NYC": 999, "Reno": 999},  # service, not stock
    },
}


def _normalize_hardware_term(term: str) -> str | None:
    t = term.lower().strip()
    aliases = {
        "mouse": "mouse",
        "keyboard": "keyboard",
        "monitor": "monitor",
        "screen": "monitor",
        "display": "monitor",
        "second monitor": "monitor",
        "dock": "dock",
        "docking station": "dock",
        "headset": "headset",
        "headphones": "headset",
        "webcam": "webcam",
        "camera": "webcam",
        "laptop stand": "laptop_stand",
        "stand": "laptop_stand",
        "battery": "battery",
        "battery replacement": "battery",
    }
    for alias, canonical in aliases.items():
        if alias in t:
            return canonical
    return None


def catalog_lookup_hardware(*, description: str) -> dict[str, Any]:
    canonical = _normalize_hardware_term(description)
    if not canonical:
        return {
            "found": False,
            "description": description,
            "summary": (
                f"No catalog match for '{description}'. "
                f"Routing to IT for manual sourcing."
            ),
        }
    entry = HARDWARE_CATALOG[canonical]
    return {
        "found": True,
        "term": canonical,
        "sku": entry["sku"],
        "name": entry["name"],
        "ship_days": entry["ship_days"],
        "stock_by_office": entry["stock"],
        "summary": f"Catalog match: {entry['name']} ({entry['sku']}).",
    }


_order_counter = itertools.count(1001)


def catalog_place_order(
    *, sku: str, user_id: str, office: str = "SF", shipping_address: str = ""
) -> dict[str, Any]:
    time.sleep(0.15)
    canonical = next(
        (k for k, v in HARDWARE_CATALOG.items() if v["sku"] == sku), None
    )
    if not canonical:
        return {"error": f"Unknown SKU: {sku}"}
    entry = HARDWARE_CATALOG[canonical]
    in_office = entry["stock"].get(office, 0) > 0
    order_id = f"ORD-{next(_order_counter)}"

    if in_office:
        return {
            "status": "READY_FOR_PICKUP",
            "order_id": order_id,
            "sku": sku,
            "name": entry["name"],
            "office": office,
            "user_id": user_id,
            "summary": (
                f"Order {order_id} reserved at {office} on-site stock. "
                f"Pick up from the IT desk today."
            ),
        }
    return {
        "status": "SHIPPING",
        "order_id": order_id,
        "sku": sku,
        "name": entry["name"],
        "shipping_address": shipping_address or f"{office} office reception",
        "eta_days": entry["ship_days"],
        "user_id": user_id,
        "summary": (
            f"Order {order_id} placed for shipment to {shipping_address or office + ' office'}. "
            f"ETA {entry['ship_days']} business days."
        ),
    }
