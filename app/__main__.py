"""Thin CLI: parsing/output only; business rules and provider calls live in modules."""

import argparse
import csv
import json
from pathlib import Path
import sqlite3
import sys

from .config import load_config
from .demo import run_demo
from .pipeline import ingest
from .service import ask
from .query import execute_query
from .storage import inspect_invoice, read_report


def main() -> int:
    parser = argparse.ArgumentParser(description="CloudNova invoice pipeline and SQL query agent")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="run the original fixture and curated SQL offline")
    command = commands.add_parser("ingest", help="import a supplied CSV and report quality")
    command.add_argument("csv", type=Path)
    command.add_argument("--db", type=Path, default=Path("work/cloudnova.sqlite"))
    command.add_argument("--as-of", help="snapshot date YYYY-MM-DD; default maximum accepted invoice date")
    for name, argument, help_text in (("ask", "question", "generate SQL using a configured provider and query locally"),
                                     ("sql", "sql", "execute a manually supplied read-only query"),
                                     ("inspect", "invoice_id", "inspect original records and issues locally")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument(argument)
        command.add_argument("--db", type=Path, default=Path("work/cloudnova.sqlite"))
        if name == "ask":
            command.add_argument("--provider", choices=("openai", "anthropic"))
    args = parser.parse_args()
    try:
        if args.command == "demo":
            result = run_demo()
        elif args.command == "ingest":
            result = ingest(args.csv, args.db, args.as_of)
        elif args.command == "inspect":
            result = inspect_invoice(args.db, args.invoice_id)
        elif args.command == "sql":
            result = execute_query(args.db, args.sql)
        else:
            result = ask(args.question, args.db, load_config(provider=args.provider))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, sqlite3.Error, csv.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
