# Reviewer guide

[← Back to the README](../README.md)

The fast path is `python3 run.py`. This guide covers provider setup, scripted commands,
and the decisions behind the answers. Start with the bundled original fixture;
provide the assessment CSV locally when you want to evaluate that ledger.

## Models and API keys

Press Enter at **Model ID** to use the preselected affordable model, or type your own. Existing environment/`.env` model choices are preserved.

| Provider | Preselected model | Standard USD price per 1M input / output tokens |
| --- | --- | --- |
| OpenAI | `gpt-5.6-luna` | $0.20 / $1.20, short context |
| Claude | `claude-haiku-4-5-20251001` | $1 / $5 |

Checked **2026-09-15** against [OpenAI model guidance](https://developers.openai.com/api/docs/models/gpt-5.6-luna), [OpenAI pricing](https://developers.openai.com/api/docs/pricing), and [Claude's current model lineup](https://platform.claude.com/docs/en/models/overview). Luna is OpenAI's current cost-sensitive model; Haiku 4.5 is the least expensive model in Claude's current lineup. These are our starting choices for the review, not a measured accuracy ranking. Actual charges depend on tokens and provider rates.

### Get an OpenAI API key

1. Sign in or create an account at [OpenAI Platform](https://platform.openai.com/).
2. Select your organization/project. Open [API billing](https://platform.openai.com/settings/organization/billing/overview) and enable billing or add credits if needed.
3. Open [API keys](https://platform.openai.com/api-keys), choose **Create new secret key**, name it **CloudNova review**, and select your project.
4. Copy the new secret key. Return to this CLI, choose **1 OpenAI**, press Enter for **gpt-5.6-luna**, and paste the key at the hidden prompt.

See the [official OpenAI quickstart](https://developers.openai.com/api/docs/quickstart) for provider setup. This repository already handles the client; no SDK installation is required.

### Get a Claude API key

1. Sign in or create an account at [Claude Console](https://platform.claude.com/).
2. Open [API billing](https://platform.claude.com/settings/billing) and enable billing or add credits if needed.
3. Open [Settings → API keys](https://platform.claude.com/settings/keys). Choose **Create key**, name it **CloudNova review**, link your own account, and scope it to **one workspace**. This prototype does not supply the extra header needed by multi-workspace keys.
4. Copy the key when it is shown at creation. Return to the CLI, choose **2 Claude**, press Enter for **claude-haiku-4-5-20251001**, and paste the key at the hidden prompt.

See [Claude's official key-creation guide](https://platform.claude.com/docs/en/get-api-key). If you cannot create a key or enable billing, ask your organization administrator. API billing is separate from chat subscriptions; this CLI never buys credits. Entered keys use the secure storage described below.

### Secure key persistence

Enter a provider key once; subsequent runs reuse it without another key prompt. The selected model is saved with it. Keys are stored under the OS account in **macOS Keychain**, **Windows Credential Manager**, or **Linux Secret Service** through an available `secret-tool`. No extra Python package is required. Linux needs an unlocked Secret Service and the `secret-tool` utility for persistence; without them the key remains session-only, with a visible notice. OS unlock/access dialogs may still appear.

- `/key`: replace the active provider's saved key.
- `/forget`: remove its saved vault entry and clear the active session key.
- Explicit environment/`.env` credentials take precedence; these commands do not modify those sources.
- Secrets never go into command-line arguments, generated artifacts, or project files. There is no plaintext persistence fallback.

macOS vault write/read/update/delete was verified with a temporary synthetic entry, which was removed afterward. Windows and Linux backends are implemented but not verified on those platforms. Keys entered in an older session-only version must be entered once in this version; earlier sessions did not save them.

## Scriptable commands

After setup, use `.venv/bin/python` below; on Windows use `.venv\Scripts\python.exe`.

```bash
# Offline, machine-readable demonstration
.venv/bin/python -m app demo

# Import a CSV; specify as-of if a historical snapshot is wanted
.venv/bin/python -m app ingest fixtures/invoices.csv --db work/sample.sqlite
.venv/bin/python -m app ingest fixtures/invoices.csv --db work/earlier.sqlite --as-of 2024-12-31

# All unit/contract tests and the six independent SQL answer checks
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m app evaluate

# Live question: configuration below is required
.venv/bin/python -m app ask "What is paid revenue for 2024 in USD?" --db work/sample.sqlite --provider openai

# Manual SQL and local provenance inspection
.venv/bin/python -m app sql "SELECT invoice_id, amount_usd_cents FROM invoices LIMIT 5" --db work/sample.sqlite
.venv/bin/python -m app inspect I9 --db work/sample.sqlite

# Optional seven-call live regression set, using the original fixture
.venv/bin/python -m app evaluate --live --provider openai
```

`evaluate --live` makes up to seven paid requests and reports expected versus actual answers, SQL, timing, and pass/fail. It stops after a provider error. Its fixture expectations were specified independently before implementation; this small regression set is not a general accuracy benchmark. An evaluation failure returns a nonzero exit status.

### Optional persistent configuration

The guided journey requires no configuration-file editing. For scripted use, copy `.env.example` to `.env` and replace the values locally:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5.6-luna
```

For Claude, use `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, and `ANTHROPIC_MODEL`. Environment values override `.env`; `--provider` overrides the provider choice. The defaults are `gpt-5.6-luna` and `claude-haiku-4-5-20251001`; an omitted model uses its provider default. Explicit model settings take precedence and are never silently replaced on errors. OpenAI overrides must support Responses function calling; Claude overrides must support Messages tool use. Luna uses `reasoning.effort=none` for these bounded agent turns. Model access varies by account. Adapter contracts follow [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Claude tool calls/results](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls). `.env` is ignored by Git. Keys are never printed or included in generated artifacts.

## Business decisions and limitations

- **Conflicting invoices:** quarantine the whole invoice group. Keep alternatives and source rows; report conditional financial bounds. Unknown amounts/signs prevent a complete bound.
- **Dates:** infer only from exclusive column/format evidence or resolved paired chronology, and flag every inference. The default snapshot date is the maximum accepted invoice date, which may be future-dated in synthetic data. It is not a claim about today's business.
- **Revenue:** recorded local amounts × stated FX, rounded per invoice to integer USD cents. Paid, refunded, and net revenue are distinct. Price discrepancies are flagged.
- **MRR and churn:** one provisional latest-invoice snapshot per account. MRR uses plan price × seats × discount, including annual contracts; churned accounts contribute zero MRR. Regional means include those zero accounts. Churn is a snapshot ratio, not period churn.
- **Pending clarification:** account identity/latest-invoice precedence and recorded-amount/FX precedence. The implementation labels both policies provisional.
- **Basic input guard:** rejects obvious instruction overrides, credential requests, destructive commands, and terminal control characters before a paid call. This is a heuristic, not complete prompt-injection prevention. Result cells are untrusted tool evidence; tools are disabled when the model receives results. Direct conversational replies are model-generated and are not independently verified by SQL. New numerical findings are required by the prompt to use SQL; this semantic requirement is not a complete hallucination detector. Terminal output escapes control characters.
- **SQL hardening:** read-only connections; allowed tables, columns and functions; denied writes, raw/contact access, recursive queries and extensions; bounded SQL work and output. This constrains execution, not semantic correctness. A safe query can still answer the wrong question.
- **Data and scale:** the full supplied CSV is not in this public repo. Use your local copy. Imports are bounded to 20 MB and store sensitive raw provenance locally. This is a take-home CLI, not a deployed multiuser service.

## Bonus: input and SQL guardrails

The assessment asks for one production-hardening touch. This project's chosen bonus is **guarded input and query execution**, demonstrated by runnable checks:

```bash
.venv/bin/python -m unittest discover -s tests -p test_query.py -v
.venv/bin/python -m unittest discover -s tests -p test_agent.py -v
```

These verify that writes, raw/contact-table reads, unsafe functions, multiple statements, recursive queries, and excessive SQL work are rejected; obvious malicious questions are blocked before a paid call; result-cell instructions stay in the evidence payload; and a failed summary preserves computed results. No API key is needed. The heuristic input filter is only a first check: SQLite's authorizer enforces the actual data-access boundary.


## Session commands

| Command | What it does |
| --- | --- |
| `/examples` | Run curated SQL examples offline; these do not call a model. |
| `/quality` | Show accepted records, exclusions, warnings and financial uncertainty. |
| `/inspect I9` | Inspect the sample's quarantined invoice and original source rows locally. |
| `/provider` | Switch provider/model and clear conversation history. |
| `/key` | Replace the active provider's saved key and clear history. |
| `/forget` | Remove its saved vault entry and clear active credentials/history. |
| `/summary` | Toggle sending computed rows back to the model; clear history. |
| `/clear` | Forget recent conversation while keeping the current provider. |
| `/evaluate` | Offer the seven-case live SQL evaluation, with a paid-call confirmation. |
| `/quit` | End the session. |

History is at most three completed turns / 12 KB, held in memory. It is sent to the
selected provider for follow-ups. API keys are stored separately in the OS vault.
The first call sends the question, recent conversation, schema, metric rules and
coverage. The second sends executed SQL and result rows, including any names/IDs.
Turning `/summary` off skips that second call and keeps new result rows out of history.
No raw audit records or contact-email field are sent by the application.

## If something goes wrong

- **Python missing or too old:** install Python 3.11+ with `venv` and `sqlite3`, then rerun.
  The bootstrap creates an environment; it does not install Python or system software.
- **No API access:** stay offline with provider option 3. Check model access, API billing,
  and the correct provider key before retrying manually. Chat subscriptions do not fund API calls.
- **Credential store unavailable:** the current session still works; the CLI reports that
  it could not save the key. Linux persistence needs an unlocked Secret Service and `secret-tool`.
- **Question unclear:** give the metric, period or grouping, or use `/clear` to start fresh.
- **Query rejected:** the agent cannot bypass SQLite's read restrictions or resource limits.
  Narrow the request; there are no automatic retries.
- **Final answer unavailable:** successful local results and SQL remain visible. Large
  results may exceed the 32 KB sharing budget; narrow the query or inspect the table locally.
- **Plain terminal output:** `NO_COLOR`, redirected output and unsupported terminals disable
  ANSI styling intentionally. JSON output is always plain.

## Continue development

| Start here | Purpose |
| --- | --- |
| [Pipeline spec](../specs/PIPELINE.md) | Schema, dates, duplicate handling and financial policies |
| [Agent spec](../specs/AGENT.md) | Tool loop, history, privacy and limits |
| [Query spec](../specs/QUERY.md) | Credential and SQL contracts; original design history |
| [Evaluation spec](../specs/EVALUATION.md) | Fixture and independently calculated expectations |
| [AGENTS.md](../AGENTS.md) | Working conventions for humans and coding agents |
| [Handoff](HANDOFF.md) | Code map, verified state and pending business questions |
| [Build log](BUILD_LOG.md) | Actual milestones, failures, checks and time accounting |
| [Selected prompt log](PROMPT_LOG.md) | Labeled reconstruction of relevant AI-assisted development |
