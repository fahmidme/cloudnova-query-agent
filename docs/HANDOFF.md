# Handoff

## Current state

- Track B selected: a cleaning/modeling pipeline with a natural-language query layer.
- Owner requested a minimal public repository scaffold first, then a pause before implementation.
- README, agent instructions, build log, handoff, and ignore rules are present.
- No application code, dependencies, data, business specification, container, or tests exist yet.

## Accepted direction

- Small Python modules, local SQL storage, and a thin AI query interface.
- Easy reviewer setup in an isolated environment; container-based setup is the proposed implementation route.
- Understandable code with useful comments, traceable decisions, and honest incremental commits.
- Agent-readable context committed alongside the work.

## Next step, after the owner starts implementation

Read the supplied business context and assessment requirements, then write the actual specification and evaluation expectations before coding. Record active work time and preparation honestly against the assessment timebox.

Resolve and document deduplication, ambiguous dates, account-level subscription state, revenue/refund semantics, and treatment of invalid records. Choose the database, dependency management, model provider/configuration, and precise demo contract. Decide how reviewers obtain the supplied dataset without publishing private source material by accident.

## Validation status

This scaffold has no runtime behavior to test. Repository and remote verification should be reported separately from future application, container, evaluation, and live-model verification. A successful push does not prove any planned application behavior.
