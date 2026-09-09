"""
Training entry point (Phase 21 / 38: training is explicit and separate
from inference — this is never triggered implicitly by an API request).

Usage:
    cd backend && python -m app.ml.training
    cd backend && python -m app.ml.training --n-samples 5000 --seed 7
"""
import argparse
import json
import logging

from app.ml.model_registry import model_classes

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cyber_twin.ml.training")


def train_all(n_samples: int = 2000, seed: int = 42) -> dict:
    results = {}
    for key, cls in model_classes().items():
        model = cls()
        evaluation = model.train(n_samples=n_samples, seed=seed)
        path = model.save()
        results[key] = {
            "evaluation": evaluation.to_dict(),
            "artifact_path": str(path),
        }
        logger.info("Saved %s -> %s", key, path)
    return results


def main():
    parser = argparse.ArgumentParser(description="Train CDT2's risk-prediction ML models on the synthetic dataset.")
    parser.add_argument("--n-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    results = train_all(n_samples=args.n_samples, seed=args.seed)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
