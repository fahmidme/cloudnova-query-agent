"""Reviewer flow and answer-harness checks without network calls or real secrets."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.config import ProviderConfig
from app.evaluate import evaluate
from app.guided import configure_provider, main


class JourneyTests(unittest.TestCase):
    @patch('app.guided.read_settings', return_value={})
    @patch('app.guided.sys.stdin.isatty', return_value=True)
    @patch('app.guided.getpass.getpass', return_value='fake-hidden-key')
    @patch('builtins.input', side_effect=['2', 'test-claude-model'])
    def test_claude_hidden_session_key(self, input_mock, getpass_mock, tty, settings):
        output = io.StringIO()
        with redirect_stdout(output):
            config = configure_provider()
        self.assertEqual(config.provider, 'anthropic')
        self.assertEqual(config.api_key, 'fake-hidden-key')
        getpass_mock.assert_called_once()
        self.assertNotIn('fake-hidden-key', output.getvalue())

    @patch('app.guided.read_settings', return_value={})
    @patch('app.guided.sys.stdin.isatty', return_value=False)
    @patch('builtins.input', side_effect=['1', 'test-model'])
    def test_no_secret_entry_through_pipe(self, input_mock, tty, settings):
        with redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            configure_provider()

    @patch('builtins.input', side_effect=EOFError)
    def test_eof_exits(self, input_mock):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)

    def test_offline_answers_match_independent_expectations(self):
        result = evaluate()
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['cases']), 6)
        self.assertIn('not tested live', result['unsupported_recognition'])

    @patch('app.evaluate.ask', return_value={'columns': ['wrong'], 'rows': [[999]], 'status': 'answered'})
    def test_live_harness_detects_wrong_answers_and_unsupported(self, mocked):
        result = evaluate(ProviderConfig('fake-key', 'test-model'))
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['cases']), 7)
        self.assertTrue(all(not case['passed'] for case in result['cases']))


if __name__ == '__main__':
    unittest.main()
