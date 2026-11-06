"""Session savings tracker. Pure functions over an immutable list of Swaps.

Totals are always recomputed from the records; nothing stores a running total.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from pinktax.models import POTENTIAL_PREMIUM, Product, Report
from pinktax.normalize import normalize, parse_positive
from pinktax.verdict import yearly_savings as _yearly


@dataclass(frozen=True)
class Swap:
    pair_key: str
    label: str
    savings_at_size: Decimal
    yearly_savings: Optional[Decimal]
    date_saved: date


def _fingerprint(product: Product) -> list:
    n = normalize(product)
    return [
        " ".join(product.name.split()).casefold(),
        product.label,
        str(parse_positive(product.price, "price").normalize()),
        n.dimension,
        str(n.base_quantity.normalize()),
        " ".join((product.attributes or "").split()).casefold(),
    ]


def pair_key(a: Product, b: Product) -> str:
    """Stable key for a pair, the same whichever product is A.

    Built from name, label, price, normalized size, and attributes. Source URL
    and date seen are left out, so re-entering the same pair matches.
    """
    fingerprints = sorted([_fingerprint(a), _fingerprint(b)])
    return hashlib.sha256(json.dumps(fingerprints).encode("utf-8")).hexdigest()[:16]


def has_swap(records: list[Swap], key: str) -> bool:
    return any(r.pair_key == key for r in records)


def add_swap(
    records: list[Swap],
    report: Report,
    pair_key: str,
    label: str,
    times_per_year=None,
    *,
    today: Optional[date] = None,
) -> list[Swap]:
    """Return a new list with this swap added. Only POTENTIAL_PREMIUM reports
    qualify; a pair_key already saved returns the list unchanged."""
    if report.verdict != POTENTIAL_PREMIUM:
        raise ValueError(f"only {POTENTIAL_PREMIUM} reports can be saved, got {report.verdict}")
    if report.savings_at_size is None or report.savings_at_size <= 0:
        raise ValueError("report has no positive savings to save")
    if has_swap(records, pair_key):
        return list(records)

    yearly = None
    if times_per_year:
        times = Decimal(str(times_per_year))
        if times < 0:
            raise ValueError("times_per_year must be 0 or more")
        yearly = _yearly(report, times)

    swap = Swap(
        pair_key=pair_key,
        label=label,
        savings_at_size=report.savings_at_size,
        yearly_savings=yearly,
        date_saved=today or date.today(),
    )
    return [*records, swap]


def remove_swap(records: list[Swap], pair_key: str) -> list[Swap]:
    return [r for r in records if r.pair_key != pair_key]


def total(records: list[Swap]) -> Decimal:
    return sum((r.savings_at_size for r in records), Decimal("0"))


def yearly_total(records: list[Swap]) -> Decimal:
    return sum((r.yearly_savings for r in records if r.yearly_savings is not None), Decimal("0"))
