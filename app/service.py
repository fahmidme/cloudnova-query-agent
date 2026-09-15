"""Shared question orchestration for guided and machine-readable interfaces."""

from pathlib import Path

from .config import ProviderConfig
from .guardrails import validate_question
from .provider import generate_plan
from .query import execute_query
from .storage import read_report
from .summary import summarize


def ask(question: str, database: Path, config: ProviderConfig, include_summary: bool = True) -> dict:
    question = validate_question(question)
    coverage = read_report(database)
    plan = generate_plan(question, coverage["as_of"], config)
    if plan["sql"] is None:
        return {"question": question, "status": "unsupported", **plan, "coverage": coverage}
    result = {"question": question, "status": "answered", **plan,
              **execute_query(database, plan["sql"])}
    if include_summary:
        try:
            result['summary'] = summarize(question, result, config)
        except (ValueError, OSError) as exc:
            # A prose failure must not discard successfully computed evidence.
            result['summary_error'] = str(exc)
    return result
