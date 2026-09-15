# Handoff

## Implemented state

Track B is implemented as a Python standard-library application with original offline fixtures, atomic SQLite import, auditable cleaning, account modeling, read-only question execution, OpenAI/Claude adapters, and a one-command guided reviewer journey. The owner resumed work to replace the SQL-only planner with a bounded native tool-calling conversation. Start with `python3 run.py` from the repository directory.

Read README → this file → BUILD_LOG → relevant specs. Detailed reviewer setup and commands now live in `docs/REVIEWER_GUIDE.md`; `docs/assets/README.md` explains the reproducible CLI preview. The project is organized for another human or coding agent to continue; no A2A network/protocol is required.

## Code map

- `bootstrap.py`, `run.py`: local environment and entry point.
- `app/pipeline.py`: ingestion, grouping/quarantine, coverage orchestration.
- `app/normalize.py`, `app/dates.py`, `app/policies.py`: canonical fields, evidence-based date inference, Decimal money and business rules.
- `app/modeling.py`: one provisional as-of snapshot per account.
- `app/storage.py`: schema/constraints, atomic replacement, local provenance inspection.
- `app/query.py`: SQLite authorizer, restricted columns/functions, resource limits.
- `app/credentials.py`: native macOS/Windows vaults and Linux Secret Service, no plaintext fallback; `/key` replaces and `/forget` removes saved entries.
- `app/provider_options.py`: dated affordable defaults, pricing references, and numbered API-key onboarding links.
- `app/provider.py`, `app/config.py`: native OpenAI/Claude tool-call adapters, explicit model/provider settings, sanitized transport errors, no automatic retries.
- `app/service.py`: one optional SQL tool execution, native result continuation, and two-request limit.
- `app/prompts.py`: editable conversational instructions, invariant metric rules, allowed schema and coverage.
- `app/conversation.py`: three-turn/12 KB in-memory history; `/clear` and provider/key/sharing changes reset it.
- `app/guardrails.py`: basic malicious-input prefilter; SQL authorization remains the enforcement boundary.
- `app/presentation.py`: wrapped prose, readable currency/headers, multiline SQL, and safe terminal rendering.
- `app/__main__.py`, `app/guided.py`: JSON commands and terminal journey.
- `app/terminal.py`: dependency-free semantic colors with TTY, `NO_COLOR`, and terminal-support checks; table widths are calculated before styling.
- `app/evaluate.py`, `tests/`: independent expected answers and contract/safety tests.

## Verification evidence

- 54 offline tests pass on Python 3.12.14 and 3.14.2 after the tool-calling refactor.
- Six curated SQL answer cases match the independently committed fixture specification.
- A real terminal check selected Claude and entered a synthetic key without echoing it; no API call was made.
- Supplied ledger imported locally: 5,125 records, 5,000 invoice groups, 4,984 accepted invoices, 109 equivalent copies collapsed, 16 quarantined groups, 3,803 account snapshots.
- Supplied-data flags: 1,171 date inferences, 142 invalid emails, 1,603 price/FX mismatches, 980 uncertain account snapshots. Counts are issue events, not all distinct affected invoices.
- Two excluded groups have contradictory sign/status and unknown financial bounds; do not present a complete total revenue range for this ledger.
- The source copy fetched for local analysis was newline-normalized. The database hashes the actual local input bytes; do not call that hash a verification of the original Drive file bytes.
- Earlier owner-provided screenshot/transcript established live GPT-5.6 Luna planning and two summaries on the old flow. The refactored agent also passed a live sample smoke: capabilities, regional MRR ($269.50), contextual EMEA follow-up ($99.00), and profit refusal. Initial live regression was 5/7: extra ranking rows and misleading period-churn guidance were actual failures. After general prompt corrections, all 7/7 cases passed on a fresh regression run; both runs are recorded in BUILD_LOG. Claude remains mocked-contract verified only.
- Query turns send SQL result rows/coverage as a native tool result to the same provider by default; `/summary` or `ask --no-summary` disables this. Recent guided conversation also goes to the provider; no raw audit records or contact column are sent. The seven-call SQL eval disables result sharing. Direct replies have `status=conversation`; successful queries `answered`; rejected queries remain `query_error`.
- Fresh public clone of `35cf290`: guided journey, 54 tests, six answer checks, history clearing, summary toggle and normal exit passed in an empty Python 3.12.14 venv. Generated artifacts left Git clean. See BUILD_LOG for the final live 7/7 regression and earlier checkpoints.

## Business questions still awaiting clarification

1. Is `account_id` authoritative despite inconsistent company names, and is the latest accepted invoice a suitable snapshot?
2. Should recorded amounts multiplied by the stated FX rates prevail when list pricing disagrees?

Current behavior is provisional and visible in every query's coverage report. No reply is assumed. If clarified, amend specs first, then change isolated policy/modeling modules and independent expected results where the business meaning changes.

## Current scope

The owner resumed specifically for the small tool-calling refactor. Complete that
refactor and its verification, then stop for review. Do not assume business-policy
clarifications have arrived. Secure key persistence continues to reuse saved entries;
environment/`.env` overrides win. History is session-only and is separate from keys.

## Next concrete checks

1. Review the recorded live OpenAI regression results; Claude live behavior is still a separate unverified gate. The optional seven-call eval checks SQL and limited unsupported wording, not broad prose accuracy.
2. Apply external business clarification when received.
3. Run the one-command journey on Windows/Linux before claiming those platforms verified.

Do not commit credentials, supplied data, private correspondence, generated databases, or raw API output. `.env` and `work/` are ignored. Maintain incremental commits and distinguish offline/provider/publication evidence. Implementation began at 12:15 UTC; preparation happened earlier and must not be folded into a fictitious one-hour total.
