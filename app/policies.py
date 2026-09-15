"""Business rules from the brief; provisional decisions are isolated here."""

from decimal import Decimal, ROUND_HALF_UP

POLICY_VERSION = "cloudnova-v1"
PRICES = {"starter": Decimal(49), "pro": Decimal(99), "enterprise": Decimal(299)}
# Provisional precedence: recorded amount x the brief's stated FX direction.
FX = {"USD": Decimal(1), "EUR": Decimal("1.08"), "GBP": Decimal("1.27")}
PLAN = {alias: canonical for canonical, aliases in {
    "starter": ("starter", "start", "tier 1"),
    "pro": ("pro", "professional", "tier 2"),
    "enterprise": ("enterprise", "ent", "tier 3"),
}.items() for alias in aliases}
STATUS = {alias: canonical for canonical, aliases in {
    "paid": ("paid", "complete", "completed", "success"),
    "pending": ("pending", "in_review", "awaiting"),
    "failed": ("failed", "declined", "error"),
    "refunded": ("refunded", "refund", "charged_back"),
    "void": ("void", "cancelled", "canceled"),
}.items() for alias in aliases}
CYCLE = {"monthly": "monthly", "annual": "annual", "annually": "annual", "yearly": "annual"}
PAYMENT = {"credit card": "credit_card", "credit_card": "credit_card", "ach": "ach",
           "wire": "wire", "wire transfer": "wire", "invoice": "invoice"}
BOOL = {"true": 1, "yes": 1, "1": 1, "y": 1, "false": 0, "no": 0, "0": 0, "n": 0}
PROVISIONAL = [
    "Recorded local amounts and stated FX rates take precedence over price reconciliation.",
    "account_id is authoritative; latest accepted invoice supplies the as-of snapshot.",
    "Active means not churned in the snapshot; contract activity is not independently verified.",
    "Regional mean MRR includes churned accounts with zero MRR; churn is a snapshot ratio.",
]


def cents(value: Decimal) -> int:
    """Round once per invoice/metric, using decimal arithmetic before SQL storage."""
    result = int((value * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if abs(result) > 10**15:
        raise ValueError("amount exceeds supported integer-cent range")
    return result


def subscription_mrr(invoice: dict) -> int:
    return cents(PRICES[invoice["plan"]] * invoice["seats"]
                 * (1 - Decimal(invoice["discount_pct"]) / 100))


def revenue_contribution(invoice: dict) -> int:
    return invoice["amount_usd_cents"] if invoice["status"] in ("paid", "refunded") else 0
