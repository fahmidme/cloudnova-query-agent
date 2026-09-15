"""Execute one untrusted query using SQLite authorization and resource limits."""

import json
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from .storage import open_readonly, read_report

MAX_ROWS = 100
MAX_SQL_CHARS = 12000
MAX_QUESTION_CHARS = 2000
TABLE_COLUMNS = {
    "invoices": set("invoice_id account_id account_name region plan billing_cycle seats currency amount_local amount_usd_cents discount_pct status invoice_date signup_date churned csat_score industry payment_method support_tickets source_row".split()),
    "accounts": set("account_id account_name region plan seats discount_pct churned csat_score snapshot_invoice_id snapshot_date as_of mrr_usd_cents net_revenue_usd_cents snapshot_uncertain".split()),
}
FUNCTIONS = set("sum total count avg min max round coalesce ifnull nullif abs lower upper length substr substring date strftime julianday like trim ltrim rtrim".split())


class QueryError(ValueError):
    """The query could not be executed within the documented read boundary."""


def authorize(action, table, column, database, trigger):
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        # COUNT(*) can produce an empty column name; it still needs an allowed table.
        # SQLite can omit the database name for COUNT(*)'s empty-column read.
        # Attached databases are forbidden and each connection is fresh.
        if (database == "main" or (database is None and column == "")) and table in TABLE_COLUMNS and (not column or column in TABLE_COLUMNS[table]):
            return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and (column or "").lower() in FUNCTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def execute_query(db_path: Path, sql: str, max_rows: int = MAX_ROWS,
                  max_steps: int = 1_000_000, timeout_seconds: float = 1.0) -> dict:
    if not isinstance(sql, str) or not sql.strip() or len(sql) > MAX_SQL_CHARS:
        raise QueryError("query is empty or exceeds the SQL length limit")
    if not re.match(r"^\s*(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise QueryError("only a single SELECT/WITH query is supported")
    started, steps = time.monotonic(), 0

    def within_budget():
        nonlocal steps
        steps += 1000
        return int(steps > max_steps or time.monotonic() - started > timeout_seconds)

    try:
        with closing(open_readonly(db_path)) as conn:
            conn.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, MAX_SQL_CHARS)
            conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1_000_000)
            conn.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 50)
            conn.set_authorizer(authorize)
            conn.set_progress_handler(within_budget, 1000)
            cursor = conn.execute(sql)
            columns = [column[0] for column in cursor.description]
            rows = [list(row) for row in cursor.fetchmany(max_rows + 1)]
            if len(rows) > max_rows:
                raise QueryError(f"query returned more than {max_rows} rows; narrow it or add LIMIT")
            if len(json.dumps(rows)) > 1_000_000:
                raise QueryError("query result exceeds the output size limit")
    except sqlite3.Error as exc:
        # SQLite errors include no key or HTTP payload. Expose a useful local query error.
        raise QueryError(f"query rejected or failed: {exc}") from None
    return {"sql": sql, "columns": columns, "rows": rows,
            "query_elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "coverage": read_report(db_path)}
