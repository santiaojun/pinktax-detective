from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from pinktax.models import (
    INSUFFICIENT_EVIDENCE,
    NOT_COMPARABLE,
    POTENTIAL_PREMIUM,
)

INTENDED = {
    "body_wash": POTENTIAL_PREMIUM,
    "razor": NOT_COMPARABLE,
    "deodorant": INSUFFICIENT_EVIDENCE,
}

APP = str(Path(__file__).parent.parent / "app.py")


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()


@pytest.mark.parametrize("pair_id", sorted(INTENDED))
def test_demo_mode_pair_shows_intended_verdict(pair_id):
    at = AppTest.from_file(APP).run()
    at.button(key=f"demo_{pair_id}").click().run()
    click(at, "Compare")
    assert not at.exception
    assert at.session_state.result["report"].verdict == INTENDED[pair_id]
    caveat = "One pair is not evidence of a market-wide pattern."
    assert any(c.value == caveat for c in at.caption)


def test_savings_line_only_on_premium():
    at = AppTest.from_file(APP).run()
    at.button(key="demo_body_wash").click().run()
    at.number_input(key="times_per_year").set_value(6).run()
    click(at, "Compare")
    texts = [s.value for s in at.success]
    assert any("men's equivalent costs" in t for t in texts)
    assert any("a year" in t for t in texts)

    at.button(key="demo_razor").click().run()
    click(at, "Compare")
    assert not any("men's equivalent costs" in s.value for s in at.success)


def test_field_errors_block_compare():
    at = AppTest.from_file(APP).run()
    at.text_input(key="a_price").set_value("abc").run()
    click(at, "Compare")
    assert at.session_state.result is None
    assert any("price must be a number" in e.value for e in at.error)
    assert any("quantity is required" in e.value for e in at.error)


def test_demo_mode_off_is_insufficient_evidence():
    at = AppTest.from_file(APP).run()
    at.toggle(key="demo_mode").set_value(False).run()
    at.button(key="demo_body_wash").click().run()
    click(at, "Compare")
    assert at.session_state.result["report"].verdict == INSUFFICIENT_EVIDENCE
