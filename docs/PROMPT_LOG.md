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

12. **User direction (summary):** Replace the old model example with a current, affordable preselected model; include exact API-key setup steps and links.
    **Assistant implementation (summary):** Checked official provider documentation. Preselected GPT-5.6 Luna and Claude Haiku 4.5, preserved model overrides, and added dated pricing plus numbered console/billing/key instructions to the CLI and README. Verified default acceptance and request configuration locally; no real credential was used.

13. **User direction (summary):** Make the terminal output human-readable and conversational; send SQL results to the model to generate an answer. Add basic malicious-input protection and check the assessment bonus.
    **Assistant implementation (summary):** Added a second bounded provider call for result-grounded prose, readable currency/headers/multiline SQL, graceful summary failure, and an opt-out for result sharing. Added a heuristic malicious-input prefilter alongside SQLite authorization and escaped terminal controls. Rechecked the assessment: input/query guardrails are the selected production-hardening bonus. Added verification commands in the README. A user-provided screenshot demonstrates one live Luna query; the new synthesis path remains verified only through offline/mocked checks.

14. **User direction (summary):** Safely persist API keys after first entry instead of repeatedly asking for them. Finish the current change, report time spent, then pause while the owner takes a break and waits for clarification.
    **Assistant implementation (summary):** Added OS credential-store backends and automatic reuse, with `/key` replacement and `/forget` deletion. Preserved explicit environment/.env precedence and session-only operation when secure storage is unavailable. Verified macOS lifecycle using a removed synthetic entry and added mocked credential tests. Recorded the paused state and remaining live/business checks.

15. **User direction (summary):** Reviewed a live CLI transcript showing two successful result summaries and a failed capabilities question. Requested the actual prompts and current/proposed architecture; rejected mapping potential questions to canned answers.
    **Assistant finding:** The first response contract allowed only SQL or unsupported; it had no conversational path or history. The pasted transcript establishes two live OpenAI synthesis examples for the earlier implementation, not a complete regression run.
16. **User prompt (verbatim):** "Look into tool call type of architecture and let's restructure around that. Basically agent style but without overengineering it."
    **Assistant design (summary):** Consulted official native tool-calling documentation and wrote AGENT.md first. One read-only SQL tool, automatic conversational replies, one SQL attempt/two model calls per turn, short session context, and existing security/credential boundaries. This is a resumed extension beyond the earlier 54-minute checkpoint.

    **Assistant implementation (summary):** Implemented native tool calls for both providers, moved prompts into a dedicated module, and added bounded session history. Verified 54 offline checks and live OpenAI conversation/query/follow-up behavior on the original fixture. Live evaluation exposed result-size and period-churn explanation mistakes; corrected the general prompt rules and reran the independent cases. No new runtime dependencies.
