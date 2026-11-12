"""Run transparent diagnostics against the bundled six-row example dataset.

These are in-sample diagnostics, not independent test metrics. The dataset is
far too small for a reliable train/test split or production performance claim.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from backend.services.pipeline import TicketTriagePipeline


def main() -> None:
    frame = pd.read_csv(ROOT / "data" / "maintenance_tickets.csv").fillna("")
    pipeline = TicketTriagePipeline()
    true_category, pred_category, true_severity, pred_severity = [], [], [], []
    rows = []
    for _, row in frame.iterrows():
        result = pipeline.analyze(str(row.description), str(row.asset_type), str(row.ticket_id))
        true_category.append(str(row.target_category)); pred_category.append(result["classification"]["category"])
        true_severity.append(str(row.target_severity)); pred_severity.append(result["severity"]["severity"])
        rows.append({"ticket_id": row.ticket_id, "actual_category": row.target_category,
                     "predicted_category": result["classification"]["category"],
                     "actual_severity": row.target_severity, "predicted_severity": result["severity"]["severity"],
                     "score": result["severity"]["score"]})
    report = {
        "warning": "IN-SAMPLE ONLY: six bundled examples; do not interpret as independent test/generalization performance.",
        "sample_count": len(frame),
        "category_accuracy": accuracy_score(true_category, pred_category),
        "category_report": classification_report(true_category, pred_category, zero_division=0, output_dict=True),
        "category_confusion_matrix_labels": sorted(set(true_category) | set(pred_category)),
        "severity_accuracy": accuracy_score(true_severity, pred_severity),
        "severity_report": classification_report(true_severity, pred_severity, zero_division=0, output_dict=True),
        "ticket_results": rows,
        "validation_recommendation": "Collect a larger expert-labelled dataset, group duplicate/related assets, then use a chronological or site-held-out test split where timestamps/sites are available."
    }
    output = ROOT / "docs" / "evaluation_results.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nSaved: {output}")

if __name__ == "__main__":
    main()
