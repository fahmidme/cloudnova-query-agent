# Handoff

## Current state

- Track B selected: a cleaning/modeling pipeline with a natural-language query layer.
- Owner requested a minimal public repository scaffold first, then a pause before implementation.
- README, agent instructions, build log, handoff, and ignore rules are present.
- No application code, dependencies, data, business specification, container, or tests exist yet.

## Accepted direction

- Small Python modules, local SQL storage, and a thin AI query interface.
- Easy reviewer setup with Python already installed, a project-local virtual environment, and pinned dependencies. Docker is not required.
- Understandable code with useful comments, traceable decisions, and honest incremental commits.
- Agent-readable context committed alongside the work.

## Next step, after the owner starts implementation

Read the supplied business context and assessment requirements, then write the actual specification and evaluation expectations before coding. Record active work time and preparation honestly against the assessment timebox.

Resolve and document deduplication, ambiguous dates, account-level subscription state, revenue/refund semantics, and treatment of invalid records. Choose the database, dependency management, model provider/configuration, and precise demo contract. Decide how reviewers obtain the supplied dataset without publishing private source material by accident.

## Planning clarification — 2026-09-15

The owner accepted an installed Python runtime as a reviewer prerequisite and preferred a simpler setup over Docker. Read-only inspection of the supplied CSV began to ground the business-rule discussion in actual records. This is preparation, not an implemented pipeline or a completed specification.

## Validation status

This scaffold has no runtime behavior to test. Repository and remote verification should be reported separately from future application, container, evaluation, and live-model verification. A successful push does not prove any planned application behavior.
