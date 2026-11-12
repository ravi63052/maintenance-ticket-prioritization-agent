# Architecture and design notes

## Responsibility boundaries

- `knowledge_base.py`: owns CSV loading, schema checks, TF-IDF vectorization and nearest-example retrieval.
- `classifier.py`: maps text evidence to a category; retrieval is a fallback, not a replacement for expert labels.
- `severity.py`: calculates a transparent weighted score and applies a safety override.
- `decision_engine.py`: maps category/text to a root-cause hypothesis, recommended action, team and queue.
- `pipeline.py`: sequences the tools and returns a structured result plus a trace.
- `app.py`: validates HTTP input, calls the pipeline and serializes the result.
- `frontend/index.html`: captures a ticket and renders the API response. It contains no prioritization business rules.

## Why not train a classifier?

The supplied data has six rows and six distinct categories. There is effectively one example per category. A train/test split would leave categories absent from training or testing, and a model could memorize the examples without learning general patterns. Training a supervised classifier and reporting its accuracy would be misleading. TF-IDF retrieval plus explicit rules is reproducible and demonstrates NLP preprocessing while honestly exposing the dataset limitation. With a larger labelled dataset, compare a majority-class baseline, TF-IDF + Logistic Regression, and a transformer fine-tune if data volume and compute justify it.

## Agent-style workflow

The pipeline calls local tools in a fixed sequence: retrieve context → classify → score severity → hypothesize cause → recommend action → route. The trace exposes each step. This qualifies as simple tool/rule orchestration for the assignment's agent-style routing requirement; it is not an autonomous planner and does not use an LLM to select tools.

## Input/output contract

Input: free-text description, asset type, optional ticket ID, downtime hours, generation impact and people-at-risk flag.

Output: category and confidence estimate, severity score/label/components, root-cause hypothesis and confidence, recommended action, routing team/queue, retrieved examples, execution trace and limitations.

## Safety and human oversight

Explicit safety language or a structured people-at-risk flag forces critical severity and routes to Site Safety. Recommendations remind users to follow approved isolation/emergency procedures. The prototype must not be used to authorize switching, isolation, restart or other safety-critical actions. A qualified operator remains responsible.
