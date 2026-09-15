# Pipeline contract v1

Written before implementation on 2026-09-15. Source: the supplied CloudNova business context and Track B requirements, read before drafting. This is our interpretation, not a claim that the customer approved every policy.

## Scope and runtime

Python 3.11+ standard library, SQLite, a CLI, and an optional OpenAI Responses API adapter. No runtime packages, Docker, database server, or frontend. Create a local virtual environment with a Python bootstrap script; do not install or modify system software. Supply an original small fixture for a fully offline demo. The full assessment CSV remains local and is selected with an explicit path.

Use separate modules for configuration/policies, date interpretation, normalization, pipeline orchestration, SQLite storage, read-only queries, and the provider. Keep functions small and document business choices.

## S1: Source preservation and validation

- Accept a UTF-8 CSV with the 19 documented columns. Reject duplicate/missing headers and malformed record widths; do not partially replace a previous database on a failed import.
- Keep the input unchanged. Record its SHA-256, import row count, policy version, and reporting date in the database/report. Use CSV record numbers including the header (first data record = 2), not physical text lines if quoted multiline fields exist.
- Preserve every original field in a local `raw_records` table. Link accepted invoices to all original duplicate rows through `invoice_sources`. Keep source row numbers in each quality issue and quarantine entry.
- Do not expose contact emails to the model. Raw records and provenance tables are available to local inspection, not model-generated SQL.

## S2: Canonical schema

`invoices` has exactly one accepted row per invoice_id:

| Field | Type / rule |
| --- | --- |
| invoice_id, account_id, account_name | Required nonblank text; trim whitespace. |
| region | NA, EMEA, APAC, LATAM; preserve NA as a category, not a missing value. |
| plan | starter, pro, enterprise. |
| billing_cycle | monthly or annual. |
| seats | Positive integer. |
| currency | USD, EUR, GBP. |
| amount_local | Decimal string in major currency units. |
| amount_usd_cents | Integer cents, per-invoice HALF_UP rounding after FX conversion. |
| discount_pct | Decimal string in [0,100]. |
| status | paid, pending, failed, refunded, void. |
| invoice_date | ISO date; unresolved/invalid required dates quarantine the invoice. |
| signup_date | ISO date or NULL with a quality warning. |
| churned | Boolean integer 0/1; invalid values quarantine. |
| csat_score | Integer 1..5 or NULL; invalid optional values become NULL with warning. |
| industry, contact_email, payment_method | Nullable normalized text. Invalid email becomes NULL with warning; do not guess a corrected address. |
| support_tickets | Nonnegative integer or NULL with warning. |
| source_row | Lowest original record number among equivalent duplicates. |

Normalize case/outer whitespace. Plan aliases: start/tier 1 -> starter; professional/tier 2 -> pro; ent/tier 3 -> enterprise. Billing aliases yearly/annually -> annual. Status aliases: complete/completed/success -> paid; in_review/awaiting -> pending; declined/error -> failed; refund/charged_back -> refunded; cancelled/canceled -> void. Booleans: true/yes/1/y and false/no/0/n. Payment methods: credit card/credit_card, ach, wire transfer/wire, invoice. Unknown required categories quarantine; unknown optional payment methods warn and become NULL.

Parse amounts with Decimal, accepting valid thousands separators and matching currency symbols/codes. Reject non-finite numbers and contradictory currency markers. Integer strings mean whole currency units; never infer missing cents. Preserve negative refunds. Refunded rows must be negative; paid/pending/failed/void rows must be nonnegative. Invalid signs quarantine rather than being silently repaired.

## S3: Date interpretation (owner-approved evidence-first approach)

- Parse year-first ISO/slash and English abbreviated-month dates exactly.
- For numeric year-last slash/dash strings, enumerate valid DMY and MDY interpretations.
- Learn ordering evidence separately for each date column and separator from unambiguous values in this input. Infer an ambiguous value only if evidence supports exactly one ordering. This is a documented heuristic, not proof of source locale.
- If that cannot resolve it, compare with a resolved paired signup/invoice date: signup must be on or before invoice. Infer only if this leaves exactly one candidate. Do not use circular inferences when both dates are unresolved.
- Every inferred value gets a warning containing the raw value, candidates, and evidence. If unresolved, invoice_date quarantines; signup_date becomes NULL with warning. If two resolved dates violate chronology, flag the inconsistency without rewriting the dates.
- Store the default reporting date as the maximum accepted invoice date in this dataset, not the wall-clock date. Support an explicit `--as-of YYYY-MM-DD`. Label snapshot outputs with that date. Future-dated synthetic source rows do not establish real current business state.

## S4: Duplicates and financial uncertainty (owner-approved)

Group by invoice_id after normalization, comparing all canonical business fields except source_row. Identical/equivalent duplicates collapse and retain all source references. If canonical variants disagree, or any variant is invalid, quarantine the entire invoice group. Do not select a winner based on file order or prefer paid status.

For each excluded invoice group, calculate the minimum/maximum alternative net-revenue contribution from its distinct interpretable variants: paid/refunded -> signed USD cents; other statuses -> zero. Sum these per-group bounds without counting copies multiple times. If any variant has an uninterpretable amount/currency/status/sign, mark that group's bounds unknown. Report the count of unknown groups separately.

These are all-dates, one-record-per-invoice alternative bounds, not lost revenue, forecast revenue, or independently verified truth. Date ambiguity does not prevent an all-dates amount bound, but no year/month attribution is claimed for unresolved dates. Accepted revenue is a subtotal; quarantined records can make totals incomplete.

## S5: Metrics (brief-defined unless marked provisional)

- Price per seat/month in USD: starter 49, pro 99, enterprise 299.
- Convert local amounts to USD by multiplying: USD 1, EUR 1.08, GBP 1.27. **Provisional source precedence:** keep the recorded amount and stated FX direction even when list pricing does not reconcile. Warn if abs(converted invoice) differs by more than $0.02 from plan x seats x discount x cycle months (annual = 10, monthly = 1). Do not apply discount to recorded amounts a second time or reconstruct amounts from price.
- Paid revenue = sum paid invoice USD cents. Refunds given back = positive magnitude of refunded invoice USD cents. Net revenue = paid revenue minus refunds. Pending, failed, and void do not contribute to either revenue metric.
- Pending/failed exposure = count and positive USD amount of accepted invoices with either status, not recognized revenue.
- **Provisional accounts:** account_id is authoritative. Pick the latest accepted invoice on/before as-of; ties use lexicographically smallest invoice_id and raise a warning. Build one `accounts` row per account with latest name, region, plan, seats, discount, CSAT and churn state. Count churned accounts in the denominator, not invoices. Flag differences across historical name/region/plan/seats/discount/churn and accounts with quarantined invoice history. These may be legitimate changes or identity errors; do not pretend to distinguish them.
- Account MRR = price x seats x (1-discount/100) if not churned, else zero. Annual billing does not change this formula. The active flag is a churn-based snapshot assumption, not proof of an active contract. Regional average MRR includes all modeled accounts including churned accounts with zero MRR; label the denominator.
- Churn comparison = churned accounts / all modeled accounts in each snapshot plan, not a period-based churn rate or a causal claim.
- Top accounts = accepted net invoice revenue through as-of, grouped by account_id, joined to snapshot CSAT; NULL CSAT is unknown, not healthy. Report CSAT <= 2 as low.

## S6: Storage and import behavior

Store `raw_records`, `invoices`, `invoice_sources`, `accounts`, `quarantine`, `quality_issues`, and `metadata`. Build into a temporary sibling database and atomically replace the designated output only on success. Use SQL constraints and transactions. Write report JSON with summary counts, source hash, as-of date, provisional policies, uncertainty bounds, and warning counts. The local database retains full issue details for audit.

## Questions awaiting external clarification

1. Is account_id authoritative despite inconsistent company identity, and is a latest-invoice snapshot acceptable?
2. Should recorded amounts and the stated FX direction remain authoritative when pricing does not reconcile?

Keep these decisions isolated in policy/modeling code. Any revised rule gets a specification amendment before implementation changes. No answer from the customer is assumed.
