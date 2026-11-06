"""Shared contract between the engine (A) and the UI (B).

Change only with both people's agreement.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

# Verdicts
POTENTIAL_PREMIUM = "POTENTIAL_PREMIUM"
NO_OBSERVED_PREMIUM = "NO_OBSERVED_PREMIUM"
NOT_COMPARABLE = "NOT_COMPARABLE"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

VERDICTS = (
    POTENTIAL_PREMIUM,
    NO_OBSERVED_PREMIUM,
    NOT_COMPARABLE,
    INSUFFICIENT_EVIDENCE,
)

# Units and marketing labels (plan.md section 0)
UNITS = ("ml", "l", "fl_oz", "g", "kg", "oz", "count")
LABELS = ("women", "men", "neutral", "unknown")


@dataclass
class Product:
    name: str
    price: Decimal
    quantity: Decimal
    unit: str
    pack_count: int = 1
    label: str = "unknown"
    attributes: str = ""
    source_url: str = ""
    date_seen: Optional[date] = None


@dataclass
class Report:
    verdict: str
    premium_pct: Optional[Decimal] = None
    unit_basis: Optional[str] = None
    savings_per_unit: Optional[Decimal] = None
    savings_at_size: Optional[Decimal] = None
    differences: list = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


# compare(a: Product, b: Product, equivalence: dict | None) -> Report
# lives in pinktax/verdict.py.
