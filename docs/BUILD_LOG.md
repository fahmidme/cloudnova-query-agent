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
