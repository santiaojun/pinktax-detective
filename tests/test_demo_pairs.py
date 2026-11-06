from decimal import Decimal

import pytest

from demo_pairs import DEMO_PAIRS, load_equivalence_fixture
from pinktax.models import (
    INSUFFICIENT_EVIDENCE,
    NOT_COMPARABLE,
    POTENTIAL_PREMIUM,
    Product,
)
from pinktax.verdict import compare

# What each pair was designed to show; the app never reads this.
INTENDED = {
    "body_wash": POTENTIAL_PREMIUM,
    "razor": NOT_COMPARABLE,
    "deodorant": INSUFFICIENT_EVIDENCE,
    "everyday_body_wash": POTENTIAL_PREMIUM,
}


def to_product(fields):
    return Product(**{**fields, "price": Decimal(fields["price"]),
                      "quantity": Decimal(fields["quantity"])})


@pytest.mark.parametrize("pair_id", sorted(DEMO_PAIRS))
def test_demo_pair_produces_intended_verdict(pair_id):
    pair = DEMO_PAIRS[pair_id]
    equivalence = load_equivalence_fixture(pair_id)
    assert equivalence is not None
    r = compare(to_product(pair["a"]), to_product(pair["b"]), equivalence)
    assert r.verdict == INTENDED[pair_id]


def test_missing_fixture_returns_none():
    assert load_equivalence_fixture("no_such_pair") is None


def test_main_storyline_fully_offline(monkeypatch):
    """Pink and blue photos -> demo extraction -> demo equivalence -> premium,
    with any attempt to build an API client failing the test."""
    import anthropic

    from demo_pairs import DEMO_IMAGES
    from pinktax.extract import from_image

    def no_api(*args, **kwargs):
        raise AssertionError("Demo mode must not create an API client")

    monkeypatch.setattr(anthropic, "Anthropic", no_api)
    pair = DEMO_PAIRS["everyday_body_wash"]
    products = {}
    for side, image in (("a", "pink_label"), ("b", "blue_label")):
        # No demo_name: the image itself selects its fixture.
        fields = from_image(DEMO_IMAGES[image].read_bytes(), "image/png", demo=True)
        assert "price" not in fields  # the photo never sets the price
        assert fields["attributes"] == pair[side]["attributes"]
        products[side] = Product(**{**fields, "label": pair[side]["label"]},
                                 price=Decimal(pair[side]["price"]))

    r = compare(products["a"], products["b"], load_equivalence_fixture("everyday_body_wash"))
    assert r.verdict == POTENTIAL_PREMIUM
    assert round(r.premium_pct, 2) == Decimal("30.03")
    assert round(r.unit_price_a, 2) == Decimal("2.75") and round(r.unit_price_b, 2) == Decimal("2.11")
    assert round(r.savings_at_size, 2) == Decimal("3.00")


def test_demo_image_lookup():
    from demo_pairs import DEMO_IMAGES, demo_image_name

    assert demo_image_name(DEMO_IMAGES["blue_label"].read_bytes()) == "blue_label"
    assert demo_image_name(b"not a demo image") is None
