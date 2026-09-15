"""Independent query boundary checks; provider mocks do not measure model accuracy."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

from app.config import ProviderConfig, load_config
from app.pipeline import ingest
from app.provider import (build_request, build_anthropic_request, parse_response,
                          parse_anthropic_response, ProviderError, generate_plan, NoRedirect)
from app.query import execute_query, QueryError
from app.service import ask

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/invoices.csv'
PLAN = {'sql': 'SELECT COUNT(*) FROM invoices', 'explanation': 'Accepted invoice count.', 'unsupported_reason': None}


def response(plan=PLAN):
    return {'status': 'completed', 'output': [{'type': 'message', 'content': [
        {'type': 'output_text', 'text': json.dumps(plan)}]}]}


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

    @patch('app.service.generate_plan')
    def test_mocked_question_executes_and_unsupported_does_not(self, generate):
        config = ProviderConfig('fake-test-key', 'test-model')
        generate.return_value = PLAN
        self.assertEqual(ask('How many invoices?', self.db, config)['rows'], [[8]])
        generate.return_value = {'sql': None, 'explanation': 'Cannot calculate period churn.',
                                 'unsupported_reason': 'No churn event dates or opening cohort.'}
        result = ask('Enterprise churn during February 2024?', self.db, config)
        self.assertEqual(result['status'], 'unsupported')
        self.assertNotIn('rows', result)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.config = ProviderConfig('fake-test-key', 'test-model')

    def test_request_contract_excludes_key_and_private_columns(self):
        payload = build_request('How much revenue?', '2024-03-15', self.config)
        self.assertFalse(payload['store'])
        self.assertTrue(payload['text']['format']['strict'])
        self.assertNotIn('fake-test-key', json.dumps(payload))
        self.assertNotIn('contact_email', json.dumps(payload))
        self.assertNotIn('fake-test-key', repr(self.config))
        with self.assertRaises(ProviderError):
            build_request('x' * 2001, '2024-03-15', self.config)

    def test_openai_parser(self):
        self.assertEqual(parse_response(response()), PLAN)
        bad = [response({**PLAN, 'extra': True}), response({**PLAN, 'unsupported_reason': 'both'}),
               response({**PLAN, 'sql': ''}), {'status': 'incomplete'},
               {'status': 'completed', 'output': []},
               {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal'}]}]}]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(ProviderError):
                parse_response(item)

    def test_anthropic_contract_and_parser(self):
        payload = build_anthropic_request('How many?', '2024-03-15', self.config)
        self.assertEqual(payload['tool_choice']['name'], 'query_plan')
        self.assertEqual(payload['messages'][0]['role'], 'user')
        good = {'stop_reason': 'tool_use', 'content': [{'type': 'tool_use', 'name': 'query_plan', 'input': PLAN}]}
        self.assertEqual(parse_anthropic_response(good), PLAN)
        for item in [{**good, 'stop_reason': 'max_tokens'}, {**good, 'content': good['content'] * 2},
                     {**good, 'content': [{'type': 'tool_use', 'name': 'other', 'input': PLAN}]}]:
            with self.assertRaises(ProviderError):
                parse_anthropic_response(item)

    @patch('app.provider.build_opener')
    def test_transport_and_sanitized_error(self, opener):
        reply = MagicMock()
        reply.__enter__.return_value.read.return_value = json.dumps(response()).encode()
        opener.return_value.open.return_value = reply
        self.assertEqual(generate_plan('How many?', '2024-03-15', self.config)['sql'], PLAN['sql'])
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.openai.com/v1/responses')
        opener.return_value.open.side_effect = HTTPError(request.full_url, 401, 'secret-body', {}, None)
        with self.assertRaises(ProviderError) as caught:
            generate_plan('How many?', '2024-03-15', self.config)
        self.assertNotIn('secret-body', str(caught.exception))
        self.assertIn('401', str(caught.exception))
        with self.assertRaises(ProviderError):
            NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com')

    @patch.dict('os.environ', {}, clear=True)
    def test_config_inert_values_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('LLM_PROVIDER=anthropic\nANTHROPIC_API_KEY="fake-key"\nANTHROPIC_MODEL=test-model\n')
            config = load_config(path)
            self.assertEqual(config.provider, 'anthropic')
            with patch.dict('os.environ', {'ANTHROPIC_MODEL': 'override'}):
                self.assertEqual(load_config(path).model, 'override')
            path.write_text('OPENAI_API_KEY=$(never-executed)\nOPENAI_MODEL=test\n')
            self.assertEqual(load_config(path).api_key, '$(never-executed)')
            path.write_text('export something\n')
            with self.assertRaises(ValueError):
                load_config(path)


if __name__ == '__main__':
    unittest.main()
