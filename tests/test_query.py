"""Independent query boundary checks; provider mocks do not measure model accuracy."""

from pathlib import Path
import tempfile
import unittest

from app.pipeline import ingest
from app.query import execute_query, QueryError

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/invoices.csv'
class QueryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'test.sqlite'
        ingest(FIXTURE, self.db)

    def test_aggregate_and_cte(self):
        self.assertEqual(execute_query(self.db, 'WITH x AS (SELECT amount_usd_cents FROM invoices WHERE status="paid") SELECT SUM(amount_usd_cents)/100.0 FROM x')['rows'], [[2710.0]])

    def test_disallowed_operations(self):
        statements = [
            'DELETE FROM invoices', 'DROP TABLE invoices', 'PRAGMA table_info(invoices)',
            "ATTACH DATABASE ':memory:' AS extra", 'SELECT * FROM raw_records',
            'SELECT * FROM metadata', 'SELECT * FROM sqlite_master',
            'SELECT contact_email FROM invoices', 'SELECT load_extension("x")',
            'SELECT COUNT(*) FROM invoices; DELETE FROM invoices',
            'WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<5) SELECT * FROM n',
            'SELECT * FROM pragma_table_info("invoices")',
        ]
        for sql in statements:
            with self.subTest(sql=sql), self.assertRaises(QueryError):
                execute_query(self.db, sql)
        self.assertEqual(execute_query(self.db, 'SELECT COUNT(*) FROM invoices')['rows'], [[8]])

    def test_limits(self):
        with self.assertRaises(QueryError):
            execute_query(self.db, 'SELECT invoice_id FROM invoices', max_rows=2)
        with self.assertRaises(QueryError):
            execute_query(self.db, 'SELECT COUNT(*) FROM invoices a, invoices b, invoices c, invoices d, invoices e', max_steps=1000)
        with self.assertRaises(QueryError):
            execute_query(self.db, 'SELECT 1 ' + ' ' * 12000)


if __name__ == '__main__':
    unittest.main()
