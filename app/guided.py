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
from .evaluate import evaluate
from .pipeline import ingest
from .presentation import show_answer, prose, safe_text
from .provider_options import DEFAULT_MODELS, GUIDES
from .query import execute_query
from .service import ask
from .storage import inspect_invoice
from .terminal import paint

ROOT = Path(__file__).resolve().parents[1]


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(paint(label, "prompt") + paint(suffix, "muted") + ": ").strip() or default


def heading(title: str):
    print("\n" + paint("=" * 64, "muted"))
    print(paint(title, "heading"))
    print(paint("=" * 64, "muted"))


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
        print(paint("Flags: " + ", ".join(f"{code}={count}" for code, count in report['warning_counts'].items()), "warning"))
    for policy in report['provisional_policies']:
        print(paint(f"  * {policy}", "warning"))


def configure_provider() -> ProviderConfig | None:
    settings = read_settings()
    print("\n" + paint("1", "prompt") + " OpenAI   " + paint("2", "prompt") + " Claude (Anthropic)   " + paint("3", "prompt") + " Stay offline")
    choice = prompt("Provider", "3")
    if choice in {"3", "offline"}:
        return None
    provider = {"1": "openai", "2": "anthropic", "openai": "openai", "claude": "anthropic", "anthropic": "anthropic"}.get(choice.lower())
    if provider is None:
        raise ValueError("choose 1, 2, or 3")
    prefix = PROVIDERS[provider]
    guide = GUIDES[provider]
    print(paint(f"Recommended: {guide['name']}", "heading"))
    print(f"Default model pricing, checked 2026-09-15: {guide['price']}")
    print(f"Current rates: {guide['pricing_url']}")
    print("API key setup (if you already have a key, continue below):")
    for number, step in enumerate(guide['steps'], 1):
        print(f"  {number}. {step}")
    print("API billing is separate from chat subscriptions. Keys entered here are not saved.")
    print("Press Enter for the selected model, or type another model ID you can access.")
    configured_model = settings.get(f"{prefix}_MODEL", "")
    default_model = DEFAULT_MODELS[provider] if not configured_model or configured_model == "your-model-id" else configured_model
    model = prompt("Model ID", default_model)
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
    prose("Ready. Answered questions use up to two paid API calls: SQL planning and answer summary. No automatic retries.", "success")
    prose("The summary call sends SQL result rows (including any names/IDs), SQL, and coverage to your chosen provider. Use /summary to turn it off.")
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
        print("\n" + paint("Expected unsupported question: ", "warning") + UNSUPPORTED['question'])
        print(UNSUPPORTED['reason'])
        heading("4 / Check the independent evaluations")
        if prompt("Run the offline test suite? y/n", "y").lower() == 'y':
            check = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
            if check.returncode:
                print(paint("Evaluations failed. Review the output before trusting results.", "error"))
                return check.returncode
            print(paint("Offline evaluations passed.", "success"))
        heading("5 / Ask your own questions")
        print("Choose a provider now, or keep exploring the curated SQL offline.")
        config = None
        include_summary = True
        while True:
            try:
                config = configure_provider()
                break
            except ValueError as exc:
                prose(f"Configuration: {exc}", "warning")
        print()
        prose("Commands: /examples, /quality, /inspect INVOICE_ID, /provider, /summary, /evaluate, /quit")
        print("Try: Which region has the highest average MRR per account?")
        while True:
            question = prompt("Ask or enter a command", "/quit")
            try:
                if question == '/quit':
                    break
                if question == '/provider':
                    config = configure_provider()
                elif question == '/summary':
                    include_summary = not include_summary
                    print('AI summaries ' + ('on: result rows are sent to the provider.' if include_summary else 'off: result rows stay local.'))
                elif question == '/quality':
                    quality(report)
                elif question.startswith('/inspect '):
                    print(json.dumps(inspect_invoice(database, question[9:].strip()), indent=2, ensure_ascii=True))
                elif question == '/examples':
                    print("Curated SQL examples (offline):")
                    for label, sql in QUESTIONS:
                        print(f"\n{label}")
                        show_answer(execute_query(database, sql))
                elif question == '/evaluate' and config is not None:
                    if prompt("Run up to 7 paid model calls against the original sample? y/n", "n").lower() == 'y':
                        print("Running live answer checks...", flush=True)
                        evaluation = evaluate(config)
                        for case in evaluation['cases']:
                            print(paint("PASS" if case["passed"] else "FAIL", "success" if case["passed"] else "error") + ": " + case["question"])
                            if not case['passed']:
                                print(json.dumps(case, indent=2, ensure_ascii=True))
                        print(paint("All cases passed." if evaluation["passed"] else "Some cases failed; review the details above.", "success" if evaluation["passed"] else "error"))
                elif config is None:
                    print("Use /provider to enable natural-language questions, or /examples for offline SQL.")
                else:
                    print("Planning and running SQL, then preparing your answer...", flush=True)
                    show_answer(ask(question, database, config, include_summary=include_summary))
            except (ValueError, OSError, sqlite3.Error) as exc:
                prose(f"Could not complete this action: {exc}", "error")
        print("\n" + paint("Session complete.", "success") + " Local audit database: work/reviewer.sqlite")
        print("Next: README.md for commands; docs/HANDOFF.md for design and remaining work.")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nSession ended. No entered API key was saved.")
        return 0
    except (ValueError, OSError, sqlite3.Error, csv.Error) as exc:
        print(paint(safe_text(f"Could not start the tour: {exc}"), "error", sys.stderr), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
