# CloudNova Query Agent

A spec-driven invoice cleaning pipeline and natural-language query agent, built incrementally with AI assistance.

**Status: repository scaffold only.** Track B implementation has not started. There is no runnable application, installer, container, or evaluation harness yet.

## Intended outcome

Turn a messy invoice ledger into queryable, trustworthy data. A reviewer should be able to ask a question, see the generated SQL and answer, and understand the business rules and limitations behind the result.

## Start here

- [AGENTS.md](AGENTS.md): instructions for humans and coding agents.
- [Handoff](docs/HANDOFF.md): current state, next step, and unresolved decisions.
- [Build log](docs/BUILD_LOG.md): concise record of actual work and verification.

## Planned boundaries

These are design goals, not implemented modules:

| Boundary | Responsibility |
| --- | --- |
| Ingestion | Read source records and preserve source row identifiers. |
| Transformation | Normalize, validate, deduplicate, and report rejected or ambiguous records. |
| Modeling | Apply explicit revenue, currency, subscription, and account-level rules. |
| Storage | Keep cleaned records and queryable models in a local SQL database. |
| Question interface | Translate natural language into constrained read-only queries; show SQL and results. |
| Evaluation | Check independently specified expected answers and documented failure cases. |

Prefer small Python modules, explicit inputs and outputs, and a thin command-line entry point. Keep business rules separate from model-provider calls and interface code.

## Reproducible setup target

The implementation should offer a container-based, single-command demo after cloning and documented configuration. The host should not need Python, a database server, or manually installed Python packages. Dependencies should be pinned and installed inside the container.

A supported container runtime must already be installed and running. Initial setup requires internet access to download images and dependencies. Live model calls may require a configured provider API key and network access. A fresh machine with literally no tools cannot run a repository without these bootstrap prerequisites; document them plainly and do not silently install system software.

Validate the eventual instructions from a fresh clone with no existing project environment or generated database. Document credential requirements and whether evaluations can run without paid model calls. The exact command and dependency choices will be specified during implementation; none are available yet.

## Development approach

Write and commit the specification before implementation. Follow with small, truthful commits for each meaningful change. Preserve a concise record of AI direction, decisions, checks, and remaining limitations. Comments should explain business meaning, assumptions, and non-obvious choices.

This repository currently contains original project scaffolding only. Recruiter correspondence, assessment source documents, credentials, and source data are not included in this initial commit.
