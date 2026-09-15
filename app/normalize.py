"""Normalize each record without deciding which duplicate invoice wins."""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .dates import DateResolver
from .policies import BOOL, CYCLE, FX, PAYMENT, PLAN, PRICES, STATUS, cents

COLUMNS = "invoice_id account_id account_name contact_email region industry plan billing_cycle seats currency amount discount_pct status payment_method signup_date invoice_date churned csat_score support_tickets".split()


@dataclass
class Normalized:
    row: int
    raw: dict
    values: dict
    errors: list[str]
    issues: list[dict]


def decimal_value(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError("invalid decimal") from None
    if not result.is_finite() or abs(result) > 10**12:
        raise ValueError("non-finite or out-of-range decimal")
    return result


def amount(value: str, currency: str) -> Decimal:
    """Currency markers must agree with the column; integer strings are whole units."""
    if currency not in FX:
        raise ValueError("unknown currency")
    value = value.strip()
    suffix = re.search(r"\s*([A-Za-z]{3})$", value)
    if suffix:
        if suffix[1].upper() != currency:
            raise ValueError("currency marker conflicts with currency column")
        value = value[:suffix.start()].strip()
    for symbol, code in (("$", "USD"), ("€", "EUR"), ("£", "GBP")):
        if symbol in value:
            if code != currency or value.count(symbol) != 1 or not value.startswith(symbol):
                raise ValueError("invalid currency symbol")
            value = value.removeprefix(symbol).strip()
    if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?", value):
        raise ValueError("invalid amount format")
    return decimal_value(value.replace(",", ""))


def integer(value: str, minimum: int = 0, maximum: int = 2**31 - 1) -> int:
    parsed = decimal_value(value)
    if parsed != parsed.to_integral_value() or not minimum <= parsed <= maximum:
        raise ValueError("invalid integer/range")
    return int(parsed)


def financial_fields(raw: dict) -> dict:
    """This also supplies all-dates uncertainty bounds for otherwise invalid rows."""
    currency = raw["currency"].strip().upper()
    try:
        status = STATUS[raw["status"].strip().lower()]
    except KeyError:
        raise ValueError("unknown status") from None
    local = amount(raw["amount"], currency)
    if (status == "refunded" and local >= 0) or (status != "refunded" and local < 0):
        raise ValueError("amount sign contradicts status")
    return {"currency": currency, "amount_local": format(local.normalize(), "f"),
            "amount_usd_cents": cents(local * FX[currency]), "status": status}


def normalize(row: int, raw: dict, resolver: DateResolver) -> Normalized:
    values, errors = {"source_row": row}, []
    dates, issues = resolver.resolve(raw)
    values.update(dates)
    if not dates["invoice_date"]:
        errors.append("invoice_date is invalid or unresolved")
    for field in ("invoice_id", "account_id", "account_name"):
        values[field] = raw[field].strip()
        if not values[field]:
            errors.append(f"{field} is required")
    region = raw["region"].strip().upper()
    values["region"] = region
    if region not in {"NA", "EMEA", "APAC", "LATAM"}:
        errors.append("unknown region")
    for field, mapping in (("plan", PLAN), ("billing_cycle", CYCLE), ("churned", BOOL)):
        try:
            values[field] = mapping[raw[field].strip().lower()]
        except KeyError:
            errors.append(f"unknown {field}")
    try:
        values.update(financial_fields(raw))
        values["seats"] = integer(raw["seats"], 1)
        discount = decimal_value(raw["discount_pct"])
        if not 0 <= discount <= 100:
            raise ValueError("discount outside 0..100")
        values["discount_pct"] = format(discount.normalize(), "f")
    except ValueError as exc:
        errors.append(str(exc))
    for field, minimum, maximum in (("csat_score", 1, 5), ("support_tickets", 0, 2**31 - 1)):
        values[field] = None
        if raw[field].strip():
            try:
                values[field] = integer(raw[field], minimum, maximum)
            except ValueError:
                issues.append({"code": "optional_invalid", "field": field})
    email = raw["contact_email"].strip()
    values["contact_email"] = email or None
    if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        values["contact_email"] = None
        issues.append({"code": "email_invalid", "field": "contact_email"})
    values["industry"] = raw["industry"].strip() or None
    payment = raw["payment_method"].strip().lower()
    values["payment_method"] = PAYMENT.get(payment)
    if payment and payment not in PAYMENT:
        issues.append({"code": "optional_invalid", "field": "payment_method"})
    if not errors:
        try:
            expected = cents(PRICES[values["plan"]] * values["seats"]
                             * (1 - Decimal(values["discount_pct"]) / 100)
                             * (10 if values["billing_cycle"] == "annual" else 1))
            delta = abs(values["amount_usd_cents"]) - expected
            if abs(delta) > 2:
                issues.append({"code": "price_fx_mismatch", "field": "amount", "difference_usd_cents": delta})
        except ValueError as exc:
            errors.append(str(exc))
    return Normalized(row, raw, values, errors, issues)
