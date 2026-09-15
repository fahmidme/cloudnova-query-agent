"""Small, independent answer regression set; offline and live evidence stay distinct."""

from pathlib import Path
import tempfile

from .config import ProviderConfig
from .demo import QUESTIONS, UNSUPPORTED
from .pipeline import ingest
from .provider import ProviderError
from .query import execute_query
from .service import ask

# Values come from specs/EVALUATION.md, committed before transformation code.
EXPECTED = [
    (['paid_revenue_usd'], [[2710.0]]),
    (['refunds_usd', 'net_revenue_usd'], [[49.0, 2661.0]]),
    (['region', 'mean_mrr_usd'], [['NA', 269.5]]),
    (['plan', 'churned_accounts', 'accounts', 'snapshot_churn_pct'], [['enterprise', 1, 1, 100.0], ['starter', 0, 4, 0.0]]),
    (['account_id', 'account_name', 'net_revenue_usd', 'csat_flag'],
     [['A6', 'Zeta', 1323.0, 'not_low'], ['A1', 'Alpha', 931.0, 'low'], ['A2', 'Beta', 299.0, 'not_low'],
      ['A5', 'Epsilon', 108.0, 'unknown'], ['A3', 'Gamma', 0.0, 'not_low']]),
    (['invoices', 'exposure_usd'], [[2, 247.0]]),
]


def evaluate(config: ProviderConfig | None = None) -> dict:
    results = []
    with tempfile.TemporaryDirectory(prefix='cloudnova-eval-') as directory:
        database = Path(directory) / 'fixture.sqlite'
        ingest(Path(__file__).resolve().parents[1] / 'fixtures/invoices.csv', database)
        for (question, sql), (columns, expected) in zip(QUESTIONS, EXPECTED):
            request = question + '. Return exactly these columns in order: ' + ', '.join(columns) + '.'
            if 'snapshot_churn_pct' in columns:
                request += ' Sort by plan ascending.'
            if 'csat_flag' in columns:
                request += " Sort by net revenue descending then account_id ascending. CSAT flags: low, not_low, unknown."
            try:
                answer = ask(request, database, config) if config else execute_query(database, sql)
                passed = answer.get('columns') == columns and answer.get('rows') == expected
                results.append({'question': request, 'passed': passed, 'expected_rows': expected, 'answer': answer})
            except ProviderError as exc:
                results.append({'question': request, 'passed': False, 'error': str(exc)})
                return {'mode': 'live', 'passed': False, 'stopped_on_provider_error': True, 'cases': results}
            except (ValueError, OSError) as exc:
                results.append({'question': request, 'passed': False, 'error': str(exc)})
        if config:
            try:
                answer = ask(UNSUPPORTED['question'], database, config)
                results.append({'question': UNSUPPORTED['question'], 'passed': answer.get('status') == 'unsupported', 'answer': answer})
            except (ValueError, OSError) as exc:
                results.append({'question': UNSUPPORTED['question'], 'passed': False, 'error': str(exc)})
    return {'mode': 'live' if config else 'offline curated SQL',
            'passed': all(case['passed'] for case in results), 'cases': results,
            'unsupported_recognition': 'live checked' if config else 'not tested live; mocked contract test only'}
