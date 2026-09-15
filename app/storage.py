"""Local audit storage. Import replacement is atomic; generated queries use a separate reader."""

import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

SCHEMA = """
CREATE TABLE raw_records (source_row INTEGER PRIMARY KEY, invoice_id TEXT, raw_json TEXT NOT NULL);
CREATE TABLE invoices (
 invoice_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, account_name TEXT NOT NULL,
 region TEXT NOT NULL CHECK(region IN ('NA','EMEA','APAC','LATAM')),
 plan TEXT NOT NULL CHECK(plan IN ('starter','pro','enterprise')),
 billing_cycle TEXT NOT NULL CHECK(billing_cycle IN ('monthly','annual')),
 seats INTEGER NOT NULL CHECK(seats > 0), currency TEXT NOT NULL CHECK(currency IN ('USD','EUR','GBP')),
 amount_local TEXT NOT NULL, amount_usd_cents INTEGER NOT NULL, discount_pct TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('paid','pending','failed','refunded','void')),
 invoice_date TEXT NOT NULL, signup_date TEXT, churned INTEGER NOT NULL CHECK(churned IN (0,1)),
 csat_score INTEGER CHECK(csat_score BETWEEN 1 AND 5), industry TEXT, contact_email TEXT,
 payment_method TEXT, support_tickets INTEGER CHECK(support_tickets >= 0), source_row INTEGER NOT NULL
);
CREATE TABLE invoice_sources (invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id), source_row INTEGER NOT NULL REFERENCES raw_records(source_row), PRIMARY KEY(invoice_id,source_row));
CREATE TABLE accounts (
 account_id TEXT PRIMARY KEY, account_name TEXT NOT NULL, region TEXT NOT NULL, plan TEXT NOT NULL,
 seats INTEGER NOT NULL, discount_pct TEXT NOT NULL, churned INTEGER NOT NULL CHECK(churned IN (0,1)),
 csat_score INTEGER, snapshot_invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
 snapshot_date TEXT NOT NULL, as_of TEXT NOT NULL, mrr_usd_cents INTEGER NOT NULL,
 net_revenue_usd_cents INTEGER NOT NULL, snapshot_uncertain INTEGER NOT NULL
);
CREATE TABLE quarantine (invoice_id TEXT PRIMARY KEY, details_json TEXT NOT NULL);
CREATE TABLE quality_issues (id INTEGER PRIMARY KEY, source_row INTEGER, code TEXT NOT NULL, details_json TEXT NOT NULL);
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX invoices_account_date ON invoices(account_id,invoice_date);
CREATE INDEX invoices_status_date ON invoices(status,invoice_date);
"""


def insert_dicts(connection, table: str, records: list[dict]):
    if not records:
        return
    # Table and field names come exclusively from application-owned dictionaries.
    fields = list(records[0])
    sql = f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})"
    connection.executemany(sql, [[r[f] for f in fields] for r in records])


def write_database(path: Path, raw: list[dict], invoices: list[dict], sources: list[dict],
                   accounts: list[dict], quarantine: list[dict], issues: list[dict], report: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".import-", suffix=".sqlite", dir=path.parent)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(temporary)) as conn, conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.executescript(SCHEMA)
            insert_dicts(conn, "raw_records", [{"source_row": i, "invoice_id": r["invoice_id"].strip(),
                                               "raw_json": json.dumps(r)} for i, r in enumerate(raw, 2)])
            insert_dicts(conn, "invoices", invoices)
            insert_dicts(conn, "invoice_sources", sources)
            insert_dicts(conn, "accounts", accounts)
            insert_dicts(conn, "quarantine", [{"invoice_id": q["invoice_id"], "details_json": json.dumps(q)} for q in quarantine])
            insert_dicts(conn, "quality_issues", [{"source_row": q.get("source_row"), "code": q["code"], "details_json": json.dumps(q)} for q in issues])
            conn.execute("INSERT INTO metadata VALUES ('report', ?)", (json.dumps(report),))
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def open_readonly(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def read_report(path: Path) -> dict:
    with closing(open_readonly(path)) as conn:
        result = conn.execute("SELECT value FROM metadata WHERE key='report'").fetchone()
        if not result:
            raise ValueError("database has no import metadata")
        return json.loads(result[0])


def inspect_invoice(path: Path, invoice_id: str) -> dict:
    """Explicit local audit command; never send these raw records to the model."""
    with closing(open_readonly(path)) as conn:
        raw = conn.execute("SELECT source_row, raw_json FROM raw_records WHERE invoice_id=? ORDER BY source_row", (invoice_id,)).fetchall()
        quarantine = conn.execute("SELECT details_json FROM quarantine WHERE invoice_id=?", (invoice_id,)).fetchone()
        issues = conn.execute("SELECT details_json FROM quality_issues WHERE source_row IN (SELECT source_row FROM raw_records WHERE invoice_id=?)", (invoice_id,)).fetchall()
        return {"invoice_id": invoice_id,
                "records": [{"source_row": r[0], "raw": json.loads(r[1])} for r in raw],
                "quarantine": json.loads(quarantine[0]) if quarantine else None,
                "issues": [json.loads(r[0]) for r in issues]}
