# Query and reviewer contract v1

Written before implementation on 2026-09-15.

## Commands to implement

- `python bootstrap.py`: create `.venv`, verify Python 3.11+ and SQLite support, print OS-specific next commands. No packages or network required.
- `python -m app demo`: import the bundled original fixture into `work/demo.sqlite`, show deterministic stakeholder queries and results. Label this as an offline SQL demonstration, not live natural-language generation.
- `python -m app ingest PATH --db PATH [--as-of YYYY-MM-DD]`: validate/import a supplied ledger and print quality report JSON.
- `python -m app ask QUESTION --db PATH`: use OpenAI to generate a query plan, execute read-only SQL locally, return SQL, deterministic result rows, units/metric definition, elapsed time, and data-quality caveats.
- `python -m app sql SQL --db PATH`: inspect a manually supplied read-only query under the same restrictions; not described as AI generation.
- `python -m app inspect INVOICE_ID --db PATH`: show source record numbers, raw records, and quarantine/issues locally for audit.
- `python -m unittest discover -s tests -v`: offline evaluation, independent expected results and safety checks.

## OpenAI configuration

Read `OPENAI_API_KEY` and `OPENAI_MODEL` from the environment or a project-local `.env` file without executing shell syntax. Existing environment values take precedence. Require the model explicitly instead of silently substituting one; provide a documented example. Responses API endpoint is fixed to https://api.openai.com/v1/responses. Use urllib with a timeout and no automatic retry of a possibly completed paid request. Do not follow credential-bearing HTTP redirects. Never log keys or raw HTTP error bodies.

Send only the user's question, a static schema/metric contract, and as-of metadata. Do not send invoice rows, contacts, company names, result rows, or raw source files. Set `store=false`. The model generates a structured plan containing `sql`, `explanation`, and `unsupported_reason`, with nullable sql/reason. Parse/validate this contract locally; reject refusals, incomplete output, multiple messages, malformed JSON, and missing/unexpected fields. Treat model output as untrusted.

For unsupported historical churn, forecasts, or unavailable attributes, return an explicit unsupported response instead of fabricating SQL. Show explanation as model-provided interpretation, not proof of correctness. Deterministic query results are the answer; no second LLM summarization call.

## SQL execution boundary: the chosen production-hardening feature

- Open the database with SQLite URI mode=ro and query_only. Allow one SELECT/WITH statement.
- Use SQLite's authorizer to allow reads from `invoices` and `accounts` only, SELECTs and a small aggregate/date/string function allowlist. Deny writes, DDL, ATTACH, PRAGMA, internal/raw tables, extension functions, and recursive queries.
- Add an instruction/time budget and a maximum output row count; error on oversized results rather than silently truncating them. Bound question and SQL length. Do not expose contact_email to generated SQL even though it exists in the private local invoice table.
- This controls access and resource use, not semantic correctness. A safe SQL query can still answer the wrong question. Validate meaning with independent evals, clear metric definitions, and human review.

## Answer contract

JSON output includes question (for ask), sql, columns, rows, interpretation (model-generated for ask), timing, and coverage report. Coverage always states excluded invoice groups, ambiguous/inferred date warnings, account snapshot assumptions, FX precedence, and as-of date. Currency columns should be labeled `_usd` or `_usd_cents`. Provenance is traceable using invoice_id and the inspect command; aggregate answers show their query/filter and coverage, not a claim that every row was individually cited.

## Limitations to preserve

No live-model accuracy claim without API execution. Offline demo SQL is manually authored. Mocked provider tests verify parsing/error handling, not real model behavior. No arbitrary-language guarantee, period churn inference, distributed data platform, deployment, or production compliance claim. No API credentials are required for ingestion, offline demo, or deterministic evaluations.
