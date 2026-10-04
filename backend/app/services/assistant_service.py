import os
from typing import Any
import httpx

class AssistantService:
    """Optional Gemini adapter; returning None keeps the demo deterministic when unconfigured."""
    def __init__(self) -> None:
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')

    def try_answer(self, message: str, context: dict[str, Any]) -> str | None:
        if not self.api_key:
            return None
        prompt = (
            'You are Sahaay, a cautious financial safety assistant. Use only the supplied simulated data. '
            'Never execute or imply execution of money movement. Reply in simple language. '
            f'Simulated context: {context}. User message: {message}'
        )
        for _ in range(2):
            try:
                response = httpx.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}',
                    json={'contents': [{'parts': [{'text': prompt}]}]}, timeout=20.0,
                )
                response.raise_for_status()
                candidates = response.json().get('candidates', [])
                return candidates[0]['content']['parts'][0]['text'].strip() if candidates else None
            except (httpx.HTTPError, KeyError, IndexError, TypeError):
                continue
        return None
