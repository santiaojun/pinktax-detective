from decimal import ROUND_HALF_UP, Decimal

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from demo_pairs import DEMO_LABEL, DEMO_PAIRS, load_equivalence_fixture
from pinktax.models import (
    INSUFFICIENT_EVIDENCE,
    LABELS,
    NO_OBSERVED_PREMIUM,
    NOT_COMPARABLE,
    POTENTIAL_PREMIUM,
    PRICE_COMPARISON_ONLY,
    UNITS,
    Product,
)
from pinktax.normalize import parse_positive
from pinktax.verdict import compare, yearly_savings

SIDES = {"a": "Product A", "b": "Product B"}
BLANK = {
    "name": "",
    "price": "",
    "quantity": "",
    "unit": "ml",
    "pack_count": 1,
    "label": "unknown",
    "attributes": "",
    "source_url": "",
    "date_seen": None,
}
VERDICT_DISPLAY = {
    POTENTIAL_PREMIUM: (st.warning, "Potential premium for this pair on this date"),
    NO_OBSERVED_PREMIUM: (st.success, "No observed premium for this pair"),
    NOT_COMPARABLE: (st.info, "Not comparable"),
    INSUFFICIENT_EVIDENCE: (st.info, "Insufficient evidence"),
    PRICE_COMPARISON_ONLY: (st.info, "Price comparison only"),
}
CAVEAT = "One pair is not evidence of a market-wide pattern."
MD_SPECIAL = "\\`*_{}[]()<>#+-.!|$~"


def esc(text) -> str:
    """Escape Markdown (and Streamlit's $...$ math) in untrusted text."""
    return "".join("\\" + c if c in MD_SPECIAL else c for c in str(text))


def money(value: Decimal) -> str:
    return f"${value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def has_api_key() -> bool:
    try:
        return "ANTHROPIC_API_KEY" in st.secrets
    except StreamlitSecretNotFoundError:
        return False


# --- state + callbacks ---

def init_state():
    for side in SIDES:
        for field, value in BLANK.items():
            st.session_state.setdefault(f"{side}_{field}", value)
    st.session_state.setdefault("demo_pair_id", None)
    st.session_state.setdefault("errors", {})
    st.session_state.setdefault("result", None)


def fill(values_by_side: dict, pair_id):
    for side, values in values_by_side.items():
        for field, value in values.items():
            st.session_state[f"{side}_{field}"] = value
    st.session_state.demo_pair_id = pair_id
    st.session_state.errors = {}
    st.session_state.result = None


def load_demo(pair_id: str):
    pair = DEMO_PAIRS[pair_id]
    fill({"a": pair["a"], "b": pair["b"]}, pair_id)


def clear_form():
    fill({"a": BLANK, "b": BLANK}, None)


def read_product(side: str, errors: dict):
    """Build a Product from the form, recording field errors from normalize."""
    s = st.session_state
    side_errors = {}
    parsed = {}
    for field in ("price", "quantity"):
        try:
            parsed[field] = parse_positive(s[f"{side}_{field}"], field)
        except ValueError as err:
            side_errors[field] = str(err)
    if side_errors:
        errors[side] = side_errors
        return None
    return Product(
        name=s[f"{side}_name"].strip() or SIDES[side],
        price=parsed["price"],
        quantity=parsed["quantity"],
        unit=s[f"{side}_unit"],
        pack_count=int(s[f"{side}_pack_count"]),
        label=s[f"{side}_label"],
        attributes=s[f"{side}_attributes"],
        source_url=s[f"{side}_source_url"].strip(),
        date_seen=s[f"{side}_date_seen"],
    )


def run_compare():
    errors = {}
    a, b = read_product("a", errors), read_product("b", errors)
    st.session_state.errors = errors
    if errors:
        st.session_state.result = None
        return

    pair_id = st.session_state.demo_pair_id
    equivalence = None
    if st.session_state.demo_mode and pair_id:
        equivalence = load_equivalence_fixture(pair_id)
    # Demo mode off: the live Claude check arrives in M3.

    st.session_state.result = {
        "report": compare(a, b, equivalence),
        "names": {"a": a.name, "b": b.name},
        "demo": pair_id is not None,
    }


# --- rendering ---

def product_form(side: str, container):
    errors = st.session_state.errors.get(side, {})
    with container:
        st.subheader(SIDES[side])
        st.text_input("Name", key=f"{side}_name")
        st.text_input("Price (USD)", key=f"{side}_price")
        if "price" in errors:
            st.error(errors["price"])
        q, u = st.columns([2, 1])
        q.text_input("Quantity", key=f"{side}_quantity")
        u.selectbox("Unit", UNITS, key=f"{side}_unit")
        if "quantity" in errors:
            st.error(errors["quantity"])
        p, l = st.columns(2)
        p.number_input("Pack count", min_value=1, step=1, key=f"{side}_pack_count")
        l.selectbox("Marketed to", LABELS, key=f"{side}_label")
        st.text_area("Key attributes", key=f"{side}_attributes",
                     help="Function, active ingredients, blade count, SPF, material...")
        st.text_input("Source URL", key=f"{side}_source_url")
        st.date_input("Date seen", key=f"{side}_date_seen")


def report_panel(result: dict):
    report = result["report"]
    names = result["names"]

    st.header("Report")
    if result["demo"]:
        st.badge(DEMO_LABEL, color="orange")
    show, title = VERDICT_DISPLAY[report.verdict]
    show(f"**{title}** ({report.verdict})")

    if report.unit_price_a is not None:
        basis = report.unit_basis
        cols = st.columns(3)
        cols[0].metric(esc(names["a"]), f"{money(report.unit_price_a)} / {basis}")
        cols[1].metric(esc(names["b"]), f"{money(report.unit_price_b)} / {basis}")
        if report.premium_pct is not None:
            pct = report.premium_pct.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            cols[2].metric("Women's premium", f"{pct}%")

    if report.verdict == POTENTIAL_PREMIUM:
        per = "item" if report.unit_basis == "item" else report.unit_basis
        st.success(esc(
            f"The men's equivalent costs {money(report.savings_per_unit)} less per {per} "
            f"({money(report.savings_at_size)} less at this size)."
        ))
        times = st.session_state.times_per_year
        if times:
            yearly = yearly_savings(report, times)
            st.success(esc(f"Bought {times} times a year, that's {money(yearly)} a year."))

    if report.reasons:
        st.subheader("Reasons")
        st.markdown("\n".join(f"- {esc(r)}" for r in report.reasons))
    if report.differences:
        st.subheader("Attribute differences")
        st.table([
            {
                "attribute": str(d.get("attribute", "")),
                "A": str(d.get("a", "")),
                "B": str(d.get("b", "")),
                "material": "yes" if d.get("material") is True else "no",
            }
            for d in report.differences
        ])
    if report.missing:
        st.subheader("Missing data")
        st.markdown("\n".join(f"- {esc(m)}" for m in report.missing))
    for warning in report.warnings:
        st.warning(esc(warning))

    st.caption(CAVEAT)


def main():
    st.set_page_config(page_title="PinkTax Detective", page_icon=":mag:", layout="wide")
    init_state()

    with st.sidebar:
        st.toggle("Demo mode", value=True, key="demo_mode",
                  help="Use saved equivalence JSON for demo pairs instead of calling Claude.")
        if not st.session_state.demo_mode:
            st.caption("The live Claude check isn't wired yet, so equivalence "
                       "can't be checked and Compare returns insufficient evidence.")
        elif not st.session_state.demo_pair_id:
            st.caption("Demo fixtures apply only after loading a demo pair.")
        st.caption(f"API key configured: {has_api_key()}")

    st.title("PinkTax Detective")
    st.write("Compare two products marketed to women and men, check they're really "
             "equivalent, and see the price per unit.")

    st.write("Load a demo pair:")
    cols = st.columns(len(DEMO_PAIRS) + 1)
    for col, (pair_id, pair) in zip(cols, DEMO_PAIRS.items()):
        col.button(pair["title"], key=f"demo_{pair_id}", on_click=load_demo,
                   args=(pair_id,), use_container_width=True)
    cols[-1].button("Clear", on_click=clear_form, use_container_width=True)
    if st.session_state.demo_pair_id:
        st.badge(DEMO_LABEL, color="orange")

    left, right = st.columns(2)
    product_form("a", left)
    product_form("b", right)

    st.number_input("Times bought per year (optional)", min_value=0, step=1,
                    value=0, key="times_per_year")
    st.button("Compare", type="primary", on_click=run_compare)

    if st.session_state.errors:
        st.error("Fix the highlighted fields, then compare again.")
    if st.session_state.result:
        report_panel(st.session_state.result)


main()
