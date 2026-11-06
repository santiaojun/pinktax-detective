from decimal import ROUND_HALF_UP, Decimal

import anthropic
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from demo_pairs import DEMO_LABEL, DEMO_PAIRS, load_equivalence_fixture
from pinktax import equivalence
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
from pinktax.alternatives import DEMO_QUERIES, suggest
from pinktax.normalize import parse_positive
from pinktax.verdict import compare, yearly_savings

try:
    from pinktax import savings as savings_mod
except ImportError:  # savings.py hasn't landed yet
    savings_mod = None

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
BLIND_NOTE = ("Claude saw only the two products' attributes and sizes, labeled A and B: "
              "not the price, the marketing label, or the product name.")
NO_SAVING = "No saving to add for this result."
MD_SPECIAL = "\\`*_{}[]()<>#+-.!|$~"
VIEWS = ["Discover", "Compare", "My Savings"]
EMPTY_SAVINGS = "No swaps yet. Compare a pair to find your first one."

# The only unsafe_allow_html string in the app: a constant, never interpolated.
CSS = """
<style>
.st-key-hero { text-align: center; padding: 1.5rem 0 0.5rem; }
.st-key-hero h2 { padding-bottom: 0.25rem; }
.st-key-discover_query { max-width: 640px; margin: 0 auto; }
.st-key-discover_query [data-baseweb="input"],
.st-key-discover_query input { border-radius: 999px; }
.st-key-pick_essence button,
.st-key-pick_other button { border-radius: 999px; }
.st-key-pick_other button { font-size: 0.85rem; }
.st-key-card_a, .st-key-card_b {
    border-radius: 12px; padding: 1.25rem; border: 1px solid;
}
.st-key-card_a { background: #FBEAF0; border-color: #E9B3C8; }
.st-key-card_b { background: #E8F0F9; border-color: #A9C4E4; }
.st-key-discover_note, .st-key-swaps_empty {
    border: 1px solid #E9B3C8; border-radius: 12px; padding: 1rem 1.25rem;
}
</style>
"""


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


def live_equivalence(a: Product, b: Product):
    """Claude's blind equivalence check, cached per input hash; None if unavailable."""
    if not has_api_key():
        return None
    model = st.secrets.get("ANTHROPIC_MODEL")
    key = equivalence.cache_key(a, b, model)
    cache = st.session_state.setdefault("equivalence_cache", {})
    if key not in cache:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        result = equivalence.check(a, b, client=client, model=model)
        if result is None:
            return None  # not cached, so Compare can retry
        cache[key] = result
    return cache[key]


# --- state + callbacks ---

def init_state():
    for side in SIDES:
        for field, value in BLANK.items():
            st.session_state.setdefault(f"{side}_{field}", value)
    st.session_state.setdefault("demo_pair_id", None)
    st.session_state.setdefault("errors", {})
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("report_open", False)
    st.session_state.setdefault("swaps", [])


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
    if st.session_state.demo_mode and pair_id:
        equivalence_result = load_equivalence_fixture(pair_id)
    elif not st.session_state.demo_mode:
        equivalence_result = live_equivalence(a, b)
    else:
        equivalence_result = None

    st.session_state.result = {
        "report": compare(a, b, equivalence_result),
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


def compare_and_open():
    """Compare button: run the comparison, then open the report dialog."""
    run_compare()
    result = st.session_state.result
    st.session_state.report_open = result is not None
    if result is not None and savings_mod is not None:
        a, b = read_product("a", {}), read_product("b", {})
        try:
            result["pair_key"] = savings_mod.pair_key(a, b)
        except ValueError:
            result["pair_key"] = None


def add_to_savings(result: dict):
    """Report button: save this pair to My Savings (savings.py does the math)."""
    names = result["names"]
    times = st.session_state.get("times_per_year") or None
    try:
        st.session_state.swaps = savings_mod.add_swap(
            st.session_state.swaps, result["report"], result["pair_key"],
            f"{names['a']} → {names['b']}", times)
    except ValueError:
        st.session_state.save_notice = NO_SAVING
        return
    st.session_state.save_notice = "Saved to My Savings"


def remove_from_savings(pair_key: str):
    st.session_state.swaps = savings_mod.remove_swap(st.session_state.swaps, pair_key)


def open_report():
    st.session_state.report_open = True


def close_report():
    st.session_state.report_open = False


def report_summary(result: dict):
    report = result["report"]
    names = result["names"]

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
        if savings_mod is not None and result.get("pair_key"):
            saved = savings_mod.has_swap(st.session_state.swaps, result["pair_key"])
            st.button("In total savings" if saved else "Add to total savings",
                      type="primary", disabled=saved, key="add_swap",
                      on_click=add_to_savings, args=(result,))
            notice = st.session_state.pop("save_notice", None)
            if notice:
                st.toast(notice)
    else:
        st.caption(NO_SAVING)

    if report.reasons:
        st.subheader("Reasons")
        st.markdown("\n".join(f"- {esc(r)}" for r in report.reasons))


def report_details(result: dict):
    report = result["report"]

    st.subheader("Blind equivalence check")
    st.caption(BLIND_NOTE)
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


def report_panel(result: dict):
    summary_tab, details_tab = st.tabs(["Summary", "Details"])
    with summary_tab:
        report_summary(result)
    with details_tab:
        report_details(result)
    st.caption(CAVEAT)


@st.dialog("Report", width="large", on_dismiss=close_report)
def report_dialog(result: dict):
    report_panel(result)
    if st.button("Close"):
        close_report()
        st.rerun()


def go_compare(term):
    """on_click callback: remember the term and switch to the Compare tab."""
    st.session_state["compare_prefill"] = term
    st.session_state["view"] = "Compare"


def clear_other(other_key: str):
    st.session_state[other_key] = None


def cached_suggest(query: str, demo: bool):
    """suggest() once per (query, demo): reruns must not call Claude again."""
    cache = st.session_state.setdefault("alt_cache", {})
    if (query, demo) not in cache:
        cache[(query, demo)] = suggest(query, demo=demo)
    return cache[(query, demo)]


def discover_view():
    with st.container(key="hero"):
        st.header("Same purpose. Better choices.")
        st.caption("Find what you need, not what marketing tells you.")
    query = st.text_input(
        "What do you want to buy?", key="discover_query",
        placeholder="What do you want to buy? e.g. razor",
        label_visibility="collapsed",
    ).strip()
    if st.session_state.demo_mode:
        st.caption("Demo mode searches: " + ", ".join(esc(q) for q in DEMO_QUERIES) + ".")
    if not query:
        return

    with st.spinner("Finding search terms..."):
        found = cached_suggest(query, st.session_state.demo_mode)
    if found.empty:
        st.info("No search terms for this product yet. Try adding more attributes.")
        return

    by_term = {s.term: s for s in found.essence + found.other}
    st.pills("Search for what it is", [s.term for s in found.essence],
             key="pick_essence", format_func=esc,
             on_change=clear_other, args=("pick_other",))
    if found.other:
        st.caption("Other options")
        st.pills("Other options", [s.term for s in found.other],
                 key="pick_other", format_func=esc, label_visibility="collapsed",
                 on_change=clear_other, args=("pick_essence",))

    term = st.session_state.get("pick_essence") or st.session_state.get("pick_other")
    if term not in by_term:
        st.caption("Pick a term to see where to search.")
        return
    cols = st.columns(len(by_term[term].links))
    for col, link in zip(cols, by_term[term].links):
        col.link_button(link.retailer, link.url, use_container_width=True)
    with st.container(key="discover_note"):
        st.write("Found a candidate? Compare it.")
        st.button("Compare it", type="primary", on_click=go_compare, args=(term,))


def savings_view():
    st.header("My Savings")
    records = st.session_state.swaps
    if savings_mod is None or not records:
        with st.container(key="swaps_empty"):
            st.write(EMPTY_SAVINGS)
        return
    total_col, yearly_col = st.columns(2)
    total_col.metric("Total potential savings", money(savings_mod.total(records)))
    yearly = savings_mod.yearly_total(records)
    if yearly > 0:
        yearly_col.metric("Per year, estimated", money(yearly))
    for record in records:
        with st.container(border=True):
            text, action = st.columns([4, 1])
            text.write(f"**{esc(record.label)}**")
            detail = f"{money(record.savings_at_size)} less at this size"
            if record.yearly_savings is not None:
                detail += f" · {money(record.yearly_savings)} a year"
            detail += f" · saved {record.date_saved.isoformat()}"
            text.caption(esc(detail))
            action.button("Remove", key=f"remove_{record.pair_key}",
                          on_click=remove_from_savings, args=(record.pair_key,))
    st.caption("Potential savings, estimated. Not confirmed purchases.")


def main():
    st.set_page_config(page_title="PinkTax Detective", page_icon=":mag:", layout="wide")
    init_state()

    with st.sidebar:
        st.toggle("Demo mode", value=True, key="demo_mode",
                  help="Use saved equivalence JSON for demo pairs instead of calling Claude.")
        if not st.session_state.demo_mode:
            st.caption("Compare asks Claude to check equivalence. Without an API "
                       "key it can't, and Compare returns insufficient evidence.")
        elif not st.session_state.demo_pair_id:
            st.caption("Demo fixtures apply only after loading a demo pair.")
        st.caption(f"API key configured: {has_api_key()}")

    st.markdown(CSS, unsafe_allow_html=True)
    title_col, metric_col = st.columns([3, 1])
    title_col.title("PinkTax Detective")
    if savings_mod is not None:
        metric_col.metric("Potential savings this session",
                          money(savings_mod.total(st.session_state.swaps)))
    discover_tab, compare_tab, savings_tab = st.tabs(
        VIEWS, key="view", on_change="rerun")

    with discover_tab:
        discover_view()

    with compare_tab:
        st.write("Compare two products marketed to women and men, check they're really "
                 "equivalent, and see the price per unit.")

        prefill = st.session_state.get("compare_prefill")
        if prefill:
            st.info(f"From Discover: you searched for {esc(prefill)}. Enter a candidate "
                    "you found as Product B, then compare.")

        st.write("Load a demo pair:")
        cols = st.columns(len(DEMO_PAIRS) + 1)
        for col, (pair_id, pair) in zip(cols, DEMO_PAIRS.items()):
            col.button(pair["title"], key=f"demo_{pair_id}", on_click=load_demo,
                       args=(pair_id,), use_container_width=True)
        cols[-1].button("Clear", on_click=clear_form, use_container_width=True)
        if st.session_state.demo_pair_id:
            st.badge(DEMO_LABEL, color="orange")

        left, right = st.columns(2)
        product_form("a", left.container(key="card_a"))
        product_form("b", right.container(key="card_b"))

        st.number_input("Times bought per year (optional)", min_value=0, step=1,
                        value=0, key="times_per_year")
        st.button("Compare", type="primary", on_click=compare_and_open)

        if st.session_state.errors:
            st.error("Fix the highlighted fields, then compare again.")
        if st.session_state.result:
            _, title = VERDICT_DISPLAY[st.session_state.result["report"].verdict]
            last, view = st.columns([3, 1])
            last.write(f"Last result: **{title}**")
            view.button("View report", on_click=open_report, use_container_width=True)

    with savings_tab:
        savings_view()

    if st.session_state.report_open and st.session_state.result:
        report_dialog(st.session_state.result)


main()
