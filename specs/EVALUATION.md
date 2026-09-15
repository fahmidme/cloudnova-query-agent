# Independent evaluation plan v1

Define these expectations before writing transformation/query code. Build a tiny original fixture with hand-computable values; do not use production outputs as its answer key.

## Fixture ledger and expected interpretation

All invoice dates below are in 2024; include consistent names per account unless explicitly testing identity conflict. USD unless noted.

| Invoice | Account | Plan, seats, discount | Date | Status / amount | Churned |
| --- | --- | --- | --- | --- | --- |
| I1 | A1 (NA) | Starter, 10, 0% | 2024-01-15 | Complete / $490 | No |
| I1 equivalent copy | A1 | same | 2024/01/15 | paid / 490.00 | FALSE |
| I2 | A1 | Starter, 10, 0% | 2024-02-15 | paid / 490 | No |
| I3 | A1 | Starter, 10, 0% | 2024-03-15 | REFUND / -49 | No |
| I4 | A2 (EMEA) | Enterprise, 1, 0% | 2024-01-16 | paid / 299 | Yes |
| I5 | A3 (EMEA) | Pro, 2, 0% | 2024-01-17 | pending / 198 | No |
| I6 | A4 (NA) | Starter, 1, 0% | 2024-01-18 | failed / 49 | No |
| I7 | A5 (APAC) | Starter, 1, 0% | 2024-01-19 | paid / 100 EUR | No |
| I8 | A6 (LATAM) | Starter, 3, 10%, annual | 2024-01-20 | paid / 1,323 | No |
| I9, conflicting pair | A7 (NA) | Starter, 10, 0% | 2024-01-21 | paid / 490 AND void / 490 | No |

Fixture has 11 records, 9 invoice IDs; 8 accepted invoices, 1 equivalent copy collapsed, 1 invoice group quarantined (2 rows). A7 has no account snapshot because no invoice survives. Give A1 snapshot CSAT 2, A6 CSAT 5, and A5 missing CSAT.

## Expected stakeholder answers

1. Paid revenue in 2024: 490 + 490 + 299 + 108 + 1323 = **$2,710**.
2. Refunds given back: **$49**. Net revenue: **$2,661**. These must be distinct metrics.
3. Mean MRR per modeled account including churned zero-MRR accounts: NA=(490+49)/2=**$269.50**; EMEA=(0+198)/2=**$99**; APAC=**$49**; LATAM=**$132.30**. NA ranks first.
4. Snapshot churn: Enterprise **1/1 = 100%**; Starter **0/4 = 0%**. This is not churn during a reporting period.
5. Top 5 net-revenue accounts: A6 **1323**, A1 **931** (low CSAT), A2 **299**, A5 **108** (CSAT unknown), A3 **0**. Order ties by account_id; A4 is also zero and sorts after A3.
6. Pending/failed: **2 invoices**, **$247 exposure**.
7. I9 excluded net-revenue contribution: **$0..$490**. Accepted plus interpretable alternatives: **$2,661..$3,151**, not a confirmed total or lost-revenue estimate.

## Additional behavior checks

- Cohort evidence `18-07-2024` resolves `02-04-2024` to April 2 with an inference flag. A cohort with evidence in both directions must not choose arbitrarily. Paired chronology can disambiguate; otherwise quarantine unresolved invoice dates.
- Equivalent duplicates compare normalized values, but paid versus void variants never both enter revenue. Invalid variants prevent an invoice group from appearing clean.
- An annual $1,323 invoice at Starter x 3 seats x 90% produces MRR $132.30, not $110.25.
- Accounts use exactly one as-of snapshot; future invoices do not affect earlier snapshots. Conflicting identity/state is flagged, not erased.
- Invalid amount/sign/currency: quarantine with unknown financial bounds where necessary. NULL email/CSAT do not become invented values or zero.
- Source row references include all equivalent copies. A failed re-import leaves the previous database unchanged.
- SELECT works; writes, schema/raw/email access, ATTACH, PRAGMA, unsafe functions, multiple statements, recursive CTEs, and excessive rows/work are rejected.
- Mock API success, unsupported result, refusal, incomplete output, invalid JSON/schema, transport failure, and missing configuration. Clearly distinguish these contract tests from live-provider evaluation.

## Expected failure / unsupported case

Question: "What was our Enterprise churn rate during February 2024?"

Expected behavior: state that period churn cannot be established from invoice snapshots without churn event dates and opening cohort membership. Do not substitute current/snapshot churn. Show this explicitly as an expected unsupported case in the offline demo; test a mocked unsupported plan. Live model recognition of this limit must be verified separately if a key is supplied.

## Optional live harness — specified before implementation

`python -m app evaluate --live [--provider openai|anthropic]` makes seven sequential provider calls over the original fixture: the six stakeholder query cases above plus period churn. Assert the independently specified answer rows, requested column contract, deterministic ordering, and explicit unsupported status. Record SQL, result, timing, and pass/fail per case. A provider error must remain a failure; stop subsequent calls after a provider failure to avoid repeated billing/authentication failures. This is a small regression set, not an accuracy benchmark. Without `--live`, evaluate curated SQL offline and mark natural-language unsupported recognition as untested.
