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
