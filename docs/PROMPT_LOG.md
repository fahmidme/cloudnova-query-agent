# Selected development conversation

This is a trimmed reconstruction of relevant user direction and assistant decisions, not a raw transcript. Summaries are labeled; chronology is preserved. Setup and research preceded implementation and are part of the real work history. No claim is made that all preparation plus implementation fits in one hour.

## Preparation — 2026-09-15

1. **User direction (summary):** Inspect the recruiting email and assessment context, then explain Track B.
   **Assistant decision (summary):** Propose a small Python pipeline, local SQL database, and thin natural-language query interface.
2. **User direction (summary):** Create a minimal public repository first, use honest incremental commits, and make code modular, understandable, commented, and easy for another agent to follow. Pause before implementing.
   **Assistant action:** Created the scaffold commit `febe718`; verified an anonymous clone. Wrote AGENTS.md and handoff guidance.
3. **User correction (summary):** Python may be assumed installed; Docker is unnecessary. Show actual problematic data before choosing policies.
   **Assistant action:** Inspected 5,125 source records and documented concrete invoice, date, account-identity, and FX inconsistencies. Revised setup to Python/venv.
4. **User decisions (summary):** Set aside conflicting invoices and report impact. Infer dates from other date evidence where sensible, while flagging them. Accept provisional account/FX handling; clarify revenue terminology.
   **Assistant clarification:** Separate paid revenue, refunds, and net revenue. Quarantined records represent uncertainty bounds, not automatically lost revenue. Account and FX questions were raised for external clarification; no response is assumed.
5. **User direction (summary):** Read the job description to understand expectations.
   **Assistant decision:** Prioritize business rules, specification-first AI direction, independent evaluations, maintainability, and customer-readable explanations. Avoid infrastructure added only to match job-description keywords.

## Implementation begins — 2026-09-15 12:15 UTC

6. **User prompt (verbatim):** "Continue"
   **Assistant plan (summary):** Commit specifications and independent expected answers first; implement modular ingestion, cleaning, modeling, SQL safety, and reviewer setup. Keep pending account/FX policies isolated and provisional.
7. **User provider choice (verbatim):** "OpenAI API with a configurable model"
   **Assistant decision:** Use the Responses API behind a small standard-library adapter. Keep offline ingestion/demo/evaluation independent of credentials. Require explicit model configuration and verify live behavior separately.

8. **Assistant implementation (summary, 12:26 UTC):** Built the pipeline from the committed specs, then ran 18 offline tests against independent fixture expectations. Used SQLite integer cents and Decimal conversion, preserved raw records locally, kept account modeling separate, and corrected connection cleanup to support atomic replacement across operating systems. CLI and live query work follow this milestone.

9. **User direction (summary):** Prefer natural-language questions translated into SQL. Keep the one-hour implementation timebox, include Claude if time allows, and make one command guide reviewers through setup and testing.
   **Assistant decision:** Added a shared SQL-plan boundary, OpenAI Responses and Claude Messages adapters, read-only SQLite authorization and resource limits. Kept all data computation local and provider calls optional.
10. **User direction (summary):** Let reviewers choose the provider and enter their API key inside the journey; preserve incremental commits.
    **Assistant implementation (summary, 12:40 UTC):** Committed the guided specification before code, then added the terminal journey with hidden session-only key input. Split query-layer and guided-journey milestones into separate pushed commits. Ran 32 offline tests, six answer checks, a supplied-data import, and a terminal check with a synthetic key. Live API behavior remains separately unverified.

11. **User prompt (verbatim):** "Lets add some color to the cli"
    **Assistant implementation (summary):** Added a small semantic ANSI palette to the guided terminal, keeping status text, aligned tables, plain redirected output, and `NO_COLOR` support. No new dependencies or provider calls.
