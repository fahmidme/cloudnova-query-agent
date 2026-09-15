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

## 2026-09-15 13:09 UTC — Secure persistence and owner-requested pause

Added OS-protected persistence for entered API keys/model choices: macOS Keychain via native Security APIs, Windows Credential Manager, and Linux Secret Service through an available `secret-tool`. Secrets are passed in memory or stdin, never subprocess arguments or plaintext fallback files. Saved entries are reused automatically without another key prompt or confirmation; `/key` replaces and `/forget` removes the active provider's saved entry. Explicit environment/.env values retain precedence. Unavailable/locked storage is reported honestly and the active session remains usable.

**Verification:** 43 offline tests passed on Python 3.12.14 and 3.14.2; six independent answer checks passed. New checks cover automatic reuse without getpass, unavailable-store behavior, explicit configuration precedence, serialization/deletion, and Linux stdin secret transport. A real macOS Keychain test wrote, read, updated, deleted, and verified absence of a temporary synthetic entry. Windows/Linux backends remain unverified on their respective platforms. No real API key was accessed in the tests and no paid API call was made.

**Pause:** owner is taking a break and waiting for the account/FX clarification email. Implementation began at 12:15 UTC; this final checkpoint is approximately 54 minutes later, leaving roughly six minutes against the original one-hour implementation timebox. Earlier preparation is separate. Remaining work when resumed: apply confirmed business answers and verify live synthesis/provider regressions. Do not continue feature work during the pause.


## 2026-09-15 — Resumed native tool-calling refactor

Owner explicitly resumed work to replace the rigid SQL/unsupported planner with a
small agent-style conversation, without question-to-answer mappings. Specification
`04845c0` preceded the implementation. Consulted official OpenAI function-calling
and Claude tool-call/result documentation.

Replaced the old JSON planner and separate summary module with automatic native
`query_database` calls and a bounded continuation in the same conversation. The
model can answer directly or ask a clarification. Code enforces one SQL attempt,
two provider requests, strict tool-name/argument checks, no retries, and the existing
read-only SQLite limits. Added three-turn/12 KB session history, `/clear`, automatic
clearing on provider/key/sharing changes, and local-only result handling with
`/summary` disabled. Prompts and metric rules now live in `app/prompts.py`.

**Verification at implementation commit:** 54 offline tests passed on Python 3.12.14
and 3.14.2, plus all six independent curated SQL cases. Migrated old provider and
summary tests to native tool contracts; added actual local SQL round trips with
mocked HTTP for both providers, error feedback, no second tool execution, history
bounds/clearing, opt-out privacy, and result preservation. No external framework or
runtime dependency was added.

**Live smoke:** using the saved OpenAI configuration and original synthetic fixture,
a capabilities reply used one call, the regional MRR answer used two calls and
returned NA $269.50, a contextual “What about EMEA?” returned $99.00 using two calls,
and profit received an expense-data explanation using one call. The initial
capabilities reply incorrectly said local-currency data was unavailable; clarified
that prompt rule and a one-call recheck correctly described separate-currency totals.
This is seven successful paid calls, not a comprehensive accuracy claim. The full
seven-case live regression and fresh public clone are checked separately below.

**Accounting:** this is a new session beginning approximately 16:13 UTC, beyond the
earlier 54-minute implementation checkpoint. It must not be represented as fitting
inside the original hour. External account/FX clarification remains pending.


**First full live regression:** GPT-5.6 Luna passed 5/7 cases. The highest-region query
returned four ranked regions instead of the requested single winner. The period-churn
reply correctly refused calculation but incorrectly proposed an earlier as-of
re-import and omitted the opening cohort requirement. Updated general prompt rules
for result cardinality and the distinction between snapshot churn and period churn;
independent expected rows were unchanged. Reran the seven cases after that correction.


**Final live regression:** all 7/7 cases passed with `gpt-5.6-luna` after the prompt
correction: paid revenue $2,710; refunds $49 and net $2,661; one winning region NA
$269.50; Enterprise/Starter snapshot churn 100%/0%; the five expected accounts/CSAT
flags; two pending/failed invoices with $247 exposure; and a period-churn explanation
explicitly requiring both opening accounts and dated events. Manually read that
explanation in addition to the harness's limited text check. This run disables the
final answer call for SQL cases and does not score prose accuracy. Session live
verification used 21 provider requests in total (smoke/recheck plus two seven-case
runs), all on the original synthetic fixture. No private supplied ledger was sent.


**Fresh public clone, 16:23 UTC:** anonymously cloned `35cf290` with global Git
configuration disabled. `python3 run.py` created an empty Python 3.12.14 virtual
environment; the guided sample journey, all 54 tests, `/clear`, `/summary`, and normal
exit passed. The six independent offline answer cases passed separately. The venv
had no third-party packages, user site-packages were disabled, and generated outputs
left Git clean. This check made no provider calls. The published implementation is
ready for owner review; Claude live and Windows/Linux runtime checks remain open.

**Time checkpoint:** this resumed refactor took approximately 10–11 additional
minutes, bringing the two implementation sessions to roughly 64–65 minutes. Earlier
repository preparation and research are separate. No claim of completion inside the
original one-hour timebox is made.


## 2026-09-15 — Reviewer-focused README refresh

Owner requested a more useful, visually polished README with GitHub badges, separate
application/agent architecture diagrams, and colored CLI examples without excessive
length. Restructured the landing page around quick start, a contextual answer preview,
model selection, two diagrams, key data decisions, verification, and continuation.
Moved detailed API-key onboarding, configuration, scripted commands, troubleshooting
and development links to `docs/REVIEWER_GUIDE.md`; session commands are collapsible.

Added four self-contained SVG badges with truthful stack/recorded-test labels (no
fictional CI status). External badge requests returned HTTP 403 in this environment,
so local assets avoid that dependency. The colored CLI preview uses the real terminal
formatter and the recorded EMEA answer from the original synthetic-fixture smoke
check. A standard-library generator recomputes and asserts its SQL rows, then exports
SVG and accessible plain text. No API key is read and no live call is made. The title
bar is documentation framing; no latency is invented. Preview provenance and the
reproduction command are documented beside the assets.

**Checks:** regenerated the preview from the original fixture, verified its expected
columns/rows, checked all relative documentation links, parsed all SVG assets, and
reviewed the local rendering. Application code is unchanged; runtime test counts and
live evidence refer to the previous recorded verification. This documentation polish
is additional work outside the earlier implementation time checkpoints.


**Owner visual feedback and correction:** the first SVG stretched text through fixed
`textLength` sizing. Removed forced widths and switched to natural monospace text
with colored spans, preserving spaces without distorting glyphs. Trimmed irrelevant
trailing spaces from the plain-text export. Inspected the corrected preview in the
published GitHub README: normal glyph proportions and aligned table columns. Also
verified the four badge images, both rendered Mermaid diagrams, quick-start layout,
and collapsed command section on GitHub. The local preview browser URL was blocked;
GitHub verification used the explicitly authorized public README after publication.


## 2026-09-15 — Locked submission checkpoint

Owner selected the current implementation for submission without further feature
work. The account identity/latest-invoice and recorded-amount/FX choices remain
explicit assumptions, with no external confirmation claimed. Updated the README and
handoff to distinguish these chosen submission assumptions from resolved business
questions. The annotated `submission-v1` tag freezes this review version.

Verification carries forward from the recorded implementation and README checks:
54 offline tests, six independent SQL cases, seven passing live OpenAI cases after
the documented corrections, and fresh-clone setup. No new runtime code or paid API
calls were added for this checkpoint. The original timebox overrun remains disclosed.
The recruiting response is prepared separately as an unsent email draft; no private
correspondence is committed and no send is implied by this checkpoint.
