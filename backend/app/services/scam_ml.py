"""Cached lightweight ML layer for the Sahaay hybrid scam detector."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .scam_training_data import TRAINING_DATA

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "scam_tfidf_logreg.joblib"
_BUNDLE: dict[str, Any] | None = None


def _train_and_save() -> dict[str, Any]:
    texts = [row["text"] for row in TRAINING_DATA]
    labels = [row["label"] for row in TRAINING_DATA]
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42, solver="liblinear")),
        ]
    )
    model.fit(train_texts, train_labels)
    predictions = model.predict(test_texts)
    metrics = {
        "accuracy": round(float(accuracy_score(test_labels, predictions)), 4),
        "precision": round(float(precision_score(test_labels, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(test_labels, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(test_labels, predictions, zero_division=0)), 4),
        "training_examples": len(train_texts),
        "test_examples": len(test_texts),
    }
    bundle = {"model": model, "metrics": metrics}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)
    return bundle


def load_or_train() -> dict[str, Any]:
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE
    try:
        loaded = joblib.load(MODEL_PATH)
        if isinstance(loaded, dict) and loaded.get("model") and loaded.get("metrics"):
            _BUNDLE = loaded
            return _BUNDLE
    except (OSError, ValueError, EOFError, ImportError, AttributeError):
        pass
    _BUNDLE = _train_and_save()
    return _BUNDLE


def predict_scam_probability(text: str) -> float:
    bundle = load_or_train()
    model = bundle["model"]
    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)
    return float(probabilities[classes.index(1)])


def model_metrics() -> dict[str, Any]:
    return dict(load_or_train()["metrics"])
