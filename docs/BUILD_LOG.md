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
