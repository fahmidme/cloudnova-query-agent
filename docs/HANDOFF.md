# Handoff

## Implemented state

Track B is implemented as a Python standard-library application with original offline fixtures, atomic SQLite import, auditable cleaning, account modeling, read-only question execution, OpenAI/Claude adapters, and a one-command guided reviewer journey. Start with `python3 run.py` from the repository directory.

Read README → this file → BUILD_LOG → relevant specs. The project is organized for another human or coding agent to continue; no A2A network/protocol is required.

## Code map

- `bootstrap.py`, `run.py`: local environment and entry point.
- `app/pipeline.py`: ingestion, grouping/quarantine, coverage orchestration.
- `app/normalize.py`, `app/dates.py`, `app/policies.py`: canonical fields, evidence-based date inference, Decimal money and business rules.
- `app/modeling.py`: one provisional as-of snapshot per account.
- `app/storage.py`: schema/constraints, atomic replacement, local provenance inspection.
- `app/query.py`: SQLite authorizer, restricted columns/functions, resource limits.
- `app/credentials.py`: native macOS/Windows vaults and Linux Secret Service, no plaintext fallback; `/key` replaces and `/forget` removes saved entries.
- `app/provider_options.py`: dated affordable defaults, pricing references, and numbered API-key onboarding links.
- `app/provider.py`, `app/config.py`: explicit model/provider settings, one structured plan, sanitized transport errors, no automatic retries.
- `app/service.py`: question validation, planning, execution, and optional answer synthesis.
- `app/guardrails.py`: basic malicious-input prefilter; SQL authorization remains the enforcement boundary.
- `app/summary.py`: bounded result-to-model answer synthesis, with computed results preserved on failure.
- `app/presentation.py`: wrapped prose, readable currency/headers, multiline SQL, and safe terminal rendering.
- `app/__main__.py`, `app/guided.py`: JSON commands and terminal journey.
- `app/terminal.py`: dependency-free semantic colors with TTY, `NO_COLOR`, and terminal-support checks; table widths are calculated before styling.
- `app/evaluate.py`, `tests/`: independent expected answers and contract/safety tests.

## Verification evidence

- 43 offline tests pass on Python 3.12.14 and 3.14.2.
- Six curated SQL answer cases match the independently committed fixture specification.
- A real terminal check selected Claude and entered a synthetic key without echoing it; no API call was made.
- Supplied ledger imported locally: 5,125 records, 5,000 invoice groups, 4,984 accepted invoices, 109 equivalent copies collapsed, 16 quarantined groups, 3,803 account snapshots.
- Supplied-data flags: 1,171 date inferences, 142 invalid emails, 1,603 price/FX mismatches, 980 uncertain account snapshots. Counts are issue events, not all distinct affected invoices.
- Two excluded groups have contradictory sign/status and unknown financial bounds; do not present a complete total revenue range for this ledger.
- The source copy fetched for local analysis was newline-normalized. The database hashes the actual local input bytes; do not call that hash a verification of the original Drive file bytes.
- Owner-provided screenshot shows a successful live GPT-5.6 Luna region/MRR question on the fixture. New answer synthesis, Claude live behavior, and the full live regression set remain unverified. Mocked contract checks do not establish model accuracy.
- Answered questions now send SQL result rows and coverage to the selected provider for a second call by default; `/summary` or `ask --no-summary` disables this. No raw audit records or contact column are sent. The seven-call SQL eval disables synthesis.
- Fresh public clone of `917a68b`: guided journey, 32 tests, six answer checks, demo, and quarantine inspection passed in an empty Python 3.12.14 venv. Generated artifacts left Git clean. See BUILD_LOG for timing and exact scope.

## Business questions still awaiting clarification

1. Is `account_id` authoritative despite inconsistent company names, and is the latest accepted invoice a suitable snapshot?
2. Should recorded amounts multiplied by the stated FX rates prevail when list pricing disagrees?

Current behavior is provisional and visible in every query's coverage report. No reply is assumed. If clarified, amend specs first, then change isolated policy/modeling modules and independent expected results where the business meaning changes.

## Paused at owner request

The owner is taking a break and waiting for external business clarification. Complete no additional features until resumed. Secure persistence is the final requested change: saved keys are reused automatically; environment/`.env` overrides win. macOS write/read/update/delete passed using a removed synthetic entry; Windows/Linux remain unverified. Old session-only key entries cannot be recovered automatically.

## Next concrete checks

1. If a local key is available, run `python -m app evaluate --live --provider openai` or `anthropic`, record exact model/results, and investigate failed semantic cases. This makes up to seven paid calls.
2. Apply external business clarification when received.
3. Run the one-command journey on Windows/Linux before claiming those platforms verified.

Do not commit credentials, supplied data, private correspondence, generated databases, or raw API output. `.env` and `work/` are ignored. Maintain incremental commits and distinguish offline/provider/publication evidence. Implementation began at 12:15 UTC; preparation happened earlier and must not be folded into a fictitious one-hour total.
