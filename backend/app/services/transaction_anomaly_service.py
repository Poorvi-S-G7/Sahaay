"""Hybrid anomaly detection for simulated transaction safety checks."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

import joblib
from sklearn.ensemble import IsolationForest

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "transaction_anomaly_iforest.joblib"
_BUNDLE: dict[str, Any] | None = None


def _signature(history: list[dict[str, Any]]) -> tuple[tuple[float, str, int], ...]:
    return tuple(
        sorted(
            (float(row["amount"]), row["created_at"].isoformat(), int(row.get("day_frequency", 1)))
            for row in history
            if row.get("direction") == "expense"
        )
    )


def _day_frequency(history: list[dict[str, Any]], timestamp: datetime) -> int:
    return sum(
        1
        for row in history
        if row.get("direction") == "expense"
        and row["created_at"].date() == timestamp.date()
    )


def _feature_row(row: dict[str, Any], history: list[dict[str, Any]]) -> list[float]:
    timestamp = row["created_at"]
    return [float(row["amount"]), float(timestamp.hour), float(row.get("day_frequency", _day_frequency(history, timestamp)))]


def _train_or_load(history: list[dict[str, Any]]) -> dict[str, Any]:
    global _BUNDLE
    expense_history = [row for row in history if row.get("direction") == "expense"]
    signature = _signature(expense_history)
    if _BUNDLE is not None and _BUNDLE.get("signature") == signature:
        return _BUNDLE
    try:
        loaded: Any = joblib.load(MODEL_PATH)
        if loaded.get("signature") == signature:
            _BUNDLE = loaded
            assert _BUNDLE is not None
            return _BUNDLE
    except (OSError, ValueError, EOFError, AttributeError, KeyError):
        pass

    # Isolation Forest is intentionally trained only on simulated historical expenses.
    # A tiny MVP history is padded with the median profile to keep fitting stable.
    training_rows = list(expense_history)
    if not training_rows:
        now = datetime.utcnow()
        training_rows = [{"amount": 500.0, "created_at": now, "direction": "expense", "day_frequency": 1}]
    while len(training_rows) < 4:
        source = training_rows[len(training_rows) % len(training_rows)].copy()
        source["created_at"] = source["created_at"] + timedelta(minutes=len(training_rows))
        training_rows.append(source)
    features = [_feature_row(row, expense_history or training_rows) for row in training_rows]
    model = IsolationForest(n_estimators=128, contamination="auto", random_state=42, n_jobs=1)
    model.fit(features)
    _BUNDLE = {"model": model, "signature": signature, "training_examples": len(expense_history)}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(_BUNDLE, MODEL_PATH)
    return _BUNDLE


def warm_model(history: list[dict[str, Any]]) -> None:
    """Load or train once during application startup, never per request."""
    _train_or_load(history)


def _ml_score(model: IsolationForest, feature: list[float]) -> int:
    # decision_function is positive for inliers and negative for outliers. The
    # scaling is deliberately bounded because rules provide the safety floor.
    decision = float(model.decision_function([feature])[0])
    return max(0, min(100, round(50 - decision * 100)))


def analyze_transaction(
    history: list[dict[str, Any]],
    amount: float,
    transaction_time: datetime | None = None,
    merchant: str | None = None,
) -> dict[str, Any]:
    now = transaction_time or datetime.utcnow()
    expenses = [row for row in history if row.get("direction") == "expense"]
    amounts = [float(row["amount"]) for row in expenses] or [500.0]
    typical_mean = mean(amounts)
    typical_median = median(amounts)
    typical_std = pstdev(amounts) if len(amounts) > 1 else 0.0
    recent_count = sum(
        1
        for row in expenses
        if now - row["created_at"] <= timedelta(hours=24) and now >= row["created_at"]
    )

    proposed = {"amount": float(amount), "created_at": now, "direction": "expense", "day_frequency": recent_count + 1}
    bundle = _train_or_load(history)
    ml_score = _ml_score(bundle["model"], _feature_row(proposed, expenses or [proposed]))

    reasons: list[str] = []
    rule_scores: list[int] = []
    high_amount_threshold = max(5000.0, typical_median * 4)
    if amount >= 10000:
        reasons.append(f"{amount:,.0f} is a very large simulated payment compared with your recent activity.")
        rule_scores.append(85)
    elif amount > high_amount_threshold:
        reasons.append(f"{amount:,.0f} is much higher than your recent payment amounts around {typical_median:,.0f}.")
        rule_scores.append(70)
    elif amount > max(1000.0, typical_mean + max(typical_std * 3, typical_mean)):
        reasons.append(f"{amount:,.0f} is above your usual simulated spending range.")
        rule_scores.append(52)

    if recent_count >= 5 and amount > max(2000.0, typical_median * 3):
        reasons.append("Several simulated payments were already made in the last 24 hours.")
        rule_scores.append(55)
    if now.hour < 6 or now.hour >= 23:
        reasons.append("The proposed payment time is outside your usual daytime activity.")
        rule_scores.append(48)

    deterministic_score = max(rule_scores, default=0)
    anomaly_score = max(deterministic_score, round(0.35 * ml_score + 0.65 * deterministic_score))
    anomaly_score = max(0, min(100, anomaly_score))
    if anomaly_score >= 70:
        level = "High Risk"
    elif anomaly_score >= 40:
        level = "Suspicious"
    else:
        level = "Normal"
    is_anomaly = anomaly_score >= 40

    if is_anomaly:
        recommended_action = "Please verify the amount and recipient before continuing. A stronger confirmation is required for this simulated payment."
    else:
        recommended_action = "Review the recipient and amount, then confirm the simulated payment if everything looks right."
    if not reasons:
        reasons = ["The amount and timing are within the normal range of your simulated transaction history."]

    return {
        "anomaly_level": level,
        "anomaly_score": anomaly_score,
        "is_anomaly": is_anomaly,
        "reasons": reasons,
        "recommended_action": recommended_action,
        "ml_score": ml_score,
    }


def model_info() -> dict[str, Any]:
    if _BUNDLE is None:
        return {"model": "Isolation Forest", "training_examples": 0, "loaded": False}
    return {"model": "Isolation Forest", "training_examples": _BUNDLE.get("training_examples", 0), "loaded": True}
