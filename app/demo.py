"""Curated offline SQL demonstration, explicitly separate from live NLP generation."""

from pathlib import Path

from .pipeline import ingest
from .query import execute_query

QUESTIONS = [
    ("Paid invoice revenue in 2024 (USD)", "SELECT ROUND(SUM(amount_usd_cents)/100.0,2) AS paid_revenue_usd FROM invoices WHERE status='paid' AND invoice_date >= '2024-01-01' AND invoice_date < '2025-01-01'"),
    ("Refunds given back and net revenue (USD)", "SELECT ROUND(-SUM(CASE WHEN status='refunded' THEN amount_usd_cents ELSE 0 END)/100.0,2) AS refunds_usd, ROUND(SUM(CASE WHEN status IN ('paid','refunded') THEN amount_usd_cents ELSE 0 END)/100.0,2) AS net_revenue_usd FROM invoices"),
    ("Region with highest mean MRR per account, including churned accounts", "SELECT region, ROUND(AVG(mrr_usd_cents)/100.0,2) AS mean_mrr_usd FROM accounts GROUP BY region ORDER BY AVG(mrr_usd_cents) DESC LIMIT 1"),
    ("Enterprise versus Starter snapshot churn (%)", "SELECT plan, SUM(churned) AS churned_accounts, COUNT(*) AS accounts, ROUND(100.0*SUM(churned)/COUNT(*),2) AS snapshot_churn_pct FROM accounts WHERE plan IN ('enterprise','starter') GROUP BY plan ORDER BY plan"),
    ("Top 5 accounts by net revenue, with snapshot CSAT", "SELECT account_id, account_name, ROUND(net_revenue_usd_cents/100.0,2) AS net_revenue_usd, CASE WHEN csat_score IS NULL THEN 'unknown' WHEN csat_score <= 2 THEN 'low' ELSE 'not_low' END AS csat_flag FROM accounts ORDER BY net_revenue_usd_cents DESC, account_id LIMIT 5"),
    ("Pending/failed invoice count and exposure (USD)", "SELECT COUNT(*) AS invoices, ROUND(SUM(amount_usd_cents)/100.0,2) AS exposure_usd FROM invoices WHERE status IN ('pending','failed')"),
]
UNSUPPORTED = {"question": "What was our Enterprise churn rate during February 2024?",
               "status": "expected_unsupported",
               "reason": "Invoice snapshots lack churn event dates and opening cohort membership; snapshot churn is not period churn."}


def run_demo() -> dict:
    fixture = Path(__file__).resolve().parents[1] / "fixtures/invoices.csv"
    database = Path("work/demo.sqlite")
    report = ingest(fixture, database)
    results = []
    for question, sql in QUESTIONS:
        result = execute_query(database, sql)
        result.pop("coverage")
        results.append({"question": question, **result})
    return {"mode": "offline curated SQL, no model call", "coverage": report,
            "answers": results, "expected_unsupported": UNSUPPORTED}
