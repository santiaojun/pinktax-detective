"""Three synthetic product pairs. DEMO DATA: invented names, prices, and URLs.

Each pair is form input only. The verdict always comes from compare(); the
saved equivalence JSON in fixtures/equivalence/<pair_id>.json stands in for
Claude's answer in Demo mode.
"""

import json
from datetime import date
from pathlib import Path
from typing import Optional

DEMO_LABEL = "DEMO DATA"
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "equivalence"
EXTRACTION_DIR = Path(__file__).parent / "fixtures" / "extraction"
DEMO_IMAGE_DIR = Path(__file__).parent / "fixtures" / "demo_images"

# Synthetic label photos (no brands, only the color differs) for the photo
# demo. Keys are demo_name values for extract.from_image(demo=True).
DEMO_IMAGES = {
    "pink_label": DEMO_IMAGE_DIR / "pink_label.png",
    "blue_label": DEMO_IMAGE_DIR / "blue_label.png",
}

DEMO_PAIRS = {
    "body_wash": {
        "title": "Body wash",
        "a": {
            "name": "Petal Glow Body Wash",
            "price": "6.49",
            "quantity": "12",
            "unit": "fl_oz",
            "pack_count": 1,
            "label": "women",
            "attributes": "Function: daily body cleanser. Cleansers: sodium laureth sulfate, "
                          "cocamidopropyl betaine. Moisturizer: glycerin. Scent: rose.",
            "source_url": "https://example.com/demo/petal-glow-body-wash",
            "date_seen": date(2026, 11, 6),
        },
        "b": {
            "name": "Ridge Body Wash",
            "price": "6.49",
            "quantity": "18",
            "unit": "fl_oz",
            "pack_count": 1,
            "label": "men",
            "attributes": "Function: daily body cleanser. Cleansers: sodium laureth sulfate, "
                          "cocamidopropyl betaine. Moisturizer: glycerin. Scent: cedar.",
            "source_url": "https://example.com/demo/ridge-body-wash",
            "date_seen": date(2026, 11, 6),
        },
    },
    "razor": {
        "title": "Disposable razors",
        "a": {
            "name": "Silk Glide Disposable Razor",
            "price": "9.99",
            "quantity": "4",
            "unit": "count",
            "pack_count": 1,
            "label": "women",
            "attributes": "Disposable razor. Blade count: 3. Lubricating strip: aloe. "
                          "Handle: plastic, pink.",
            "source_url": "https://example.com/demo/silk-glide-razor",
            "date_seen": date(2026, 11, 6),
        },
        "b": {
            "name": "Edge Pro Disposable Razor",
            "price": "9.99",
            "quantity": "4",
            "unit": "count",
            "pack_count": 1,
            "label": "men",
            "attributes": "Disposable razor. Blade count: 5. Lubricating strip: aloe. "
                          "Handle: plastic, black.",
            "source_url": "https://example.com/demo/edge-pro-razor",
            "date_seen": date(2026, 11, 6),
        },
    },
    "deodorant": {
        "title": "Deodorant",
        "a": {
            "name": "Fresh Bloom Antiperspirant",
            "price": "5.49",
            "quantity": "2.6",
            "unit": "oz",
            "pack_count": 1,
            "label": "women",
            "attributes": "Antiperspirant stick. Active ingredient: aluminum zirconium "
                          "tetrachlorohydrex gly 18%. Protection: 48 hours. Scent: powder.",
            "source_url": "https://example.com/demo/fresh-bloom-antiperspirant",
            "date_seen": date(2026, 11, 6),
        },
        "b": {
            "name": "Summit Deodorant",
            "price": "5.29",
            "quantity": "3",
            "unit": "oz",
            "pack_count": 1,
            "label": "men",
            "attributes": "Stick. Scent: pine.",
            "source_url": "https://example.com/demo/summit-deodorant",
            "date_seen": date(2026, 10, 30),
        },
    },
}


def load_equivalence_fixture(pair_id: str) -> Optional[dict]:
    """Saved equivalence JSON for a demo pair, or None if missing or unreadable."""
    return _load_json(FIXTURE_DIR / f"{pair_id}.json")


def load_extraction_fixture(name: str) -> Optional[dict]:
    """Saved photo-extraction JSON (product A's label) for a demo pair, or None."""
    return _load_json(EXTRACTION_DIR / f"{name}.json")


def _load_json(path: Path) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
