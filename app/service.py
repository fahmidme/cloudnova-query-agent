"""Shared question orchestration for guided and machine-readable interfaces."""

from pathlib import Path

from .config import ProviderConfig
from .provider import generate_plan
from .query import execute_query
from .storage import read_report


def ask(question: str, database: Path, config: ProviderConfig) -> dict:
    coverage = read_report(database)
    plan = generate_plan(question, coverage["as_of"], config)
    if plan["sql"] is None:
        return {"question": question, "status": "unsupported", **plan, "coverage": coverage}
    return {"question": question, "status": "answered", **plan,
            **execute_query(database, plan["sql"])}
