import io
from pathlib import Path

import pytest
from PIL import Image
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
    "everyday_body_wash": POTENTIAL_PREMIUM,
}

APP = str(Path(__file__).parent.parent / "app.py")


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()


@pytest.mark.parametrize("pair_id", sorted(INTENDED))
def test_demo_mode_pair_shows_intended_verdict(pair_id):
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.button(key=f"demo_{pair_id}").click().run()
    click(at, "Compare")
    assert not at.exception
    assert at.session_state.result["report"].verdict == INTENDED[pair_id]
    caveat = "One pair is not evidence of a market-wide pattern."
    assert any(c.value == caveat for c in at.caption)


def test_savings_line_only_on_premium():
    at = AppTest.from_file(APP, default_timeout=30).run()
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
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.text_input(key="a_price").set_value("abc").run()
    click(at, "Compare")
    assert at.session_state.result is None
    assert any("price must be a number" in e.value for e in at.error)
    assert any("quantity is required" in e.value for e in at.error)


def test_demo_mode_off_is_insufficient_evidence():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.toggle(key="demo_mode").set_value(False).run()
    at.button(key="demo_body_wash").click().run()
    click(at, "Compare")
    assert at.session_state.result["report"].verdict == INSUFFICIENT_EVIDENCE


def test_demo_mode_off_calls_check_once_and_caches(monkeypatch):
    from pinktax import equivalence

    calls = []

    def fake_check(a, b, *, client=None, model=None):
        calls.append((a.name, b.name))
        return {"comparable": "yes", "differences": [], "missing": [], "note": ""}

    monkeypatch.setattr(equivalence, "check", fake_check)
    at = AppTest.from_file(APP, default_timeout=30)
    at.secrets["ANTHROPIC_API_KEY"] = "test-key"
    at.run()
    at.toggle(key="demo_mode").set_value(False).run()
    at.button(key="demo_body_wash").click().run()
    click(at, "Compare")
    click(at, "Compare")
    assert calls == [("Petal Glow Body Wash", "Ridge Body Wash")]
    assert at.session_state.result["report"].verdict == POTENTIAL_PREMIUM


def test_demo_mode_photo_storyline_end_to_end():
    from demo_pairs import DEMO_IMAGES

    at = AppTest.from_file(APP, default_timeout=30).run()
    at.button(key="demo_everyday_body_wash").click().run()
    at.toggle(key="photo_mode").set_value(True).run()
    # Renamed on purpose: demo images are recognized by content, on either card.
    pink = ("IMG_0001.png", DEMO_IMAGES["pink_label"].read_bytes(), "image/png")
    blue = ("IMG_0002.png", DEMO_IMAGES["blue_label"].read_bytes(), "image/png")
    at.file_uploader(key="a_photo").set_value(pink).run()
    at.file_uploader(key="b_photo").set_value(blue).run()
    assert not at.exception
    for side, price, label in (("a", "12.99", "women"), ("b", "9.99", "men")):
        assert at.session_state[f"{side}_photo_error"] is None
        assert at.session_state[f"{side}_attributes"] == "Function: body cleanser. Aloe + glycerin."
        assert at.session_state[f"{side}_price"] == price   # the photo never sets price
        assert at.session_state[f"{side}_label"] == label   # no printed label: kept
    click(at, "Compare")
    assert at.session_state.result["report"].verdict == POTENTIAL_PREMIUM


def test_demo_mode_unknown_photo_on_b_shows_demo_error():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.button(key="demo_everyday_body_wash").click().run()
    at.toggle(key="photo_mode").set_value(True).run()
    # A real PNG that isn't a demo image, even though it's named like one.
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, format="PNG")
    at.file_uploader(key="b_photo").set_value(("pink_label.png", buf.getvalue(), "image/png")).run()
    assert not at.exception
    assert at.session_state["b_photo_error"].startswith("Demo mode has saved readings only")
    assert at.session_state["b_attributes"] == "Function: body cleanser. Aloe + glycerin."  # unchanged


def test_corrupt_upload_does_not_crash_page():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.toggle(key="photo_mode").set_value(True).run()
    at.file_uploader(key="a_photo").set_value(("label.png", b"\x89PNG broken", "image/png")).run()
    assert not at.exception
    assert any(c.value == "Can't preview this file" for c in at.caption)


def test_every_demo_pair_has_card_photos():
    from demo_pairs import DEMO_PAIRS

    photos = Path(APP).parent / "assets" / "demo_photos"
    for pair_id in DEMO_PAIRS:
        for side in ("a", "b"):
            assert (photos / f"{pair_id}_{side}.png").is_file(), f"{pair_id}_{side}.png"


def test_hero_pink_caption():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert any(c.value == "Yes, it's pink. That's the point." for c in at.caption)
