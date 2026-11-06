from decimal import Decimal

import pytest

from pinktax.models import Product
from pinktax.normalize import normalize, parse_positive


def product(price="5", quantity="100", unit="ml", pack_count=1):
    return Product(name="P", price=price, quantity=quantity, unit=unit, pack_count=pack_count)


@pytest.mark.parametrize("value", [None, "", "   ", "-1", "0", "abc", "NaN", "Infinity", -3, 0])
@pytest.mark.parametrize("field", ["price", "quantity"])
def test_bad_price_or_quantity_raises_naming_field(field, value):
    p = product(**{field: value})
    with pytest.raises(ValueError, match=field):
        normalize(p)


def test_parse_positive_accepts_str_int_decimal():
    assert parse_positive("1.50", "price") == Decimal("1.50")
    assert parse_positive(2, "price") == Decimal("2")
    assert parse_positive(Decimal("3.25"), "price") == Decimal("3.25")


def test_bad_unit_and_pack_count_raise():
    with pytest.raises(ValueError, match="unit"):
        normalize(product(unit="cup"))
    with pytest.raises(ValueError, match="pack_count"):
        normalize(product(pack_count=0))


def test_litre_and_millilitre_share_basis():
    half = normalize(product(price="5", quantity="500", unit="ml"))
    litre = normalize(product(price="10", quantity="1", unit="l"))
    assert half.basis == litre.basis == "100 ml"
    assert half.unit_price == litre.unit_price == Decimal("1")


def test_fl_oz_converts_to_ml():
    n = normalize(product(price="8.99", quantity="16", unit="fl_oz"))
    assert n.base_quantity == Decimal("473.1760")
    assert n.basis == "100 ml"


def test_mass_units():
    assert normalize(product(quantity="1", unit="kg")).base_quantity == Decimal("1000")
    assert normalize(product(quantity="2", unit="oz")).base_quantity == Decimal("56.6990")
    assert normalize(product(unit="g")).basis == "100 g"


def test_pack_count_gives_per_item_price():
    two_pack = normalize(product(price="10", quantity="5", unit="count", pack_count=2))
    assert two_pack.basis == "item"
    assert two_pack.base_quantity == Decimal("10")
    assert two_pack.unit_price == Decimal("1")
