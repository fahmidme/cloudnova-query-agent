"""A small terminal journey over the same modules used by the JSON CLI."""

import csv
import getpass
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import warnings

from .config import PROVIDERS, ProviderConfig, read_settings
from .demo import QUESTIONS, UNSUPPORTED
from .pipeline import ingest
from .query import execute_query
from .service import ask
from .storage import inspect_invoice

ROOT = Path(__file__).resolve().parents[1]


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{label}{suffix}: ").strip() or default


def heading(title: str):
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


def table(columns: list, rows: list):
    if not rows:
        print("No matching rows.")
        return
    # JSON-escaped control characters keep untrusted data from controlling the terminal.
    cells = [[json.dumps(value, ensure_ascii=True) if isinstance(value, str)
              else ("unknown" if value is None else str(value)) for value in row] for row in rows]
    headers = [json.dumps(str(column), ensure_ascii=True)[1:-1] for column in columns]
    widths = [max(len(headers[i]), *(len(row[i]) for row in cells)) for i in range(len(headers))]
    print(" | ".join(value.ljust(width) for value, width in zip(headers, widths)))
    print("-+-".join("-" * width for width in widths))
    for row in cells:
        print(" | ".join(value.ljust(width) for value, width in zip(row, widths)))


def quality(report: dict):
    heading("2 / Data quality and coverage")
    print(f"{report['source_records']:,} source records -> {report['accepted_invoices']:,} accepted invoices"
          f" -> {report['modeled_accounts']:,} account snapshots")
    print(f"{report['equivalent_duplicate_copies']:,} equivalent copies collapsed; "
          f"{report['quarantined_invoice_groups']:,} invoice groups set aside.")
    print(f"Snapshot as of {report['as_of']} (latest accepted invoice date).")
    bounds = report['all_dates_net_revenue_uncertainty']
    print(f"Excluded invoice alternatives: ${bounds['excluded_known_min_cents']/100:,.2f}"
          f" to ${bounds['excluded_known_max_cents']/100:,.2f}; "
          f"{bounds['excluded_unknown_groups']} additional groups have unknown impact.")
    print("These are conditional, all-date bounds, not lost revenue or a period estimate.")
    if report['warning_counts']:
        print("Flags: " + ", ".join(f"{code}={count}" for code, count in report['warning_counts'].items()))
    for policy in report['provisional_policies']:
        print(f"  * {policy}")


def show_answer(result: dict):
    if result.get('status') == 'unsupported':
        print("Unsupported: " + json.dumps(result['unsupported_reason'], ensure_ascii=True))
        return
    if result.get('explanation'):
        print("Model interpretation: " + json.dumps(result['explanation'], ensure_ascii=True))
    print("SQL: " + json.dumps(result['sql'], ensure_ascii=True))
    table(result['columns'], result['rows'])
    if 'provider_elapsed_ms' in result:
        print(f"Model: {result['provider_elapsed_ms']:,.0f} ms | SQLite: {result['query_elapsed_ms']:,.2f} ms")


def configure_provider() -> ProviderConfig | None:
    settings = read_settings()
    print("\n1 OpenAI   2 Claude (Anthropic)   3 Stay offline")
    choice = prompt("Provider", "3")
    if choice in {"3", "offline"}:
        return None
    provider = {"1": "openai", "2": "anthropic", "openai": "openai", "claude": "anthropic", "anthropic": "anthropic"}.get(choice.lower())
    if provider is None:
        raise ValueError("choose 1, 2, or 3")
    prefix = PROVIDERS[provider]
    print("Enter a model ID available to your API account.")
    if provider == "openai":
        print("Requires Responses + Structured Outputs support (for example, gpt-4o-mini).")
    else:
        print("Requires Messages tool use; use the model ID from your Claude API console.")
    model = prompt("Model ID", settings.get(f"{prefix}_MODEL", ""))
    key = settings.get(f"{prefix}_API_KEY", "")
    if key == "your-api-key":
        key = ""
    if key:
        print("A configured API key is available (hidden).")
        if prompt("Use this key? y/n", "y").lower() != 'y':
            key = ""
    if not key:
        if not sys.stdin.isatty():
            raise ValueError("hidden key entry needs a terminal; use environment/.env for scripted runs")
        # Never allow getpass to fall back to echoing a secret on unsupported terminals.
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            try:
                key = getpass.getpass("API key (hidden, this session only): ").strip()
            except getpass.GetPassWarning:
                raise ValueError("terminal cannot hide input; configure the key in .env instead") from None
    config = ProviderConfig(key, model, provider)
    print("Ready. Each question makes one paid API request; no automatic retries.")
    print("Only your question, schema, metric rules and as-of date go to the provider.")
    return config


def main() -> int:
    heading("CloudNova | From invoice ledger to a traceable answer")
    print("Python + SQLite. No package downloads. No API key needed for the offline tour.")
    try:
        heading("1 / Choose your data")
        print("Press Enter for the original 11-record sample, or paste a CSV path.")
        source = prompt("CSV", "sample")
        path = ROOT / "fixtures/invoices.csv" if source == "sample" else Path(source.strip("\"'")).expanduser()
        database = ROOT / "work/reviewer.sqlite"
        report = ingest(path, database)
        quality(report)
        heading("3 / Explore answers")
        print("Starting with a curated SQL example (offline; no model generated this query).")
        print(QUESTIONS[1][0])
        show_answer(execute_query(database, QUESTIONS[1][1]))
        print("\nExpected unsupported question: " + UNSUPPORTED['question'])
        print(UNSUPPORTED['reason'])
        heading("4 / Check the independent evaluations")
        if prompt("Run the offline test suite? y/n", "y").lower() == 'y':
            check = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
            if check.returncode:
                print("Evaluations failed. Review the output before trusting results.")
                return check.returncode
        heading("5 / Ask your own questions")
        print("Choose a provider now, or keep exploring the curated SQL offline.")
        config = None
        while True:
            try:
                config = configure_provider()
                break
            except ValueError as exc:
                print(f"Configuration: {exc}")
        print("\nCommands: /examples, /quality, /inspect INVOICE_ID, /provider, /quit")
        print("Try: Which region has the highest average MRR per account?")
        while True:
            question = prompt("Ask or enter a command", "/quit")
            try:
                if question == '/quit':
                    break
                if question == '/provider':
                    config = configure_provider()
                elif question == '/quality':
                    quality(report)
                elif question.startswith('/inspect '):
                    print(json.dumps(inspect_invoice(database, question[9:].strip()), indent=2, ensure_ascii=True))
                elif question == '/examples':
                    print("Curated SQL examples (offline):")
                    for label, sql in QUESTIONS:
                        print(f"\n{label}")
                        show_answer(execute_query(database, sql))
                elif config is None:
                    print("Use /provider to enable natural-language questions, or /examples for offline SQL.")
                else:
                    print("Generating SQL, then checking and executing it locally...", flush=True)
                    show_answer(ask(question, database, config))
                    print(f"Coverage: {report['accepted_invoices']} invoices; {report['quarantined_invoice_groups']} groups excluded. /quality for caveats.")
            except (ValueError, OSError, sqlite3.Error) as exc:
                print(f"Could not complete this action: {exc}")
        print("\nSession complete. Local audit database: work/reviewer.sqlite")
        print("Next: README.md for commands; docs/HANDOFF.md for design and remaining work.")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nSession ended. No entered API key was saved.")
        return 0
    except (ValueError, OSError, sqlite3.Error, csv.Error) as exc:
        print(f"Could not start the tour: {exc}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
