"""Unit normalization and per-unit prices. Deterministic, Decimal only."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from pinktax.models import Product

VOLUME = "volume"
MASS = "mass"
COUNT = "count"

# unit -> (dimension, factor to the dimension's base unit: ml, g, or item)
UNIT_TABLE = {
    "ml": (VOLUME, Decimal("1")),
    "l": (VOLUME, Decimal("1000")),
    "fl_oz": (VOLUME, Decimal("29.5735")),
    "g": (MASS, Decimal("1")),
    "kg": (MASS, Decimal("1000")),
    "oz": (MASS, Decimal("28.3495")),
    "count": (COUNT, Decimal("1")),
}

# dimension -> (basis label, base units per basis)
BASIS = {
    VOLUME: ("100 ml", Decimal("100")),
    MASS: ("100 g", Decimal("100")),
    COUNT: ("item", Decimal("1")),
}


@dataclass(frozen=True)
class Normalized:
    dimension: str
    basis: str              # "100 ml", "100 g", or "item"
    base_quantity: Decimal  # total ml, g, or items (pack_count applied)
    basis_quantity: Decimal  # base_quantity expressed in basis units
    unit_price: Decimal     # price per basis unit


def parse_positive(value, field: str) -> Decimal:
    """Parse value as a finite Decimal > 0, or raise ValueError naming the field."""
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} is required")
    if isinstance(value, float):
        value = str(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError(f"{field} is required")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field} must be a number, got {value!r}") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be a finite number")
    if number <= 0:
        raise ValueError(f"{field} must be greater than 0")
    return number


def parse_pack_count(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"pack_count must be a whole number, got {value!r}")
    if value < 1:
        raise ValueError("pack_count must be at least 1")
    return value


def dimension_of(unit: str) -> str:
    if unit not in UNIT_TABLE:
        raise ValueError(f"unit must be one of {', '.join(UNIT_TABLE)}, got {unit!r}")
    return UNIT_TABLE[unit][0]


def normalize(product: Product) -> Normalized:
    """Validate a product and compute its per-unit price. Raises ValueError."""
    price = parse_positive(product.price, "price")
    quantity = parse_positive(product.quantity, "quantity")
    pack_count = parse_pack_count(product.pack_count)
    dimension = dimension_of(product.unit)
    factor = UNIT_TABLE[product.unit][1]

    base_quantity = quantity * factor * pack_count
    basis, per_basis = BASIS[dimension]
    basis_quantity = base_quantity / per_basis
    return Normalized(
        dimension=dimension,
        basis=basis,
        base_quantity=base_quantity,
        basis_quantity=basis_quantity,
        unit_price=price / basis_quantity,
    )
