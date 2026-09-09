"""
Synthetic Digital Twin Dataset (Phase 3.2).

CDT2 does not have a production/labeled cybersecurity incident dataset,
so the risk models are trained on a reproducible SYNTHETIC dataset
generated to have the same shape and feature ranges as
app/ml/feature_engineering.py's real feature vector, with a target risk
label built from a transparent, documented weighted formula plus noise
— NOT a random target. This lets the models learn genuine, checkable
relationships (e.g. "internet exposure + critical vuln + no MFA + short
attack path => high risk") instead of memorizing noise.

This is explicitly and permanently labeled "Synthetic Digital Twin
Dataset" everywhere it surfaces (model metadata, API responses, UI) per
the project's anti-fabrication rule — it must never be presented or
mistaken for real-world/production data.

Fixed random seed (42) makes generation fully reproducible: calling
generate_synthetic_dataset() twice produces byte-identical output.
"""
import numpy as np
import pandas as pd

from app.ml.feature_engineering import FEATURE_NAMES

DATASET_LABEL = "Synthetic Digital Twin Dataset"
RANDOM_SEED = 42

# Documented weights for the synthetic target formula. These mirror the
# same qualitative relationships as the deterministic risk engine
# (app/services/risk_engine.py) — asset criticality, exposure, weak
# auth, and vulnerabilities all push risk up; strong controls and long
# attack paths pull it down — but are independent of that engine's exact
# formula, so the ML models learn a related-but-not-identical signal
# worth comparing/ensembling against.
TARGET_WEIGHTS = {
    "asset_criticality": 9.0,       # 1-4  -> up to 36
    "internet_exposed": 12.0,        # 0/1
    "mfa_enabled": -14.0,            # having MFA REDUCES risk
    "permission_level_score": 5.0,   # 0-3  -> up to 15
    "permission_count": 0.6,         # small per-permission bump
    "vulnerability_count": 3.0,
    "critical_vulnerability_count": 9.0,
    "known_exploited": 14.0,
    "avg_cvss_score": 2.0,           # 0-10
    "attack_path_length": -2.5,      # longer path from entry = harder to reach = lower risk
    "attack_path_cost": -0.8,
    "historical_security_events": 1.5,
    "active_security_events": 4.0,
    "network_segmentation": -10.0,   # segmentation REDUCES risk
    "org_control_maturity": -18.0,   # mature control program REDUCES risk
}

BASELINE = 20.0  # every environment has some baseline residual risk
NOISE_STD = 8.0  # gaussian noise so models must actually learn, not memorize a deterministic formula


def _sample_feature_row(rng: np.random.Generator) -> dict[str, float]:
    return {
        "asset_criticality": rng.integers(1, 5),
        "internet_exposed": rng.integers(0, 2),
        "mfa_enabled": rng.integers(0, 2),
        "permission_level_score": rng.integers(0, 4),
        "permission_count": rng.integers(1, 25),
        "vulnerability_count": rng.poisson(1.5),
        "critical_vulnerability_count": rng.poisson(0.4),
        "known_exploited": rng.integers(0, 2) if rng.random() < 0.25 else 0,
        "avg_cvss_score": round(float(rng.uniform(0, 10)), 2) if rng.random() < 0.6 else 0.0,
        "attack_path_length": rng.integers(0, 6),
        "attack_path_cost": round(float(rng.uniform(0, 40)), 2),
        "historical_security_events": rng.poisson(2.0),
        "active_security_events": rng.poisson(0.5),
        "network_segmentation": rng.choice([0.0, 0.5, 1.0]),
        "org_control_maturity": round(float(rng.uniform(0, 1)), 2),
    }


def generate_synthetic_dataset(n_samples: int = 2000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate the reproducible synthetic training set.

    Returns a DataFrame with columns FEATURE_NAMES + ['risk_score',
    'risk_class', 'is_high_risk'] where risk_class/is_high_risk are
    derived labels for classification-style evaluation, and risk_score
    (0-100) is the regression-style target most models are trained on.
    """
    rng = np.random.default_rng(seed)
    rows = [_sample_feature_row(rng) for _ in range(n_samples)]
    df = pd.DataFrame(rows, columns=FEATURE_NAMES)

    linear = BASELINE + sum(df[col] * w for col, w in TARGET_WEIGHTS.items())
    # critical_vulnerability_count combined with internet_exposed and no
    # MFA is a materially worse combination than the sum of its parts —
    # a modest interaction term keeps the target learnable-but-nonlinear,
    # which is the whole point of using tree ensembles instead of just
    # reusing the deterministic engine's own linear formula.
    interaction = (
        df["critical_vulnerability_count"]
        * df["internet_exposed"]
        * (1 - df["mfa_enabled"])
        * 6.0
    )
    noise = rng.normal(0, NOISE_STD, size=n_samples)
    risk_score = (linear + interaction + noise).clip(0, 100)

    df["risk_score"] = risk_score.round(2)
    df["risk_class"] = pd.cut(
        df["risk_score"], bins=[-0.1, 25, 50, 75, 100.1],
        labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
    ).astype(str)
    df["is_high_risk"] = (df["risk_score"] >= 50).astype(int)  # binary target used by the classifiers
    return df


def dataset_metadata(n_samples: int, seed: int = RANDOM_SEED) -> dict:
    return {
        "dataset": DATASET_LABEL,
        "n_samples": n_samples,
        "random_seed": seed,
        "features": FEATURE_NAMES,
        "target": "is_high_risk (binary, risk_score >= 50)",
        "generation_method": (
            "Weighted linear combination of feature values plus a documented "
            "interaction term and Gaussian noise (see TARGET_WEIGHTS in "
            "app/ml/synthetic_data.py). Not sourced from any real "
            "incident data."
        ),
    }
