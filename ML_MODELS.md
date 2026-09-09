# ML Models

## Status: not yet implemented

None of the 10 ML models described in the master specification (XGBoost,
LightGBM, Random Forest, Isolation Forest, Autoencoder, GraphSAGE, GAT,
GCN, transformer text classifier, sentence-transformer embeddings) are
built in this version. The `/risk-analysis` and `/advisor` pages in the
UI say so explicitly rather than showing invented numbers, and
`requirements.txt` lists their packages as commented-out until that
phase starts, per the spec's own phased build order (Section 38) and
its explicit rule against fabricating metrics (Section 25: "Never
generate fake metrics").

This document exists so the intended design isn't lost — it's the plan
for Phase 4 onward, written against the actual code that exists today.

## Why nothing is implemented yet

The spec's own priority order puts ML at Phase 4, after the UI, API,
database, and deterministic risk/graph engines are solid (Phase 1-3),
which is what this build delivers. Building ML models against a schema
that might still change would mean re-training against a moving target.

## Planned integration point

`app/services/risk_engine.py` already produces exactly the feature set
XGBoost/LightGBM/Random Forest would need per-asset:

- `criticality`, `internet_exposed`, `mfa_enabled`, `permission_level`,
  `permission_count` — asset fields already in `models.py`
- open vulnerability count/severity, known-exploited flag — from the
  `vulnerabilities` table
- attack-path length/cost — from `graph_engine.py`

Plan: `ml/train_risk_model.py` reads these same fields (via a small
feature-extraction function shared with `risk_engine.py` so the ML
model and the deterministic model never drift apart in what they mean
by "internet exposed," etc.), trains against labeled or synthetic
outcome data, and saves a model with `joblib`. At inference time,
`app/services/risk_engine.py` would call the saved model and blend its
`risk_probability` with the deterministic score using the configurable
weighting described in Section 14 of the spec — never replacing it
outright, so the app keeps working even if the model file is missing.

## Model-by-model plan

| Model | Library | Purpose | Where it plugs in |
|---|---|---|---|
| XGBoost | `xgboost` | Primary risk-probability prediction | Blended into `Asset.risk_score` |
| LightGBM | `lightgbm` | Alternative gradient boosting, for comparison | New `/api/ml/compare` endpoint |
| Random Forest | `scikit-learn` | Baseline ensemble comparison | Same comparison endpoint |
| Isolation Forest | `scikit-learn` | Anomaly detection (e.g. sudden permission jumps) | New `SecurityEvent` of type `anomaly`, written by a scheduled job |
| Autoencoder | `torch` | Advanced anomaly detection, optional | Only once enough historical `risk_scores` rows exist to train on |
| GraphSAGE | `torch-geometric` | Node representation learning over the digital twin graph | Feeds a graph-derived risk signal, blended like XGBoost's |
| GAT | `torch-geometric` | Attention-weighted relationship importance | Explains *which* relationship drives an attack path, shown in the attack-path "Why?" panel |
| GCN | `torch-geometric` | Experimental baseline vs. GraphSAGE/GAT | `/api/ml/graph-model-comparison`, not in the live request path |
| BERT/RoBERTa/DistilBERT | `transformers` | Classify free-text vulnerability/incident descriptions | Runs when a vulnerability is created without a CVE match |
| Sentence Transformer | `sentence-transformers` | Embeddings for RAG semantic search | Feeds the Phase 7 vector store, not the risk engine |

## Explainability plan (SHAP)

Once XGBoost/LightGBM/Random Forest exist, `shap.TreeExplainer` output
would be exposed via the existing `AssetRiskDetail.factors` shape (see
`schemas.py`) so the frontend's "Why is this asset high risk?" panel
in `AssetDetails.tsx` needs no changes — it would simply receive a
richer, ML-augmented factor list alongside the deterministic one.

## Evaluation policy

Per Section 25 of the spec: accuracy/precision/recall/F1/ROC-AUC will
only ever be displayed after a model has actually been trained and
evaluated in this codebase, and results trained on synthetic seed data
will be labeled "synthetic-data evaluation" in the UI, not presented as
real-world accuracy.
