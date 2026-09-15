"""Hand-computed business expectations; see specs/EVALUATION.md for the answer key."""

import csv
import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app.dates import DateResolver
from app.normalize import COLUMNS, amount
from app.pipeline import ingest
from app.storage import inspect_invoice

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/invoices.csv"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "ledger.sqlite"
        self.report = ingest(FIXTURE, self.db)

    def query(self, sql):
        with closing(sqlite3.connect(self.db)) as conn:
            return conn.execute(sql).fetchall()

    def custom_import(self, edit, as_of=None):
        with FIXTURE.open(newline="") as source:
            rows = list(csv.DictReader(source))
        edit(rows)
        path = Path(self.directory.name) / "custom.csv"
        with path.open("w", newline="") as target:
            writer = csv.DictWriter(target, COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return ingest(path, self.db, as_of)

    def test_independent_paid_refund_and_net_expectations(self):
        self.assertEqual(self.query("SELECT SUM(amount_usd_cents) FROM invoices WHERE status='paid' AND invoice_date>='2024-01-01' AND invoice_date<'2025-01-01'"), [(271000,)])
        self.assertEqual(self.query("SELECT -SUM(amount_usd_cents) FROM invoices WHERE status='refunded'"), [(4900,)])
        self.assertEqual(self.query("SELECT SUM(amount_usd_cents) FROM invoices WHERE status IN ('paid','refunded')"), [(266100,)])

    def test_regional_account_mean_not_invoice_mean(self):
        self.assertEqual(self.query("SELECT region, AVG(mrr_usd_cents) FROM accounts GROUP BY region ORDER BY AVG(mrr_usd_cents) DESC"),
                         [("NA", 26950.0), ("LATAM", 13230.0), ("EMEA", 9900.0), ("APAC", 4900.0)])

    def test_snapshot_churn_denominator(self):
        self.assertEqual(self.query("SELECT plan, SUM(churned), COUNT(*) FROM accounts WHERE plan IN ('enterprise','starter') GROUP BY plan ORDER BY plan"),
                         [("enterprise", 1, 1), ("starter", 0, 4)])

    def test_top_accounts_and_csat_unknown(self):
        self.assertEqual(self.query("SELECT account_id,net_revenue_usd_cents,csat_score FROM accounts ORDER BY net_revenue_usd_cents DESC, account_id LIMIT 5"),
                         [("A6", 132300, 5), ("A1", 93100, 2), ("A2", 29900, 3), ("A5", 10800, None), ("A3", 0, 4)])

    def test_pending_failed_exposure(self):
        self.assertEqual(self.query("SELECT COUNT(*),SUM(amount_usd_cents) FROM invoices WHERE status IN ('pending','failed')"), [(2, 24700)])

    def test_quarantine_bounds_and_duplicate_provenance(self):
        self.assertEqual([self.report[k] for k in ("source_records","accepted_invoices","equivalent_duplicate_copies","quarantined_invoice_groups")], [11, 8, 1, 1])
        bounds = self.report["all_dates_net_revenue_uncertainty"]
        self.assertEqual((bounds["total_min_cents"], bounds["total_max_cents"]), (266100,315100))
        self.assertEqual(self.query("SELECT source_row FROM invoice_sources WHERE invoice_id='I1' ORDER BY source_row"), [(2,), (3,)])
        self.assertEqual(inspect_invoice(self.db, "I9")["quarantine"]["source_rows"], [11,12])

    def test_annual_mrr_uses_brief_not_annual_amount_divided_by_12(self):
        self.assertEqual(self.query("SELECT mrr_usd_cents FROM accounts WHERE account_id='A6'"), [(13230,)])

    def test_as_of_uses_one_snapshot_and_excludes_future_account_revenue(self):
        report = ingest(FIXTURE, self.db, "2024-01-31")
        self.assertEqual(report["invoices_after_as_of"], 2)
        self.assertEqual(self.query("SELECT snapshot_invoice_id,net_revenue_usd_cents FROM accounts WHERE account_id='A1'"), [("I1",49000)])

    def test_changed_account_identity_is_visible(self):
        self.custom_import(lambda rows: rows[3].update(account_name="Changed", churned="Yes"))
        self.assertEqual(self.query("SELECT snapshot_uncertain,churned,mrr_usd_cents FROM accounts WHERE account_id='A1'"), [(1,1,0)])

    def test_invalid_variant_quarantines_the_whole_invoice(self):
        report = self.custom_import(lambda rows: rows[1].update(amount="unknown"))
        self.assertEqual(self.query("SELECT COUNT(*) FROM invoices WHERE invoice_id='I1'"), [(0,)])
        self.assertEqual(report["all_dates_net_revenue_uncertainty"]["excluded_unknown_groups"], 1)
        self.assertIsNone(report["all_dates_net_revenue_uncertainty"]["total_max_cents"])

    def test_optional_email_is_not_repaired_or_required(self):
        self.custom_import(lambda rows: rows[2].update(contact_email="billing_at_alpha.example", csat_score="99"))
        self.assertEqual(self.query("SELECT contact_email,csat_score FROM invoices WHERE invoice_id='I2'"), [(None,None)])

    def test_failed_import_preserves_database_and_source(self):
        before = self.db.read_bytes()
        source_before = FIXTURE.read_bytes()
        broken = Path(self.directory.name) / "broken.csv"
        broken.write_text("invoice_id,invoice_id\nI1,I2\n")
        with self.assertRaises(ValueError):
            ingest(broken,self.db)
        self.assertEqual(before,self.db.read_bytes())
        self.assertEqual(source_before,FIXTURE.read_bytes())
        self.assertEqual(self.report["source_sha256"],hashlib.sha256(source_before).hexdigest())

    def test_invalid_signs_never_enter_revenue(self):
        self.custom_import(lambda rows: rows[2].update(amount="-490", status="paid"))
        self.assertEqual(self.query("SELECT COUNT(*) FROM invoices WHERE invoice_id='I2'"), [(0,)])

    def test_amount_currency_and_thousands_validation(self):
        self.assertEqual(str(amount("1,200.00 EUR", "EUR")), "1200.00")
        for value,currency in (("1,20.00", "USD"),("£49","USD"),("NaN","USD"),("100","CAD")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                amount(value,currency)


class DateTests(unittest.TestCase):
    def test_cohort_inference_still_flags_ambiguity(self):
        raw = {"signup_date":"2023-01-01","invoice_date":"02-04-2024"}
        resolver = DateResolver([raw, {"signup_date":"2023-01-01","invoice_date":"18-07-2024"}])
        result,issues = resolver.resolve(raw)
        self.assertEqual(result["invoice_date"],"2024-04-02")
        self.assertEqual(issues[0]["code"],"date_inferred")
        self.assertEqual(len(issues[0]["candidates"]),2)

    def test_conflicting_cohorts_do_not_vote(self):
        raw = {"signup_date":"2023-01-01","invoice_date":"02-04-2024"}
        resolver = DateResolver([raw, {"signup_date":"2023-01-01","invoice_date":"18-07-2024"},
                                 {"signup_date":"2023-01-01","invoice_date":"07-18-2024"}])
        result,issues = resolver.resolve(raw)
        self.assertIsNone(result["invoice_date"])
        self.assertEqual(issues[0]["code"],"date_unresolved")

    def test_chronology_can_resolve_but_not_overwrite(self):
        raw = {"signup_date":"2024-03-01","invoice_date":"02-04-2024"}
        result,issues = DateResolver([raw]).resolve(raw)
        self.assertEqual(result["invoice_date"],"2024-04-02")
        self.assertIn("chronology",issues[0]["evidence"])

    def test_no_circular_date_inference(self):
        raw = {"signup_date":"01-02-2024","invoice_date":"02-04-2024"}
        result,_ = DateResolver([raw]).resolve(raw)
        self.assertEqual(result,{"signup_date":None,"invoice_date":None})


if __name__ == "__main__":
    unittest.main()
