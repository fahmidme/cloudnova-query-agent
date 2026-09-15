# Query and reviewer contract v1

Written before implementation on 2026-09-15.

## Commands to implement

- `python run.py`: create the local environment and launch a guided reviewer journey: select the original fixture or a CSV path, inspect quality and sample SQL, run offline evaluations, then optionally configure a provider and ask live questions. Noninteractive input must exit cleanly; hidden key entry requires a terminal.
- `python bootstrap.py`: create `.venv`, verify Python 3.11+ and SQLite support, print OS-specific next commands. No packages or network required.
- `python -m app demo`: import the bundled original fixture into `work/demo.sqlite`, show deterministic stakeholder queries and results. Label this as an offline SQL demonstration, not live natural-language generation.
- `python -m app ingest PATH --db PATH [--as-of YYYY-MM-DD]`: validate/import a supplied ledger and print quality report JSON.
- `python -m app ask QUESTION --db PATH`: use OpenAI to generate a query plan, execute read-only SQL locally, return SQL, deterministic result rows, units/metric definition, elapsed time, and data-quality caveats.
- `python -m app sql SQL --db PATH`: inspect a manually supplied read-only query under the same restrictions; not described as AI generation.
- `python -m app inspect INVOICE_ID --db PATH`: show source record numbers, raw records, and quarantine/issues locally for audit.
- `python -m unittest discover -s tests -v`: offline evaluation, independent expected results and safety checks.

## OpenAI configuration

Read `OPENAI_API_KEY` and `OPENAI_MODEL` from the environment or a project-local `.env` file without executing shell syntax. Existing environment values take precedence. Use the documented provider default when the model is omitted; preserve explicit model overrides. Responses API endpoint is fixed to https://api.openai.com/v1/responses. Use urllib with a timeout and no automatic retry of a possibly completed paid request. Do not follow credential-bearing HTTP redirects. Never log keys or raw HTTP error bodies.

For query planning, send only the user's question, a static schema/metric contract, and as-of metadata. This first call does not include source/result rows. The optional synthesis call described below includes executed result rows. Set `store=false`. The model generates a structured plan containing `sql`, `explanation`, and `unsupported_reason`, with nullable sql/reason. Parse/validate this contract locally; reject refusals, incomplete output, multiple messages, malformed JSON, and missing/unexpected fields. Treat model output as untrusted.

For unsupported historical churn, forecasts, or unavailable attributes, return an explicit unsupported response instead of fabricating SQL. Show explanation as model-provided interpretation, not proof of correctness. Deterministic query results remain the source of truth; the owner-requested answer synthesis below adds a readable explanation.

## Secure credential persistence — owner-requested amendment

Persist newly entered provider keys and model choices in the OS credential store: macOS Keychain, Windows Credential Manager, or Linux Secret Service through an available `secret-tool`. Reuse the saved provider entry automatically, without asking to re-enter or reconfirm the key. Explicit environment/`.env` credentials take precedence. `/key` replaces the current provider's saved credentials; `/forget` deletes the current provider's vault entry and clears the active session. Neither command edits environment variables or `.env` files. Never put secret values in process arguments, logs, repository files, or plaintext fallback storage. If the OS store is unavailable/locked, clearly report session-only operation; never claim persistence succeeded. The offline suite must mock store access; separately verify macOS with a temporary synthetic entry and remove it afterward. OS access dialogs may still be required by the operating system.

## Conversational answers — owner-requested amendment, 2026-09-15

After successful SQL execution, the guided journey sends the question, executed SQL, result columns/rows, query interpretation, and selected coverage caveats to the same provider for a second structured response (`answer`, `caveats`). The owner explicitly requested result-to-model synthesis. Disclose this data flow and up to two paid calls per answered question. No raw audit records or contact-email column are sent; result identifiers/names may be sent. Treat every result cell as untrusted data, never as instructions. Bound the synthesis input to 32 KB; if oversized, failed, refused, or malformed, show deterministic results with a clear summary-unavailable note. Unsupported questions use only the first call.

The answer should lead with the finding, format currency/percentages, state relevant as-of/coverage assumptions, and avoid unsupported claims or new calculations. It remains an AI summary, not independent verification. Show a readable result table and actual multiline SQL beneath it. Wrap prose to terminal width, remove JSON quoting from human output, escape terminal control codes, and use vertical records if tables would be too wide. Machine-readable output keeps original values and column names. `ask --no-summary` and guided `/summary` permit SQL-only operation; live SQL regression cases disable synthesis and keep their seven-call contract.

### Basic malicious-input guard — owner-requested amendment

Before a paid call, reject empty/oversized questions, terminal control characters, high-confidence requests to ignore/override instructions, reveal secrets/system prompts, or mutate the database. This is a small heuristic prefilter, not a complete prompt-injection detector. SQL authorization remains the enforcement boundary regardless of wording. Query results may contain malicious strings; synthesis receives them only as untrusted evidence, has no action tools, and its output is escaped for terminal display. A prose summary can still be wrong; keep the local evidence visible. Test preflight rejection without provider calls, safe ordinary questions, result-cell injection isolation, and deterministic-result preservation on summary failure.

## Guided provider choice — added before implementation

The owner requested OpenAI or Claude selection and hidden API-key entry within the one-command journey. Save newly entered keys through the OS credential store as specified above; reuse saved entries automatically. Allow an explicit model identifier (with editable examples). Existing environment or `.env` values can be reused. `LLM_PROVIDER` selects `openai` (default) or `anthropic`; Claude uses `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`. The machine CLI also accepts `--provider`.

The guided `/evaluate` command runs the seven-case live regression set using the session's provider/key after a visible paid-call count prompt. It requires an explicit yes; offline tests remain separately available without credentials.

### Affordable defaults and key onboarding — owner-requested amendment

Preselect `gpt-5.6-luna` for OpenAI and `claude-haiku-4-5-20251001` for Claude, verified against official model/pricing documentation on 2026-09-15. Enter accepts the shown model; a typed ID or configured model overrides it. Set OpenAI Luna reasoning effort to `none` for these bounded query plans to avoid spending the output budget on hidden reasoning; other model overrides retain provider defaults. Show dated standard input/output rates with a pricing link, plus numbered sign-in, billing, key-creation, and hidden-entry instructions in the CLI and README. Do not create accounts, buy credits, or save keys automatically. Claude onboarding should request a key scoped to a single workspace; multi-workspace key headers are not supported by this prototype.

Claude uses the fixed Anthropic Messages endpoint `https://api.anthropic.com/v1/messages` with the same schema/metric contract, a forced `query_plan` client tool, and local validation of exactly one tool plan. No tool result or invoice data is sent back. Apply the same timeout, redirect rejection, error sanitization, and no-retry policy. Provider integration checks with mocked responses are not live model evaluations.

## SQL execution boundary: the chosen production-hardening feature

- Open the database with SQLite URI mode=ro and query_only. Allow one SELECT/WITH statement.
- Use SQLite's authorizer to allow reads from `invoices` and `accounts` only, SELECTs and a small aggregate/date/string function allowlist. Deny writes, DDL, ATTACH, PRAGMA, internal/raw tables, extension functions, and recursive queries.
- Add an instruction/time budget and a maximum output row count; error on oversized results rather than silently truncating them. Bound question and SQL length. Do not expose contact_email to generated SQL even though it exists in the private local invoice table.
- This controls access and resource use, not semantic correctness. A safe SQL query can still answer the wrong question. Validate meaning with independent evals, clear metric definitions, and human review.

## Answer contract

### Terminal presentation

Use a small standard-library ANSI helper for the guided journey: cyan headings/table headers, blue prompts, magenta SQL labels, green success, yellow caveats, red errors, and subdued separators/timing. Keep textual status labels so color is never the sole signal. Apply styles after calculating table widths. Disable styling for redirected output, `NO_COLOR`, `TERM=dumb`, and Windows terminals without a known ANSI-capable host. Machine-readable JSON commands remain plain.

JSON output includes question (for ask), sql, columns, rows, interpretation (model-generated for ask), timing, and coverage report. Coverage always states excluded invoice groups, ambiguous/inferred date warnings, account snapshot assumptions, FX precedence, and as-of date. Currency columns should be labeled `_usd` or `_usd_cents`. Provenance is traceable using invoice_id and the inspect command; aggregate answers show their query/filter and coverage, not a claim that every row was individually cited.

## Limitations to preserve

No live-model accuracy claim without API execution. Offline demo SQL is manually authored. Mocked provider tests verify parsing/error handling, not real model behavior. No arbitrary-language guarantee, period churn inference, distributed data platform, deployment, or production compliance claim. No API credentials are required for ingestion, offline demo, or deterministic evaluations.
