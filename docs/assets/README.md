# README preview

`cli-preview.svg` is a static rendering of the application's real terminal formatter,
using its cyan headings, blue prompt, magenta SQL label, and muted coverage text.
The SVG uses text and shapes only, with no scripts, external fonts, or embedded secrets.
A plain-text version provides an accessible alternative.

`cli-example.json` contains the EMEA follow-up from the recorded GPT-5.6 Luna smoke
check on the original synthetic fixture (2026-09-15). The preceding question asked
which region had the highest average MRR per account. It is an example of model
wording, not a promise that every response is identical.

Rebuild from the repository root, using only Python's standard library:

```bash
python3 docs/assets/render_preview.py
```

The script imports the bundled fixture into a temporary SQLite database, runs the
recorded read-only SQL, verifies the expected columns/rows, and passes the result
through `app.presentation.show_answer`. It then converts the captured ANSI colors
to SVG text. The title bar is documentation framing; no provider latency is invented
and no API key is read or request made.

Do not replace this example with private assessment data, credentials, or raw
provider response bodies. The runtime application does not read these assets.

The four local SVG badges describe the stack and recorded offline checks. They do
not depend on an external badge service and do not imply GitHub Actions/CI exists.
Update the verification badge together with the recorded test evidence.
