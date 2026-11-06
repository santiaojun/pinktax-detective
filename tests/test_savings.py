from datetime import date
from decimal import Decimal

import pytest

from pinktax.models import (
    INSUFFICIENT_EVIDENCE,
    NO_OBSERVED_PREMIUM,
    NOT_COMPARABLE,
    PRICE_COMPARISON_ONLY,
    Product,
    Report,
)
from pinktax.savings import (
    add_swap,
    has_swap,
    pair_key,
    remove_swap,
    total,
    yearly_total,
)
from pinktax.verdict import compare

EQUIVALENT = {"comparable": "yes", "differences": [], "missing": [], "note": ""}
TODAY = date(2026, 11, 6)


def women(**kw):
    base = dict(name="W", price=Decimal("6"), quantity=Decimal("200"), unit="ml", label="women")
    return Product(**{**base, **kw})


def men(**kw):
    base = dict(name="M", price=Decimal("5"), quantity=Decimal("200"), unit="ml", label="men")
    return Product(**{**base, **kw})


def premium(**kw):
    return compare(women(**kw), men(), EQUIVALENT)  # $1.00 at size


# pair_key

def test_pair_key_stable_and_order_independent():
    assert pair_key(women(), men()) == pair_key(men(), women())
    assert pair_key(women(), men()) == pair_key(women(name="  w "), men())


def test_pair_key_same_size_in_other_units():
    assert pair_key(women(quantity=Decimal("0.2"), unit="l"), men()) == pair_key(women(), men())


def test_pair_key_ignores_url_and_date():
    k = pair_key(women(), men())
    assert pair_key(women(source_url="https://x.com", date_seen=TODAY), men()) == k


def test_pair_key_changes_with_price_or_attributes():
    k = pair_key(women(), men())
    assert pair_key(women(price=Decimal("7")), men()) != k
    assert pair_key(women(attributes="5 blades"), men()) != k


# add_swap

def test_add_swap_records_fields():
    key = pair_key(women(), men())
    records = add_swap([], premium(), key, "Body wash", times_per_year=12, today=TODAY)
    [swap] = records
    assert swap.pair_key == key and swap.label == "Body wash"
    assert swap.savings_at_size == Decimal("1.0")
    assert swap.yearly_savings == Decimal("12.0")
    assert swap.date_saved == TODAY
    assert has_swap(records, key)


def test_add_swap_returns_new_list():
    original = []
    records = add_swap(original, premium(), "k", "Body wash")
    assert original == [] and len(records) == 1


def test_duplicates_dont_double_count():
    records = add_swap([], premium(), "k", "Body wash", today=TODAY)
    again = add_swap(records, premium(), "k", "Body wash again", times_per_year=52)
    assert again == records
    assert total(again) == Decimal("1.0")
    assert yearly_total(again) == 0


@pytest.mark.parametrize("verdict", [
    NO_OBSERVED_PREMIUM, NOT_COMPARABLE, INSUFFICIENT_EVIDENCE, PRICE_COMPARISON_ONLY,
])
def test_non_premium_rejected(verdict):
    with pytest.raises(ValueError, match="POTENTIAL_PREMIUM"):
        add_swap([], Report(verdict=verdict, savings_at_size=Decimal("1")), "k", "x")


def test_real_non_premium_report_rejected():
    report = compare(women(price=Decimal("5")), men(), EQUIVALENT)
    with pytest.raises(ValueError):
        add_swap([], report, "k", "x")


def test_negative_times_rejected():
    with pytest.raises(ValueError, match="times_per_year"):
        add_swap([], premium(), "k", "x", times_per_year=-1)


# remove / totals

def test_remove_updates_total():
    records = add_swap([], premium(), "a", "Body wash", times_per_year=10)
    records = add_swap(records, premium(price=Decimal("8")), "b", "Razor")
    assert total(records) == Decimal("4.0")  # $1.00 + $3.00
    assert yearly_total(records) == Decimal("10.0")
    records = remove_swap(records, "a")
    assert total(records) == Decimal("3.0")
    assert yearly_total(records) == 0
    assert remove_swap(records, "missing") == records


def test_empty_list_totals_zero():
    assert total([]) == Decimal("0")
    assert yearly_total([]) == Decimal("0")
    assert isinstance(total([]), Decimal)
