# Working in this repository

## Read order

1. README.md
2. docs/HANDOFF.md
3. docs/BUILD_LOG.md
4. Relevant specifications under specs/ once they exist

## Current boundary

This is the repository setup stage. Do not begin Track B implementation until the owner explicitly starts that work. Do not create placeholder application code or claim planned capabilities are implemented.

## Specification and implementation

- Write the specification before the code it governs. Record unresolved business questions and explicit assumptions; do not invent customer rules.
- Prefer a small Python pipeline, a local SQL store, and a thin question interface. Confirm exact library and provider choices in the specification.
- Keep ingestion, normalization, business modeling, storage, query generation/execution, and evaluation separable. Use clear functions and typed interfaces where useful; avoid frameworks or abstraction layers that add no value.
- Preserve source identifiers so a reviewer can follow a result back to its inputs and transformation choices.
- Use descriptive names, short module docstrings, and comments explaining why a rule exists. Avoid comments that merely repeat the code.
- Constrain model-generated queries to safe, read-only execution. Make unsupported questions, invalid data, missing config, and provider errors explicit.

## Reproducibility and verification

- Aim for a documented container-based demo that avoids host Python/database dependencies. Pin dependencies and document the minimal host prerequisites.
- Verify setup from a fresh clone, not only an existing developer environment. Record exactly what ran and whether it used fixtures, supplied data, or live provider calls.
- Specify evaluation expectations independently from implementation outputs. Include at least one documented expected failure; do not disguise failures as passing results.
- Keep the agreed work timebox honest. Log actual progress and unfinished work, including preparation; do not fabricate timestamps, prompt history, or prior spec authorship.

## Agent-to-agent continuity

Here, agent-to-agent means a repository another agent can understand and continue. It does not require an A2A protocol, autonomous agent network, or extra infrastructure.

- Keep docs/HANDOFF.md current: implemented state, validation evidence, blockers, next concrete step.
- Append concise entries to docs/BUILD_LOG.md for meaningful milestones. Distinguish user direction from agent recommendations.
- Keep a trimmed, accurate prompt/decision trail as implementation proceeds. Exclude unrelated conversation, private email, personal paths, and secrets.
- Use small commits with concrete messages. Do not rewrite history to make the process look different from what happened.
- Follow the owner's current publication scope. Initial scaffold publication is authorized; future steps must respect the active task's instructions.
- Never commit credentials, local environment files, generated databases, or private correspondence. Review staged files before publishing. Assess source-data inclusion separately before adding it to a public repo.
