"""Credential lifecycle contracts use mocks; never read or change a reviewer's vault."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from app import credentials
from app.config import load_config
from app.guided import configure_provider


class CredentialTests(unittest.TestCase):
    @patch('app.guided.save_credentials')
    @patch('app.guided.getpass.getpass')
    @patch('app.guided.load_saved', return_value={'api_key': 'saved-test-key', 'model': 'saved-model'})
    @patch('app.guided.read_settings', return_value={})
    @patch('builtins.input', side_effect=['1', ''])
    def test_saved_key_reused_without_key_prompt(self, inputs, settings, saved, hidden, save):
        with redirect_stdout(io.StringIO()) as output:
            config = configure_provider()
        self.assertEqual(config.api_key, 'saved-test-key')
        self.assertEqual(config.model, 'saved-model')
        self.assertNotIn('saved-test-key', output.getvalue())
        hidden.assert_not_called()
        save.assert_not_called()
        self.assertEqual(inputs.call_count, 2)  # provider and model only

    @patch('app.guided.save_credentials', side_effect=credentials.CredentialStoreError('Store locked'))
    @patch('app.guided.getpass.getpass', return_value='new-test-key')
    @patch('app.guided.sys.stdin.isatty', return_value=True)
    @patch('app.guided.load_saved', return_value=None)
    @patch('app.guided.read_settings', return_value={})
    @patch('builtins.input', side_effect=['2', ''])
    def test_failed_save_is_visible_and_session_remains_usable(self, inputs, settings, saved, tty, hidden, save):
        with redirect_stdout(io.StringIO()) as output:
            config = configure_provider()
        self.assertEqual(config.api_key, 'new-test-key')
        self.assertIn('Store locked', output.getvalue())
        self.assertNotIn('new-test-key', output.getvalue())

    @patch('app.config.load_saved', return_value={'api_key': 'vault-key', 'model': 'vault-model'})
    def test_explicit_environment_wins_and_missing_key_uses_vault(self, saved):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'}, clear=True):
            self.assertEqual(load_config(Path('/nonexistent-local-env')).api_key, 'env-key')
            saved.assert_not_called()
        with patch.dict('os.environ', {}, clear=True):
            result = load_config(Path('/nonexistent-local-env'))
            self.assertEqual(result.api_key, 'vault-key')
            self.assertEqual(result.model, 'vault-model')

    @patch('app.credentials._operate')
    def test_vault_serialization_and_delete(self, operate):
        credentials.save_credentials('openai', 'test-key', 'test-model')
        self.assertEqual(json.loads(operate.call_args.args[2]), {'api_key': 'test-key', 'model': 'test-model'})
        credentials.forget_credentials('openai')
        operate.assert_called_with('delete', 'openai')
        operate.return_value = b'{invalid'
        with self.assertRaises(credentials.CredentialStoreError):
            credentials.load_saved('openai')

    @patch('app.credentials.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'', b''))
    @patch('app.credentials.shutil.which', return_value='/usr/bin/secret-tool')
    def test_linux_secret_uses_stdin_not_argv(self, which, run):
        secret = b'{"api_key":"test-sensitive-value","model":"test"}'
        credentials._linux('set', 'openai', secret)
        self.assertNotIn('test-sensitive-value', str(run.call_args.args[0]))
        self.assertEqual(run.call_args.kwargs['input'], secret)
        self.assertFalse(run.call_args.kwargs['check'])


if __name__ == '__main__':
    unittest.main()
