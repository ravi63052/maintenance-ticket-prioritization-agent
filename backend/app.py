"""FastAPI application for renewable-energy maintenance ticket triage."""
from __future__ import annotations
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.services.pipeline import TicketTriagePipeline

BASE = Path(__file__).resolve().parents[1]
DATA_PATH = BASE / "data" / "maintenance_tickets.csv"
FRONTEND_DIR = BASE / "frontend"
app = FastAPI(
    title="Renewable Energy Maintenance Ticket Prioritization Agent",
    description="Explainable NLP retrieval, severity scoring, recommendations, and rule-based routing.",
    version="1.0.0",
)
pipeline = TicketTriagePipeline()


class TicketRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=3000, description="Maintenance issue in plain language")
    asset_type: str = Field(default="unknown", max_length=80)
    ticket_id: str | None = Field(default=None, max_length=80)
    downtime_hours: float | None = Field(default=None, ge=0, le=10000)
    generation_impact: str | None = Field(default=None, pattern="^(low|medium|high)$")
    people_at_risk: bool = False


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "maintenance-ticket-triage"}


@app.get("/api/demo")
def demo() -> dict[str, Any]:
    return {
        "case_study": "AI Agent for Maintenance Ticket Prioritization",
        "status": "running",
        "dataset": pipeline.knowledge_base.summary(),
        "capabilities": ["ticket classification", "severity scoring", "probable root cause", "recommended next action", "agent-style routing"],
    }


@app.get("/api/tickets")
def list_tickets() -> dict[str, Any]:
    frame = pd.read_csv(DATA_PATH).fillna("")
    return {"count": len(frame), "tickets": frame.to_dict(orient="records")}


@app.post("/api/analyze")
@app.post("/api/run")
def analyze_ticket(request: TicketRequest) -> dict[str, Any]:
    try:
        details = {
            "downtime_hours": request.downtime_hours,
            "generation_impact": request.generation_impact,
            "people_at_risk": request.people_at_risk,
        }
        return pipeline.analyze(request.description, request.asset_type, request.ticket_id, details)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/analyze-sample/{ticket_id}")
@app.post("/api/analyze-sample/{ticket_id}")
def analyze_sample(ticket_id: str) -> dict[str, Any]:
    frame = pd.read_csv(DATA_PATH).fillna("")
    rows = frame[frame["ticket_id"].astype(str).str.upper() == ticket_id.upper()]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found")
    row = rows.iloc[0]
    return pipeline.analyze(str(row["description"]), str(row["asset_type"]), str(row["ticket_id"]))


@app.get("/api/metrics")
def metrics() -> dict[str, Any]:
    """Return a clearly labelled in-sample diagnostic, not a test-set claim."""
    from sklearn.metrics import accuracy_score, classification_report
    frame = pd.read_csv(DATA_PATH).fillna("")
    y_category, p_category, y_severity, p_severity = [], [], [], []
    for _, row in frame.iterrows():
        result = pipeline.analyze(str(row["description"]), str(row["asset_type"]))
        y_category.append(str(row["target_category"]))
        p_category.append(result["classification"]["category"])
        y_severity.append(str(row["target_severity"]))
        p_severity.append(result["severity"]["severity"])
    return {
        "evaluation_type": "in-sample diagnostic on the six bundled examples; NOT an independent test score",
        "sample_count": len(frame),
        "category_accuracy": round(float(accuracy_score(y_category, p_category)), 3),
        "category_report": classification_report(y_category, p_category, zero_division=0, output_dict=True),
        "severity_accuracy": round(float(accuracy_score(y_severity, p_severity)), 3),
        "severity_report": classification_report(y_severity, p_severity, zero_division=0, output_dict=True),
        "warning": "With only six examples, metrics are unstable and must not be presented as production generalization performance.",
    }


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
