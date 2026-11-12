"""Explainable ticket-category classification with a retrieval fallback."""
from __future__ import annotations

import re
from typing import Any

CATEGORY_RULES: dict[str, dict[str, Any]] = {
    "safety_hazard": {"team": "Site Safety", "keywords": ["injury", "fire", "smoke", "electric shock", "shock hazard", "exposed live", "arc flash", "personnel at risk", "unsafe", "near miss", "oil leak", "chemical leak"]},
    "inverter_thermal": {"team": "Solar Electrical Maintenance", "keywords": ["inverter", "overheat", "overheating", "high temperature", "thermal alarm", "temperature alarm", "tripping"]},
    "gearbox_vibration": {"team": "Wind Mechanical Maintenance", "keywords": ["gearbox", "vibration", "abnormal noise", "bearing", "lubrication"]},
    "inspection_compliance": {"team": "Inspection & Compliance", "keywords": ["inspection", "checklist", "compliance", "overdue", "pending inspection", "preventive maintenance"]},
    "data_gap": {"team": "SCADA / OT Support", "keywords": ["scada", "missing data", "data missing", "telemetry", "communication loss", "dashboard data", "sensor data"]},
    "pitch_system": {"team": "Wind Controls Maintenance", "keywords": ["pitch", "blade angle", "blade control", "pitch actuator"]},
    "grid_curtailment": {"team": "Grid Operations", "keywords": ["curtailment", "grid instruction", "dispatch instruction", "generation dashboard", "grid"]},
    "electrical_fault": {"team": "Electrical Maintenance", "keywords": ["transformer", "cable", "breaker", "short circuit", "voltage", "current", "switchgear", "electrical"]},
    "mechanical_fault": {"team": "Mechanical Maintenance", "keywords": ["pump", "motor", "shaft", "mechanical", "hydraulic", "leakage"]},
}


def _contains(text: str, phrase: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text) is not None


def classify_ticket(description: str, asset_type: str, retrieved: list[dict[str, Any]]) -> dict[str, Any]:
    text = f"{description} {asset_type}".lower()
    matches: list[tuple[int, str, list[str]]] = []
    for category, config in CATEGORY_RULES.items():
        hits = [word for word in config["keywords"] if _contains(text, word)]
        if hits:
            matches.append((len(hits), category, hits))

    # Safety signals take precedence over ordinary equipment categories.
    safety_match = next((item for item in matches if item[1] == "safety_hazard"), None)
    if safety_match:
        matches = [safety_match]

    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        _, category, hits = matches[0]
        confidence = min(0.98, 0.62 + 0.10 * len(hits))
        method = "keyword taxonomy"
        evidence = hits
    elif retrieved and retrieved[0]["similarity"] >= 0.18:
        category = retrieved[0]["known_category"]
        confidence = min(0.75, retrieved[0]["similarity"])
        method = "nearest bundled example (TF-IDF)"
        evidence = [f"Similar to {retrieved[0]['ticket_id']}"]
    else:
        category = "general_maintenance"
        confidence = 0.25
        method = "safe fallback"
        evidence = ["No strong category signal found"]

    team = CATEGORY_RULES.get(category, {}).get("team", "Maintenance Triage Desk")
    return {
        "category": category,
        "confidence": round(confidence, 2),
        "method": method,
        "evidence": evidence,
        "suggested_team": team,
    }
