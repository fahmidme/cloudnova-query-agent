"""Human presentation stays separate from provider semantics and computed evidence."""

from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

from app.guardrails import validate_question
from app.presentation import show_answer, safe_text, table


class AnswerTests(unittest.TestCase):
    def test_answer_leads_with_finding_and_preserves_table_sql(self):
        result = {'status': 'answered', 'answer': 'North America leads at $269.50.',
                  'sql': 'SELECT region, AVG(mrr_usd_cents)/100.0 AS average_mrr_usd\nFROM accounts',
                  'rows': [['NA', 269.5]], 'columns': ['region', 'average_mrr_usd']}
        with redirect_stdout(io.StringIO()) as output:
            show_answer(result)
        view = output.getvalue()
        self.assertLess(view.index('North America'), view.index('Computed results'))
        self.assertIn('$269.50', view)
        self.assertNotIn('"NA"', view)
        self.assertNotIn('\\nFROM', view)
        self.assertIn('\n  FROM', view)

    def test_direct_reply_has_no_empty_table(self):
        with redirect_stdout(io.StringIO()) as output:
            show_answer({'status': 'conversation', 'answer': 'Which region?', 'provider_elapsed_ms': 12})
        self.assertIn('Which region?', output.getvalue())
        self.assertNotIn('Computed results', output.getvalue())
        self.assertIn('no database query', output.getvalue())

    def test_controls_escaped_and_wide_tables_readable(self):
        self.assertNotIn('\x1b', safe_text('hello\x1b[2J'))
        self.assertNotIn('\u202e', safe_text('hello\u202e'))
        with patch('app.presentation.width', return_value=40), redirect_stdout(io.StringIO()) as output:
            table(['account_name', 'revenue_usd'], [['long company name ' * 5, 1000]])
        self.assertIn('Record 1', output.getvalue())
        self.assertIn('$1,000.00', output.getvalue())
        self.assertEqual(validate_question('Show revenue by account'), 'Show revenue by account')
        self.assertEqual(validate_question('Why did revenue drop in 2024?'), 'Why did revenue drop in 2024?')
