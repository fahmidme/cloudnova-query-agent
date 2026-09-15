"""High-confidence input checks; SQL authorization remains the enforcement boundary."""

import re
import unicodedata

from .query import MAX_QUESTION_CHARS

SUSPICIOUS = (
    r'\b(?:ignore|override|disregard|bypass)\b.{0,80}\b(?:instructions?|rules?|guardrails?|system prompt)\b',
    r'\b(?:reveal|show|print|give|expose|extract)\b.{0,60}\b(?:api[_ -]?keys?|passwords?|secrets?|system prompt|access tokens?)\b',
    r'^\s*(?:delete|drop|truncate|alter|update|insert|attach)\b.{0,60}\b(?:table|database|invoices?|accounts?|from|into)\b',
)


def validate_question(question: str) -> str:
    if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f'Question must contain 1–{MAX_QUESTION_CHARS} characters.')
    if any(unicodedata.category(char).startswith('C') and char not in '\n\t' for char in question):
        raise ValueError('Question contains control characters; use plain text.')
    normalized = ' '.join(unicodedata.normalize('NFKC', question).split())
    if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in SUSPICIOUS):
        raise ValueError('Request blocked: ask a read-only business-data question; instruction overrides, secrets, and database changes are unsupported.')
    return question.strip()
