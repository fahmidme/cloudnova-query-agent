"""Infer dates only from explicit format evidence or one resolved paired date."""

import re
from collections import defaultdict
from datetime import date, datetime

YEAR_LAST = re.compile(r"^(\d{1,2})([-/])(\d{1,2})\2(\d{4})$")


def candidates(value: str) -> tuple[str | None, dict[str, date]]:
    value = value.strip()
    match = YEAR_LAST.fullmatch(value)
    if match:
        first, sep, second, year = match.groups()
        choices = {}
        for order, month, day in (("DMY", second, first), ("MDY", first, second)):
            try:
                choices[order] = date(int(year), int(month), int(day))
            except ValueError:
                pass
        return sep, choices
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%b %d %Y"):
        try:
            return None, {"explicit": datetime.strptime(value, fmt).date()}
        except ValueError:
            pass
    return None, {}


class DateResolver:
    def __init__(self, records: list[dict]):
        # A majority is insufficient: mixed-source formats may contradict each other.
        self.evidence = defaultdict(set)
        for raw in records:
            for field in ("signup_date", "invoice_date"):
                sep, choices = candidates(raw[field])
                if sep and len(choices) == 1:
                    self.evidence[field, sep].update(choices)

    def resolve(self, raw: dict) -> tuple[dict, list[dict]]:
        resolved, pending, issues = {}, {}, []
        for field in ("signup_date", "invoice_date"):
            sep, choices = candidates(raw[field])
            unique = set(choices.values())
            resolved[field] = None
            if len(unique) == 1:
                resolved[field] = next(iter(unique))
            elif len(unique) > 1:
                evidence = self.evidence[field, sep]
                if len(evidence) == 1 and next(iter(evidence)) in choices:
                    order = next(iter(evidence))
                    resolved[field] = choices[order]
                    issues.append(self.inference(field, raw[field], choices, f"column/separator evidence: {order}"))
                else:
                    pending[field] = choices
            else:
                issues.append({"code": "date_invalid", "field": field, "raw": raw[field]})
        for field, choices in pending.items():
            other = resolved["signup_date" if field == "invoice_date" else "invoice_date"]
            valid = {d for d in choices.values() if other is not None
                     and (d >= other if field == "invoice_date" else d <= other)}
            if len(valid) == 1:
                resolved[field] = next(iter(valid))
                issues.append(self.inference(field, raw[field], choices, "paired signup/invoice chronology"))
            else:
                issues.append({"code": "date_unresolved", "field": field, "raw": raw[field],
                               "candidates": sorted(d.isoformat() for d in set(choices.values()))})
        if all(resolved.values()) and resolved["signup_date"] > resolved["invoice_date"]:
            issues.append({"code": "date_chronology_conflict", "field": "invoice_date"})
        return {k: v.isoformat() if v else None for k, v in resolved.items()}, issues

    @staticmethod
    def inference(field, raw, choices, evidence):
        return {"code": "date_inferred", "field": field, "raw": raw,
                "candidates": sorted(d.isoformat() for d in set(choices.values())), "evidence": evidence}
