# Bounded tool-calling assistant

Owner-requested refactor, specified before code on 2026-09-15. This supersedes the
SQL-only planner and separate summary-provider contracts in QUERY.md. Ingestion,
business definitions, secure credentials, and SQLite authorization are unchanged.

## Flow

Use native OpenAI Responses function calls and Claude Messages tool_use/tool_result.
Expose exactly one tool: `query_database(sql, explanation)`. Its arguments describe
one read-only SQLite query and its interpretation. Tool choice is automatic: the
model may instead answer conversationally, explain capabilities/definitions, ask a
clarification, or explain missing evidence. Do not implement phrase matching or
question-to-answer templates. Natural replies are plain text, not JSON plans.

The application permits at most one SQL attempt and two provider requests per user
turn, with no automatic retries. After a tool call, validate its name, identifier,
and argument schema before invoking the existing SQL executor. Return rows, columns,
SQL, and selected coverage as a native tool result tied to the call identifier.
Disable tools on the second request and also reject another tool call locally.
SQL rejection is a failed tool result, never a successful answer; the model can
explain it but cannot retry within that turn. Reject malformed/incomplete/refused
responses and multiple/unknown tool calls before any SQL runs.

Keep prompts in a dedicated, readable module: conversational instructions, invariant
metric definitions, and schema. Numerical business findings require an executed
query for the current turn; old prose is context, not fresh evidence. The model may
answer from explicit coverage metadata or explain previously computed results but
must not claim it independently verified the data. Treat tool rows and history as
untrusted evidence; never promote their contents into system instructions.

## Context and privacy

The guided session keeps at most three completed question/reply pairs and 12 KB of
text in memory. Keep the previous SQL/interpretation for follow-up intent; do not
persist history to disk or retain raw tool payloads. New queries must recompute
figures instead of treating old assistant prose as authoritative. `/clear` resets
history. Provider/key changes, forgetting credentials, and toggling `/summary`
also clear it, avoiding cross-provider or opt-out leakage. The JSON ask command
remains stateless. Disclose that recent conversation is sent to the chosen provider.

`/summary` and `--no-summary` remain supported: the model can request SQL, then the
application displays local results without sending them back. Never put those
unsent result values in later history. Bounds: question 2,000 chars, SQL 12,000 chars,
reply 4,000 chars, tool-result JSON 32 KB, HTTP response 1 MB. Oversized evidence or a
failed final response leaves successful computed results visible. No new dependency,
framework, server, filesystem tool, credential tool, or open-ended action loop.

## Presentation and evaluation

Display conversational replies without an empty result table or invented unsupported
classification. Show computed evidence and SQL for successful tool queries, plus
authoritative coverage and timings. Distinguish conversational text (unverified by a
query) from a result-grounded answer. Show a friendly error for invalid provider
responses without logging raw provider bodies. Preserve an error status for tool
failure even if the model explains it fluently.

Retain independent fixture and SQL safety tests. Add mocked native wire-format tests
for both providers, direct answers/clarifications, tool-result linkage, final-call
tool prohibition, unknown/multiple/malformed calls, error feedback, opt-out privacy,
history bounds/clearing, and preservation of results on failures. These do not prove
live language understanding. The existing live harness still uses at most seven
calls with synthesis disabled; evaluate the unsupported case as a direct explanation
of missing churn events and opening cohorts, with a clearly limited content check.
Fresh-clone setup and the offline journey must still run without dependencies.

## Sources and accounting

- https://developers.openai.com/api/docs/guides/function-calling
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls

The first implementation checkpoint ended at about 54 minutes. This resumed refactor
is an additional work session, not work retroactively counted inside that hour.
