"""Verdict gates A-D (plan.md section 3). Deterministic, Decimal only.

Claude's equivalence output is untrusted: only `comparable`, `differences`,
and `missing` are read, and it never sets a price, quantity, or verdict.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from urllib.parse import urlparse

from pinktax.models import (
    INSUFFICIENT_EVIDENCE,
    NO_OBSERVED_PREMIUM,
    NOT_COMPARABLE,
    POTENTIAL_PREMIUM,
    PRICE_COMPARISON_ONLY,
    Product,
    Report,
)
from pinktax.normalize import Normalized, normalize

COULDNT_CHECK = "couldn't check equivalence"


def _money(value: Decimal) -> str:
    return f"${value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def _retailer(url: str) -> str:
    host = urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _context_warnings(a: Product, b: Product) -> list[str]:
    warnings = []
    ra, rb = _retailer(a.source_url), _retailer(b.source_url)
    if ra and rb and ra != rb:
        warnings.append(f"Different retailers ({ra} vs {rb}).")
    if a.date_seen and b.date_seen and a.date_seen != b.date_seen:
        warnings.append(f"Prices seen on different dates ({a.date_seen} vs {b.date_seen}).")
    return warnings


def _check_equivalence(equivalence) -> tuple[Optional[str], list, list[str], list[str]]:
    """Gate B. Returns (blocking verdict or None, differences, missing, reasons)."""
    if not isinstance(equivalence, dict):
        return INSUFFICIENT_EVIDENCE, [], [], [COULDNT_CHECK]

    comparable = equivalence.get("comparable")
    differences = equivalence.get("differences", [])
    missing = equivalence.get("missing", [])
    if (
        comparable not in ("yes", "no", "unclear")
        or not isinstance(differences, list)
        or not all(isinstance(d, dict) for d in differences)
        or not isinstance(missing, list)
    ):
        return INSUFFICIENT_EVIDENCE, [], [], [COULDNT_CHECK]

    missing = [str(m) for m in missing]
    if comparable == "unclear":
        return INSUFFICIENT_EVIDENCE, differences, missing, [COULDNT_CHECK]

    material = [d for d in differences if d.get("material") is True]
    if comparable == "no" or material:
        reasons = [f"Material difference: {d.get('attribute', 'unspecified')}." for d in material]
        return NOT_COMPARABLE, differences, missing, reasons or ["Products are not equivalent."]

    return None, differences, missing, []


def compare(a: Product, b: Product, equivalence) -> Report:
    """Apply gates A-D in order. `equivalence` is Claude's parsed JSON dict, or None."""
    # Gate A: enough data, same dimension.
    try:
        na, nb = normalize(a), normalize(b)
    except ValueError as err:
        return Report(verdict=INSUFFICIENT_EVIDENCE, reasons=[str(err)])
    if na.dimension != nb.dimension:
        return Report(
            verdict=NOT_COMPARABLE,
            reasons=[f"Can't compare {a.unit} with {b.unit} (no density)."],
        )

    # Gate B: equivalence.
    blocked, differences, missing, reasons = _check_equivalence(equivalence)

    # Gate C: context warnings never block.
    warnings = _context_warnings(a, b)

    common = dict(
        unit_basis=na.basis,
        unit_price_a=na.unit_price,
        unit_price_b=nb.unit_price,
        differences=differences,
        missing=missing,
        warnings=warnings,
    )
    if blocked:
        return Report(verdict=blocked, reasons=reasons, **common)

    # Gate D: observed difference, women vs men only.
    labels = {a.label: na, b.label: nb}
    if set(labels) != {"women", "men"}:
        return Report(
            verdict=PRICE_COMPARISON_ONLY,
            reasons=[
                "Not a women vs men pair, so no gender verdict.",
                f"{a.name}: {_money(na.unit_price)} per {na.basis}; "
                f"{b.name}: {_money(nb.unit_price)} per {nb.basis}.",
            ],
            **common,
        )

    return _gender_report(labels["women"], labels["men"], common)


def _gender_report(nw: Normalized, nm: Normalized, common: dict) -> Report:
    diff = nw.unit_price - nm.unit_price
    # Gate A guarantees price and quantity > 0, so nm.unit_price > 0.
    premium_pct = diff / nm.unit_price * 100 if nm.unit_price else Decimal("0")
    verdict = POTENTIAL_PREMIUM if diff > 0 else NO_OBSERVED_PREMIUM
    reasons = [
        f"Women's: {_money(nw.unit_price)} per {nw.basis}; "
        f"men's: {_money(nm.unit_price)} per {nm.basis}."
    ]
    if verdict == POTENTIAL_PREMIUM:
        reasons.append("Women's per-unit price is higher for this pair on this date.")
    else:
        reasons.append("Women's per-unit price is not higher for this pair.")
    return Report(
        verdict=verdict,
        premium_pct=premium_pct,
        savings_per_unit=diff,
        savings_at_size=diff * nw.basis_quantity,
        reasons=reasons,
        **common,
    )


def yearly_savings(report: Report, times_per_year) -> Optional[Decimal]:
    """Savings at size x times bought per year; None without a premium."""
    if report.verdict != POTENTIAL_PREMIUM or report.savings_at_size is None:
        return None
    return report.savings_at_size * Decimal(str(times_per_year))
