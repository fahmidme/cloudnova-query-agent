"""Provisional account snapshots; this policy can change without rewriting ingestion."""

from collections import defaultdict

from .policies import subscription_mrr


def build_accounts(invoices: list[dict], as_of: str, excluded_accounts: set[str]) -> tuple[list[dict], list[dict]]:
    groups = defaultdict(list)
    for invoice in invoices:
        if invoice["invoice_date"] <= as_of:
            groups[invoice["account_id"]].append(invoice)
    accounts, issues = [], []
    attributes = ("account_name", "region", "plan", "seats", "discount_pct", "churned")
    for account_id, history in sorted(groups.items()):
        latest_date = max(i["invoice_date"] for i in history)
        latest = sorted((i for i in history if i["invoice_date"] == latest_date), key=lambda i: i["invoice_id"])
        snapshot = latest[0]
        changed = [field for field in attributes if len({i[field] for i in history}) > 1]
        incomplete = account_id in excluded_accounts
        if changed or len(latest) > 1 or incomplete:
            issues.append({"code": "account_snapshot_uncertain", "account_id": account_id,
                           "source_row": snapshot["source_row"], "changed_fields": changed,
                           "latest_date_tie": len(latest) > 1, "quarantined_history": incomplete})
        accounts.append({
            "account_id": account_id, **{field: snapshot[field] for field in attributes},
            "csat_score": snapshot["csat_score"], "snapshot_invoice_id": snapshot["invoice_id"],
            "snapshot_date": latest_date, "as_of": as_of,
            "mrr_usd_cents": 0 if snapshot["churned"] else subscription_mrr(snapshot),
            "net_revenue_usd_cents": sum(i["amount_usd_cents"] for i in history if i["status"] in ("paid", "refunded")),
            "snapshot_uncertain": int(bool(changed or len(latest) > 1 or incomplete)),
        })
    return accounts, issues
