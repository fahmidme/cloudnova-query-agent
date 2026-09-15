# Build log

## 2026-09-15 — Repository preparation

**Owner direction:** Set up a barebones public repository before beginning Track B. Favor modular, understandable code, easy isolated setup, useful comments, and context that another AI agent can follow. Use incremental commits.

**AI contribution:** Codex drafted the repository documentation and ignore rules. Proposed container-based setup with explicit host prerequisites and separable pipeline/query responsibilities. These are plans, not working features.

**Artifacts:** README.md, AGENTS.md, docs/HANDOFF.md, docs/BUILD_LOG.md, .gitignore.

**Checks:** Reviewed the initial file set for scope and public suitability. No runtime tests apply to this documentation-only scaffold. Remote creation, push, and clone verification occur after this commit and should be reported with the actual commit identifier.

**Next:** Wait for the owner to start the implementation stage, then write the business and evaluation specifications first. Repository preparation is part of the real work history and must remain visible.

## 2026-09-15 — Python setup preference and source inspection

**Owner direction:** Show actual data examples behind the unresolved business questions. Assume Python can already be installed on the reviewer's machine; Docker is unnecessary for the initial approach.

**AI contribution:** Updated the setup goals to a local virtual environment, pinned dependencies, and a proposed built-in SQLite database. Inspected the source CSV read-only to identify duplicate invoice conflicts, ambiguous dates, account-state inconsistencies, and a pricing/FX reconciliation issue. No transformation policy was implemented or presented as customer-approved.

**Checks:** The text fetched from the supplied CSV parsed into 5,125 data records. Inspection scripts and source data remain outside the tracked repository. Setup and application behavior are still unimplemented and untested.

## 2026-09-15 12:26 UTC — Core pipeline

Implementation began at 12:15 UTC after owner authorization. Committed specifications and independent expected answers in `e263e17` before application code. Implemented separate policy, date, normalization, modeling, pipeline, and storage modules, with an original 11-record fixture and dependency-free venv bootstrap.

**Verification:** 18 offline unittest cases passed on Python 3.14.2. These cover the hand-calculated revenue/MRR/churn/exposure results, uncertainty bounds, duplicate source references, invalid input, as-of snapshots, date inference, and failed-import preservation. CLI and OpenAI integration are the next milestone and are not verified yet. Earlier preparation remains separately visible in this log.

## 2026-09-15 12:35 UTC — Query layer and provider adapters

Added a machine-readable CLI, bounded read-only SQL execution, OpenAI Responses structured plans, and an optional Claude Messages tool-plan adapter. Provider settings use explicit model IDs and never expose keys in object representations. Shared orchestration computes answers locally.

**Verification:** 27 offline tests passed. New checks cover forbidden tables/columns/writes/recursive queries, row and instruction budgets, CTE aggregates, malformed/refused provider output, sanitized HTTP errors, and mocked question execution/unsupported responses. A test caught SQLite's database-name omission for COUNT(*) authorization; the narrow allowed-table fix now passes. Both provider integrations remain unverified with live credentials. Demo answers use curated SQL.

## 2026-09-15 12:40 UTC — Guided reviewer journey and answer harness

Added `python run.py`: automatic isolated setup, sample/custom CSV selection, quality and uncertainty reporting, curated SQL examples, optional offline tests, OpenAI/Claude selection, explicit model choice, and hidden session-only API key entry. The menu shares query orchestration with the JSON CLI. Added six independent offline answer checks and an optional seven-call live regression command.

**Verification:** 32 offline tests passed; all six curated answer cases passed. Ran the guided flow through a real terminal, selected Claude, entered a synthetic key, and verified the key was not echoed. No paid request was made in that check. Also exercised scripted offline examples and graceful EOF. The local supplied-data import read 5,125 records: 4,984 accepted invoices, 109 equivalent copies collapsed, 16 groups quarantined, 3,803 provisional account snapshots. Two quarantined groups have contradictory amount signs and unknown financial bounds. Full source data and generated databases remain untracked. These counts verify execution, not customer approval of provisional policies.

## 2026-09-15 12:44 UTC — Fresh public clone and completion checkpoint

Cloned public commit `917a68b` with the global Git configuration disabled and an empty credential helper. From that new checkout, `python3 run.py` created a fresh Python 3.12.14 venv. Ran the guided sample journey, all 32 tests, all curated examples, and quarantine provenance inspection. Separate `app evaluate` and `app demo` commands passed. Verified the venv disables user site packages, its site-packages directory is empty, and the checkout remains clean after generated artifacts are created.

README now includes exact reviewer commands, module-linked specifications, an architecture diagram, business assumptions, verification limits, and next-day work. The selected prompt log is a labeled reconstruction; handoff state is current. Provider adapter implementation references the official OpenAI Structured Outputs and Anthropic Messages documentation.

**Time accounting:** implementation ran from approximately 12:15 to 12:44 UTC (about 29 minutes) for this checkpoint. Earlier repository setup, research, and policy discussion are separate preparation and are not represented as part of a one-hour total. No real API credential was available in the project, so live OpenAI/Claude execution and the seven-case live harness remain unverified. No customer clarification reply is assumed. Windows/Linux are documented targets, not verified environments.

## 2026-09-15 12:53 UTC — Requested CLI color polish

Added a dependency-free semantic color helper and applied it to guided headings, prompts, table headers, SQL labels, success, warnings, and errors. Color is supplementary to textual labels and is disabled for redirected output, `NO_COLOR`, dumb terminals, and Windows consoles without a recognized ANSI host. Amended the presentation specification before implementation.

**Verification:** all 32 existing tests passed. Checked colored terminal output, plain pipe output, `NO_COLOR`, dumb-terminal fallback, and equal table alignment after removing ANSI sequences. Ran the complete offline journey through redirected input/output. No live API calls or new packages. This polish checkpoint is about 38 minutes after the implementation start; earlier preparation remains separate.

## 2026-09-15 12:55 UTC — Affordable model defaults and API-key onboarding

Owner requested a current, affordable preselected model and exact steps/links for obtaining API keys. Official documentation identifies GPT-5.6 Luna as OpenAI's cost-sensitive model (standard short-context $0.20 input / $1.20 output per million tokens); Claude's current least-expensive option is Haiku 4.5 ($1 / $5). Added these dated defaults, console/billing/key links, and numbered setup steps. Enter accepts the displayed default; configured or typed models remain explicit overrides. Luna uses its supported `none` reasoning setting for bounded SQL generation. Claude setup requests a single-workspace key to match the adapter's header support.

**Verification:** 32 existing tests passed. Additional local checks exercised Enter acceptance for both defaults, missing-model configuration fallback, onboarding links, no key echo, and the Luna request's reasoning setting through a mocked transport. No live API request was made. This checkpoint is about 40 minutes after implementation began; earlier preparation remains separate.

## 2026-09-15 13:03 UTC — Readable answers, synthesis, and guardrails bonus

Owner provided a screenshot of a successful live Luna query and requested a more human-readable answer with SQL results sent to the LLM. Added `summary.py` for a second structured provider call using executed rows/columns, SQL, interpretation, and selected coverage; raw audit data and the contact-email column remain excluded. Added `presentation.py` for wrapped prose, readable headers/currency, actual multiline SQL, and vertical fallback for wide tables. Summary failures/oversized inputs preserve the computed result. The CLI discloses up to two calls and result sharing; `/summary` and `ask --no-summary` disable synthesis. The seven-case live SQL eval still uses at most seven calls and does not evaluate prose.

Owner also requested basic malicious-input protection and the assessment bonus. Added a narrow preflight heuristic for instruction overrides, credential requests, destructive commands, and control characters, with SQLite authorization retained as the real data-access boundary. Result cells are untrusted evidence for synthesis; the model receives no action tools. Terminal rendering escapes controls. Rechecked the assessment document: input/SQL guardrails satisfy its suggested one production-hardening bonus, now explicitly documented with verification commands.

**Verification:** 38 offline tests passed on Python 3.12.14 and 3.14.2; six independent SQL answer cases still passed. New cases cover pre-call malicious rejection, malicious text isolated in result evidence, no raw/contact payload leakage, summary size/schema bounds, provider failure preserving results, opt-out/unsupported paths skipping synthesis, readable currency/SQL, and control-character escaping. Exercised the one-command offline journey and inspected a sample rendered answer with fixture figures and a supplied example summary. That preview was not a live model response. The owner's screenshot establishes one live planning/query example; new synthesis and complete live regressions remain unverified. This checkpoint is about 48 minutes after implementation began, excluding earlier preparation.

**Fresh-clone follow-up:** public commit `1a64aca` passed a new clone's `python3 run.py` setup, all 38 tests, readable result output, `/summary` toggle, and all six offline answer checks. Generated files left the checkout clean. This remains offline evidence; no synthesis API call was made.
