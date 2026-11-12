"""Load and search the bundled ticket examples with TF-IDF retrieval.

The six-row starter dataset is too small to train and honestly validate a
supervised classifier. We therefore use it as a small, transparent reference
set and retrieve similar examples instead of claiming a trained ML model.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "maintenance_tickets.csv"


class TicketKnowledgeBase:
    def __init__(self, csv_path: Path = DATA_PATH) -> None:
        self.csv_path = Path(csv_path)
        self.frame = pd.read_csv(self.csv_path).fillna("")
        required = {"ticket_id", "asset_type", "description", "target_severity", "target_category"}
        missing = required.difference(self.frame.columns)
        if missing:
            raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
        self.frame["description"] = self.frame["description"].astype(str)
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(self.frame["description"].tolist())

    def retrieve(self, text: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not text.strip():
            return []
        query_vector = self.vectorizer.transform([text])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        indexes = scores.argsort()[::-1][: max(1, min(top_k, len(scores)))]
        results = []
        for index in indexes:
            row = self.frame.iloc[int(index)]
            results.append({
                "ticket_id": str(row["ticket_id"]),
                "asset_type": str(row["asset_type"]),
                "description": str(row["description"]),
                "known_category": str(row["target_category"]),
                "known_severity": str(row["target_severity"]),
                "similarity": round(float(scores[index]), 4),
            })
        return results

    def summary(self) -> dict[str, Any]:
        return {
            "rows": int(len(self.frame)),
            "categories": sorted(self.frame["target_category"].astype(str).unique().tolist()),
            "severity_labels": sorted(self.frame["target_severity"].astype(str).unique().tolist()),
            "method": "TF-IDF cosine-similarity retrieval over bundled examples",
        }
