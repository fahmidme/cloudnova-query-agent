"""Orchestrate read, normalize, deduplicate, model, and atomically store an import."""

import csv
import hashlib
import io
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from .dates import DateResolver
from .modeling import build_accounts
from .normalize import COLUMNS, financial_fields, normalize
from .policies import POLICY_VERSION, PROVISIONAL, revenue_contribution
from .storage import write_database


def read_csv(path: Path) -> tuple[list[dict], str]:
    data = path.read_bytes()
    if len(data) > 20_000_000:
        raise ValueError("CSV exceeds this demo's 20 MB input limit")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")), strict=True)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != set(COLUMNS):
        raise ValueError("CSV must contain the 19 documented columns exactly once")
    rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError("CSV is empty or contains a record with the wrong field count")
    return rows, hashlib.sha256(data).hexdigest()


def quarantine_group(invoice_id, group):
    contributions = []
    for item in group:
        try:
            contributions.append(revenue_contribution(financial_fields(item.raw)))
        except ValueError:
            contributions.append(None)
    known = all(value is not None for value in contributions)
    return {"invoice_id": invoice_id, "source_rows": [item.row for item in group],
            "reason": "invalid_variant" if any(item.errors for item in group) else "conflicting_variants",
            "errors": {str(item.row): item.errors for item in group if item.errors},
            "alternative_net_revenue_min_cents": min(contributions) if known else None,
            "alternative_net_revenue_max_cents": max(contributions) if known else None}


def ingest(csv_path: Path, db_path: Path, as_of: str | None = None) -> dict:
    if csv_path.resolve() == db_path.resolve():
        raise ValueError("database output must not overwrite the source CSV")
    if as_of is not None:
        as_of = date.fromisoformat(as_of).isoformat()
    raw, source_hash = read_csv(csv_path)
    resolver = DateResolver(raw)
    groups = defaultdict(list)
    issues = []
    for row, record in enumerate(raw, 2):
        item = normalize(row, record, resolver)
        groups[item.values["invoice_id"] or f"__missing_row_{row}"].append(item)
        issues.extend({**issue, "source_row": row, "invoice_id": record["invoice_id"]} for issue in item.issues)
    invoices, sources, quarantine, excluded_accounts = [], [], [], set()
    duplicate_copies = 0
    for invoice_id, group in sorted(groups.items()):
        variants = {tuple(sorted((k, v) for k, v in item.values.items() if k != "source_row")) for item in group}
        if any(item.errors for item in group) or len(variants) != 1:
            quarantine.append(quarantine_group(invoice_id, group))
            excluded_accounts.update(item.raw["account_id"].strip() for item in group)
            continue
        invoice = group[0].values
        invoices.append(invoice)
        sources.extend({"invoice_id": invoice_id, "source_row": item.row} for item in group)
        duplicate_copies += len(group) - 1
    if as_of is None:
        as_of = max((i["invoice_date"] for i in invoices), default=None)
    if as_of is None:
        raise ValueError("no accepted invoices; specify --as-of to create an audit-only database")
    accounts, account_issues = build_accounts(invoices, as_of, excluded_accounts)
    issues.extend(account_issues)
    known = [q for q in quarantine if q["alternative_net_revenue_min_cents"] is not None]
    net = sum(revenue_contribution(i) for i in invoices)
    low = sum(q["alternative_net_revenue_min_cents"] for q in known)
    high = sum(q["alternative_net_revenue_max_cents"] for q in known)
    report = {
        "policy_version": POLICY_VERSION, "source_sha256": source_hash,
        "source_records": len(raw), "invoice_groups": len(groups), "accepted_invoices": len(invoices),
        "equivalent_duplicate_copies": duplicate_copies, "quarantined_invoice_groups": len(quarantine),
        "quarantined_source_records": sum(len(q["source_rows"]) for q in quarantine),
        "modeled_accounts": len(accounts), "as_of": as_of,
        "invoices_after_as_of": sum(i["invoice_date"] > as_of for i in invoices),
        "warning_counts": dict(sorted(Counter(q["code"] for q in issues).items())),
        "provisional_policies": PROVISIONAL,
        "all_dates_net_revenue_uncertainty": {
            "accepted_subtotal_cents": net, "excluded_known_min_cents": low, "excluded_known_max_cents": high,
            "excluded_unknown_groups": len(quarantine) - len(known),
            "total_min_cents": net + low if len(known) == len(quarantine) else None,
            "total_max_cents": net + high if len(known) == len(quarantine) else None,
            "meaning": "All dates; one alternative per excluded invoice, not lost revenue. Bounds are conditional on interpretable variants; not period-specific or a validated total.",
        },
    }
    write_database(db_path, raw, invoices, sources, accounts, quarantine, issues, report)
    return report
