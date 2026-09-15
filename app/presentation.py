"""Readable terminal evidence, with escaping confined to control characters."""

import shutil
import textwrap
import unicodedata

from .terminal import paint


def safe_text(value, multiline=False) -> str:
    return ''.join(char if (char == '\n' and multiline) or not unicodedata.category(char).startswith('C')
                   else f'\\u{ord(char):04x}' for char in str(value))


def width() -> int:
    return max(40, min(100, shutil.get_terminal_size((88, 24)).columns - 4))


def prose(text: str, tone: str | None = None, prefix: str = ''):
    for paragraph in safe_text(text, multiline=True).splitlines():
        line = textwrap.fill(paragraph, width=width(), initial_indent=prefix, subsequent_indent=' ' * len(prefix))
        print(paint(line, tone) if tone else line)


def label(column: str) -> str:
    words = safe_text(column).replace('_', ' ').split()
    return ' '.join(word.upper() if word.lower() in {'usd', 'mrr', 'csat', 'id'}
                    else '%' if word.lower() == 'pct' else word.capitalize() for word in words)


def cell(column: str, value) -> str:
    if value is None:
        return 'Unknown'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if column.endswith('_usd'):
            return f'${value:,.2f}'
        if column.endswith('_usd_cents'):
            return f'{value:,} cents'
        if column.endswith('_pct'):
            return f'{value:,.2f}%'
        return f'{value:,}'
    return safe_text(value)


def table(columns: list, rows: list):
    if not rows:
        prose('No matching rows.', 'muted')
        return
    headers = [label(column) for column in columns]
    cells = [[cell(column, value) for column, value in zip(columns, row)] for row in rows]
    widths = [max(len(headers[i]), *(len(row[i]) for row in cells)) for i in range(len(headers))]
    if sum(widths) + 3 * (len(widths) - 1) > width():
        for number, row in enumerate(cells, 1):
            print(paint(f'Record {number}', 'heading'))
            for header, value in zip(headers, row):
                prose(f'{header}: {value}', prefix='  ')
            print()
        return
    print(paint(' | '.join(value.ljust(size) for value, size in zip(headers, widths)), 'heading'))
    print(paint('-+-'.join('-' * size for size in widths), 'muted'))
    for row in cells:
        print(' | '.join(value.ljust(size) for value, size in zip(row, widths)))


def show_answer(result: dict):
    print()
    if result.get('status') == 'unsupported':
        print(paint('Cannot answer from this data', 'warning'))
        prose(result['unsupported_reason'])
        return
    summary = result.get('summary')
    if summary:
        print(paint('Answer', 'heading'))
        prose(summary['answer'])
        for caveat in summary['caveats']:
            prose(caveat, 'warning', prefix='• ')
        prose('AI summary of the computed results below.', 'muted')
    elif result.get('explanation'):
        print(paint('Query interpretation', 'heading'))
        prose(result['explanation'])
    if result.get('summary_error'):
        prose('Summary unavailable. The SQL results are still available below.', 'warning')
        prose(result['summary_error'], 'muted')
    print('\n' + paint('Computed results', 'heading'))
    table(result['columns'], result['rows'])
    print('\n' + paint('SQL used', 'sql'))
    for line in safe_text(result['sql'], multiline=True).splitlines():
        print(textwrap.fill(line, width=width(), initial_indent='  ', subsequent_indent='    ',
                            replace_whitespace=False, drop_whitespace=False))
    if 'coverage' in result:
        report = result['coverage']
        print()
        excluded = report['quarantined_invoice_groups']
        prose(f"As of {report['as_of']} · {report['accepted_invoices']:,} accepted invoices · "
              f"{excluded:,} excluded invoice {'group' if excluded == 1 else 'groups'}. /quality for full caveats.", 'muted')
    if 'provider_elapsed_ms' in result:
        timing = f"Query planning {result['provider_elapsed_ms']/1000:.2f}s · SQLite {result['query_elapsed_ms']:.1f}ms"
        if summary:
            timing += f" · Summary {summary['summary_elapsed_ms']/1000:.2f}s"
        prose(timing, 'muted')
    print()
