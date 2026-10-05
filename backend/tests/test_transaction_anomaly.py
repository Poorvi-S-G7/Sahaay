from datetime import datetime, timedelta
import unittest

from backend.app.services.transaction_anomaly_service import analyze_transaction


class TransactionAnomalyTests(unittest.TestCase):
    def setUp(self) -> None:
        base = datetime(2026, 10, 4, 10, 0)
        self.history = [
            {"id": "t1", "merchant": "Ravi Kumar", "amount": 500, "direction": "expense", "created_at": base},
            {"id": "t2", "merchant": "Fresh Basket", "amount": 860, "direction": "expense", "created_at": base - timedelta(days=1)},
            {"id": "t3", "merchant": "Metro Recharge", "amount": 299, "direction": "expense", "created_at": base - timedelta(days=5)},
            {"id": "t4", "merchant": "Asha Textiles", "amount": 18500, "direction": "income", "created_at": base - timedelta(days=3)},
        ]

    def test_normal_payment_is_not_anomaly(self) -> None:
        result = analyze_transaction(self.history, 500, datetime(2026, 10, 4, 12, 0), "Ravi Kumar")
        self.assertEqual(result["anomaly_level"], "Normal")
        self.assertLess(result["anomaly_score"], 40)
        self.assertFalse(result["is_anomaly"])

    def test_large_payment_is_high_risk(self) -> None:
        result = analyze_transaction(self.history, 25000, datetime(2026, 10, 4, 12, 0), "Ravi Kumar")
        self.assertEqual(result["anomaly_level"], "High Risk")
        self.assertGreaterEqual(result["anomaly_score"], 70)
        self.assertTrue(result["is_anomaly"])
        self.assertTrue(any("25,000" in reason for reason in result["reasons"]))

    def test_unusual_time_can_raise_suspicion(self) -> None:
        result = analyze_transaction(self.history, 1500, datetime(2026, 10, 4, 2, 0), "Ravi Kumar")
        self.assertGreaterEqual(result["anomaly_score"], 40)
        self.assertTrue(result["is_anomaly"])


if __name__ == "__main__":
    unittest.main()
