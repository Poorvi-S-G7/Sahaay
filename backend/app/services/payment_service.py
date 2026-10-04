from typing import Any
from fastapi import HTTPException

def validate_payment(contacts: list[dict[str, Any]], contact_id: str, amount: float) -> dict[str, Any]:
    contact = next((item for item in contacts if item['id'] == contact_id), None)
    if not contact:
        raise HTTPException(404, 'Recipient not found')
    if amount <= 0 or amount > 100000:
        raise HTTPException(422, 'Amount must be between ₹1 and ₹100,000')
    return contact
