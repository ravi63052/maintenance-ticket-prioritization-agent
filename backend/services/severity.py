"""Transparent, deterministic severity scoring (not a learned risk model)."""
from __future__ import annotations
from typing import Any

SAFETY_TERMS = ["fire", "smoke", "injury", "electric shock", "shock hazard", "arc flash", "exposed live", "personnel at risk", "chemical leak"]


def score_severity(description: str, asset_type: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    details = details or {}
    text = description.lower()

    # Each component is an interpretable 0–100 risk estimate from available evidence.
    safety = 100 if any(term in text for term in SAFETY_TERMS) or details.get("people_at_risk") else 10

    if details.get("generation_impact") == "high":
        generation = 100
    elif details.get("generation_impact") == "medium":
        generation = 65
    elif any(x in text for x in ["shutdown", "not generating", "generation stopped", "tripping repeatedly"]):
        generation = 85
    elif any(x in text for x in ["gearbox", "vibration", "abnormal noise"]):
        generation = 70
    elif any(x in text for x in ["pitch", "blade pitch"]):
        generation = 75
    elif any(x in text for x in ["scada", "missing data", "telemetry", "curtailment"]):
        generation = 50
    else:
        generation = 20

    if any(x in text for x in ["emergency", "sparking", "complete failure", "gearbox failure", "severe vibration"]):
        equipment = 100
    elif any(x in text for x in ["gearbox", "vibration", "abnormal noise"]):
        equipment = 95
    elif any(x in text for x in ["inverter", "overheat", "high temperature", "tripping", "pitch error"]):
        equipment = 85
    elif any(x in text for x in ["scada", "missing data", "telemetry", "communication loss"]):
        equipment = 50
    elif any(x in text for x in ["inspection", "checklist", "curtailment", "grid instruction"]):
        equipment = 40
    elif any(x in text for x in ["fault", "error", "alarm", "failure"]):
        equipment = 60
    else:
        equipment = 20

    if any(x in text for x in ["immediately", "urgent", "emergency", "asap"]):
        urgency = 100
    elif any(x in text for x in ["gearbox", "vibration", "increased", "repeated", "last two hours", "overdue", "pending", "pitch error", "tripping"]):
        urgency = 85
    elif any(x in text for x in ["error", "alarm", "instruction not reflected"]):
        urgency = 65
    else:
        urgency = 30

    if details.get("downtime_hours") is not None and float(details["downtime_hours"]) > 0:
        generation = max(generation, min(100, 45 + 10 * float(details["downtime_hours"])))

    weights = {"safety": 0.25, "generation_impact": 0.30, "equipment_condition": 0.25, "urgency": 0.20}
    components = {"safety_risk": safety, "generation_impact": generation, "equipment_condition": equipment, "operational_urgency": urgency}
    score = int(round(safety * weights["safety"] + generation * weights["generation_impact"] + equipment * weights["equipment_condition"] + urgency * weights["urgency"]))
    if safety >= 90:
        score = max(score, 90)  # safety override: never dilute an explicit safety hazard
    severity = "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 35 else "low"
    return {
        "score": score,
        "severity": severity,
        "components": components,
        "weights": weights,
        "explanation": "The score combines safety (25%), generation impact (30%), equipment condition (25%), and urgency (20%). Explicit safety hazards trigger a critical-priority override.",
    }
