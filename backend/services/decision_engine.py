"""Root-cause hypotheses, recommended actions, and deterministic routing."""
from __future__ import annotations
from typing import Any

ROOT_CAUSE_RULES = [
    ("safety_hazard", ["fire", "smoke", "electric shock", "arc flash", "chemical leak"], "Potential unsafe condition or equipment insulation/containment failure"),
    ("inverter_thermal", ["inverter", "overheat", "high temperature", "thermal alarm"], "Possible cooling-system restriction, fan failure, or excessive ambient temperature"),
    ("gearbox_vibration", ["gearbox", "vibration", "abnormal noise"], "Possible bearing wear, lubrication issue, gear damage, or misalignment"),
    ("inspection_compliance", ["inspection", "checklist", "overdue", "pending"], "Inspection task may be overdue or maintenance evidence may be incomplete"),
    ("data_gap", ["scada", "missing data", "telemetry", "communication loss"], "Possible sensor, network, gateway, or SCADA communication issue"),
    ("pitch_system", ["pitch", "blade angle"], "Possible pitch actuator, sensor, or controller fault"),
    ("grid_curtailment", ["curtailment", "grid instruction", "dispatch instruction"], "Possible mismatch between grid dispatch instruction and operational dashboard data"),
]

ACTIONS = {
    "safety_hazard": "Follow site emergency and isolation procedures; keep personnel clear and notify the Site Safety lead immediately.",
    "inverter_thermal": "Check inverter alarms and cooling/ventilation; inspect filters and fans after applying the approved electrical isolation procedure.",
    "gearbox_vibration": "Arrange an urgent condition assessment; review vibration trend, oil condition, and bearing/gearbox inspection records.",
    "inspection_compliance": "Assign the overdue inspection to an authorized technician and record checklist completion and findings.",
    "data_gap": "Check SCADA gateway/network health, sensor telemetry, and data timestamps; escalate to OT support if the gap persists.",
    "pitch_system": "Review pitch-controller alarms and event logs; inspect actuator/sensor feedback under the approved maintenance procedure.",
    "grid_curtailment": "Verify the latest grid dispatch instruction against plant controller and dashboard records; coordinate with Grid Operations.",
    "electrical_fault": "Have an authorized electrical technician inspect alarms and protection events using approved isolation and lockout procedures.",
    "mechanical_fault": "Inspect the affected mechanical assembly, operating trends, lubrication, and recent maintenance history.",
    "general_maintenance": "Have the maintenance triage desk review the ticket, gather missing asset details, and assign a qualified technician.",
}


def analyze_root_cause(description: str, category: str) -> dict[str, Any]:
    text = description.lower()
    for rule_category, terms, hypothesis in ROOT_CAUSE_RULES:
        if category == rule_category and any(term in text for term in terms):
            return {"hypothesis": hypothesis, "confidence": "medium", "basis": "Matched ticket text to a documented rule; this is not a confirmed diagnosis."}
    return {"hypothesis": "Insufficient evidence to suggest a specific root cause", "confidence": "low", "basis": "Manual inspection and additional telemetry are required."}


def recommend_action(category: str, severity: str) -> str:
    action = ACTIONS.get(category, ACTIONS["general_maintenance"])
    if severity == "critical":
        return "CRITICAL: " + action
    return action


def route_ticket(category: str, severity: str, safety_risk: int) -> dict[str, Any]:
    team = {
        "safety_hazard": "Site Safety",
        "inverter_thermal": "Solar Electrical Maintenance",
        "gearbox_vibration": "Wind Mechanical Maintenance",
        "inspection_compliance": "Inspection & Compliance",
        "data_gap": "SCADA / OT Support",
        "pitch_system": "Wind Controls Maintenance",
        "grid_curtailment": "Grid Operations",
        "electrical_fault": "Electrical Maintenance",
        "mechanical_fault": "Mechanical Maintenance",
    }.get(category, "Maintenance Triage Desk")
    if safety_risk >= 90:
        return {"primary_team": "Site Safety", "also_notify": [team] if team != "Site Safety" else [], "queue": "Emergency safety review", "reason": "Safety-risk override has precedence over normal category routing."}
    if severity == "critical":
        queue = "Urgent response"
    elif severity == "high":
        queue = "Priority maintenance"
    elif severity == "medium":
        queue = "Planned maintenance"
    else:
        queue = "Routine maintenance"
    return {"primary_team": team, "also_notify": [], "queue": queue, "reason": f"Routed by category '{category}' and severity '{severity}'."}
