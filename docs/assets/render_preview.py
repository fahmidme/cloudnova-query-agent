"""Render actual CLI formatting as a GitHub-safe SVG. No packages or API calls.

Run from the repository root: python3 docs/assets/render_preview.py
The answer wording is a recorded live example; SQL results are recomputed locally.
"""

from contextlib import redirect_stdout
from html import escape
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.pipeline import ingest
from app.presentation import prose, show_answer
from app.query import execute_query
from app.terminal import paint

ASSETS = Path(__file__).resolve().parent
ANSI = re.compile(r'\x1b\[([0-9;]*)m')
COLORS = {'1;36': '#71d5e8', '1;34': '#82aaff', '1;35': '#d6a0ef',
          '32': '#a3db76', '33': '#f0c674', '1;31': '#ff7b86', '2': '#99a7bc'}


class Terminal(io.StringIO):
    def isatty(self):
        return True


def main():
    example = json.loads((ASSETS / 'cli-example.json').read_text())
    with tempfile.TemporaryDirectory(prefix='cloudnova-readme-') as directory:
        database = Path(directory) / 'sample.sqlite'
        ingest(ROOT / 'fixtures/invoices.csv', database)
        result = execute_query(database, example['sql'])
    assert (result['columns'], result['rows']) == (example['columns'], example['rows'])
    result.update(status='answered', answer=example['answer'])
    # Only capture the human renderer. No invented provider latency or new API call.
    output = Terminal()
    environment = {key: value for key, value in os.environ.items() if key != 'NO_COLOR'}
    environment.update(TERM='xterm-256color', WT_SESSION='readme-preview')
    with patch.dict(os.environ, environment, clear=True), patch('app.presentation.width', return_value=88), redirect_stdout(output):
        print(paint('Ask or enter a command', 'prompt') + ': ' + example['question'])
        show_answer(result)
        prose('Use /quality for exclusions, /clear for a fresh conversation.', 'muted')
    colored = output.getvalue().rstrip()
    plain = '\n'.join(line.rstrip() for line in ANSI.sub('', colored).splitlines())
    (ASSETS / 'cli-preview.txt').write_text(plain + '\n')
    lines = colored.splitlines()
    line_height, top, margin = 25, 106, 34
    width, height = 1000, top + len(lines) * line_height + 22
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">CloudNova CLI: a contextual MRR answer with SQL evidence</title>',
           '<desc id="desc">Follow-up: What about EMEA? Average MRR is $99.00 across two modeled accounts. The computed result and read-only SQL appear below.</desc>',
           f'<rect x="1" y="1" width="998" height="{height-2}" rx="16" fill="#101722" stroke="#2c394d"/>',
           '<path d="M1 65 H999" stroke="#2c394d"/>',
           '<g fill="#718299"><circle cx="31" cy="33" r="5"/><circle cx="49" cy="33" r="5"/><circle cx="67" cy="33" r="5"/></g>',
           '<text x="93" y="39" fill="#dce5f2" font-family="monospace" font-size="16">CloudNova / reviewer session</text>',
           '<text x="966" y="39" text-anchor="end" fill="#99a7bc" font-family="monospace" font-size="13">ORIGINAL SAMPLE</text>',
           '<g font-family="Menlo,DejaVu Sans Mono,Consolas,monospace" font-size="16" xml:space="preserve">']
    for number, line in enumerate(lines):
        color, bold, start = '#dce5f2', False, 0
        # Natural font metrics preserve the terminal's monospace grid. Never stretch
        # text to an estimated character width; browsers and fonts differ.
        spans = []
        for match in list(ANSI.finditer(line)) + [None]:
            end = match.start() if match else len(line)
            segment = line[start:end]
            if segment:
                spans.append(f'<tspan fill="{color}" font-weight="{600 if bold else 400}">{escape(segment.replace(chr(32), chr(160)))}</tspan>')
            if match:
                code = match.group(1)
                color, bold = COLORS.get(code, '#dce5f2'), code.startswith('1;')
                start = match.end()
        svg.append(f'<text x="{margin}" y="{top+number*line_height}">' + ''.join(spans) + '</text>')
    svg += ['</g>', '</svg>']
    (ASSETS / 'cli-preview.svg').write_text('\n'.join(svg) + '\n')
    print('Rendered docs/assets/cli-preview.svg and cli-preview.txt from verified fixture results.')


if __name__ == '__main__':
    main()
