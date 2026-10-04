"""Hybrid scam analysis: explicit safety rules combined with a cached ML score."""

from __future__ import annotations

import re
from math import prod
from typing import Any

from .scam_ml import model_metrics, predict_scam_probability

RULES: list[dict[str, Any]] = [
    {"key": "credential_request", "pattern": r"otp|one[- ]time password|pin|password|passcode", "reason": "This message asks for an OTP, PIN, password, or other private code.", "weight": 0.78},
    {"key": "suspicious_link", "pattern": r"https?://|www\.", "reason": "It includes a link that should be verified before opening.", "weight": 0.5},
    {"key": "urgency", "pattern": r"urgent|immediately|act now|today|final warning", "reason": "It creates pressure to act quickly.", "weight": 0.28},
    {"key": "account_threat", "pattern": r"block|blocked|suspend|suspended|close your account|lose access", "reason": "It threatens account blocking, suspension, or loss of access.", "weight": 0.58},
    {"key": "prize_scam", "pattern": r"prize|reward|lottery|won|congratulations", "reason": "It uses a prize or reward claim.", "weight": 0.58},
    {"key": "kyc_request", "pattern": r"verify your (account|identity)|kyc|update your pan", "reason": "It asks for sensitive account or identity details.", "weight": 0.48},
    {"key": "impersonation", "pattern": r"bank manager|customer care|support team|official|income tax|police|government", "reason": "It may be impersonating a trusted organisation or authority.", "weight": 0.42},
    {"key": "financial_details_request", "pattern": r"account number|card number|cvv|financial details|bank details|upi pin", "reason": "It asks for sensitive financial information.", "weight": 0.64},
    {"key": "money_request", "pattern": r"send money|transfer money|send (?:a )?(?:small )?fee|pay (?:a )?fee|safe account", "reason": "It asks you to send money or pay an unexpected fee.", "weight": 0.52},
]


def _rule_analysis(lowered: str) -> tuple[list[str], list[str], float]:
    indicators: list[str] = []
    reasons: list[str] = []
    weights: list[float] = []
    for rule in RULES:
        if re.search(rule["pattern"], lowered):
            indicators.append(rule["key"])
            reasons.append(rule["reason"])
            weights.append(rule["weight"])
    rule_probability = 1.0 - prod(1.0 - weight for weight in weights) if weights else 0.0
    return indicators, reasons, rule_probability


def analyze_message(text: str) -> dict[str, Any]:
    lowered = text.lower()
    indicators, reasons, rule_probability = _rule_analysis(lowered)
    ml_probability = predict_scam_probability(text)
    final_score = round(100 * (0.55 * ml_probability + 0.45 * rule_probability))

    # Keep explicit credential and account-threat signals visibly high-risk even
    # when a short message is outside the small demo model's vocabulary.
    if {"credential_request", "account_threat"}.intersection(indicators):
        final_score = max(final_score, 60)
    final_score = min(98, max(2, final_score))
    level = "High" if final_score >= 60 else ("Medium" if final_score >= 30 else "Low")

    if not reasons:
        reasons = ["No obvious scam patterns found. Still verify the sender through an official channel."]
    recommendation = (
        "Do not click links or share any code. Contact the organisation using a phone number or website you already trust."
        if final_score >= 30
        else "Pause and verify the sender through an official channel. Never share private codes."
    )
    return {
        "risk_level": level,
        "score": final_score,
        "ml_probability": round(ml_probability, 4),
        "detected_rule_indicators": indicators,
        "reasons": reasons,
        "recommendation": recommendation,
    }


def training_metrics() -> dict[str, Any]:
    """Expose metrics for setup/tests, not as part of the normal user result."""
    return model_metrics()
