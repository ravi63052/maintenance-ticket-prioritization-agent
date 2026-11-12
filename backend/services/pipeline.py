
"""Orchestrate the ticket-triage steps into one structured result."""

from __future__ import annotations

from typing import Any

from .classifier import classify_ticket
from .decision_engine import (
    analyze_root_cause,
    recommend_action,
    route_ticket
)
from .knowledge_base import TicketKnowledgeBase
from .severity import score_severity
from .llm_explainer import LLMExplainer


class TicketTriagePipeline:

    def __init__(self) -> None:

        self.knowledge_base = TicketKnowledgeBase()
        self.llm_explainer = LLMExplainer()

    def analyze(
        self,
        description: str,
        asset_type: str = "unknown",
        ticket_id: str | None = None,
        details: dict[str, Any] | None = None,
        include_llm: bool = False
    ) -> dict[str, Any]:

        if not description.strip():
            raise ValueError("Ticket description cannot be empty.")


        retrieved = self.knowledge_base.retrieve(
            description,
            top_k=3
        )

        classification = classify_ticket(
            description,
            asset_type,
            retrieved
        )

        severity = score_severity(
            description,
            asset_type,
            details
        )

        root_cause = analyze_root_cause(
            description,
            classification["category"]
        )

        action = recommend_action(
            classification["category"],
            severity["severity"]
        )

        routing = route_ticket(
            classification["category"],
            severity["severity"],
            severity["components"]["safety_risk"]
        )

        result = {
            "ticket_id": ticket_id,

            "input": {
                "description": description,
                "asset_type": asset_type,
                "details": details or {}
            },

            "classification": classification,
            "severity": severity,
            "probable_root_cause": root_cause,
            "recommended_next_action": action,
            "routing": routing,
            "retrieval_evidence": retrieved,

            "agent_trace": [
                {
                    "step": "retrieve_context",
                    "status": "completed",
                    "detail": (
                        f"Retrieved {len(retrieved)} similar "
                        "bundled example(s) using TF-IDF."
                    )
                },
                {
                    "step": "classify_ticket",
                    "status": "completed",
                    "detail": (
                        f"Selected category: "
                        f"{classification['category']} "
                        f"using {classification['method']}"
                    )
                },
                {
                    "step": "score_severity",
                    "status": "completed",
                    "detail": (
                        f"Calculated transparent severity "
                        f"score: {severity['score']}/100."
                    )
                },
                {
                    "step": "recommend_action",
                    "status": "completed",
                    "detail": (
                        "Selected an action from the "
                        "category-specific maintenance playbook."
                    )
                },
                {
                    "step": "route_ticket",
                    "status": "completed",
                    "detail": (
                        f"Assigned queue: {routing['queue']} / "
                        f"{routing['primary_team']}."
                    )
                }
            ],

            "limitations": [
                "The bundled dataset contains only six synthetic examples.",
                "Severity weights and routing rules are illustrative assumptions.",
                "Root causes are hypotheses and require human verification.",
                "The workflow is deterministic rule/tool orchestration, not an autonomous LLM agent."
            ]
        }

        if include_llm:

            result["llm_explanation"] = (
                self.llm_explainer.explain(result)
            )

            result["agent_trace"].append({
                "step": "llm_explanation",
                "status": result["llm_explanation"]["status"],
                "detail": "Generated or attempted an LLM explanation."
            })

        else:

            result["llm_explanation"] = {
                "provider": "gemini",
                "status": "skipped",
                "explanation": None
            }

        return result
