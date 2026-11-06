# PinkTax Detective: Design Spec (Streamlit, 2 people)

plan.md wins on any conflict with this file. This file covers look, layout,
and copy only. Owner: frontend teammate (app.py, .streamlit/, README.md).

## 1. What the page is for
A shopper puts two products side by side and gets an honest answer: is this
the same product sold at a higher price to women, or not? Then she finds
cheaper equivalents and sees what she could save.

Demo order: Compare -> Discover alternatives -> My Savings.

The one memorable element is the verdict card with its savings number.
Everything else stays quiet.

## 2. Tokens

### Color (.streamlit/config.toml)
| Role | Hex |
|---|---|
| primaryColor (buttons, active tab, toggles) | #B0285F |
| backgroundColor (page) | #FFF7FA |
| secondaryBackgroundColor (sidebar, inputs) | #FCE4EE |
| textColor (body) | #2E1A24 |

White text on #B0285F is about 6.3:1, which passes WCAG AA for normal text.
Don't add other pinks. Status colors come from Streamlit's own st.success,
st.warning, st.info, and st.error so they stay readable.

### Type
Use the theme's sans-serif. Check which `font` values the installed Streamlit
version accepts. No custom font files: they add load risk to a live demo.
Hierarchy: st.title once, st.header per tab, st.subheader per card.
Sentence case everywhere. No all-caps labels.

### Layout
- st.set_page_config(page_title="PinkTax Detective", layout="wide")
- Product cards: st.container(border=True), two st.columns side by side.
- Key numbers: st.metric.
- unsafe_allow_html only for one constant CSS string in app.py; never
  interpolate variables, user input, or Claude output. Everything else
  renders without it. The page shows Claude output and text read from
  images, so injected HTML would break the trust boundary.

## 3. Page structure

```
PinkTax Detective
Same purpose. Better choices.
Compare two products and see if the one marketed to women really costs more.
[ Potential savings this session: $X.XX ]          <- st.metric, top right

[ Compare ] [ Discover alternatives ] [ My Savings ]   <- st.tabs

Sidebar: Demo mode toggle, Photo upload toggle, "DEMO DATA" note
```

### Tab 1: Compare
```
Try a demo pair:  [Body wash] [Razor] [Deodorant]

+--------- Product A ---------+  +--------- Product B ---------+
| (photo uploader, if on)     |  | (photo uploader, if on)     |
| Name / Price / Quantity     |  | ...same fields...           |
| Unit / Pack count / Label   |  |                             |
| Key attributes (text area)  |  |                             |
| Source URL / Date seen      |  |                             |
+-----------------------------+  +-----------------------------+
Times bought per year (optional)
[ Compare these products ]

+------------------- Verdict card -------------------+
| <verdict headline>              DEMO DATA badge     |
| metric: per-unit A | per-unit B | premium %         |
| Savings line (POTENTIAL_PREMIUM only)               |
| [ Swap it ]  (POTENTIAL_PREMIUM only)              |
| Why: reasons                                       |
| Differences found (table) / Missing info / Notes   |
| One pair is not evidence of a market-wide pattern. |
+----------------------------------------------------+
```

### Tab 2: Discover alternatives
- Uses the last compared product, or a text box if there isn't one.
- Shows 3 search terms as buttons or a horizontal row, each with links to
  Google Shopping, Amazon, and Target (built by pinktax/alternatives.py).
- Note under the links: "Found a candidate? Enter it as Product B and compare
  again."

### Tab 3: My Savings
- st.metric: total potential savings, and yearly if set.
- List of swaps: pair name, savings, date, [Remove].
- Total is always recomputed from the list (pinktax/savings.py).
- Footnote: "Potential savings, estimated. Not confirmed purchases."

## 4. Verdict copy (display text for each code)
| Code | Headline | Streamlit element |
|---|---|---|
| POTENTIAL_PREMIUM | Potential pink tax on this pair | st.warning |
| NO_OBSERVED_PREMIUM | No premium found on this pair | st.success |
| NOT_COMPARABLE | These aren't the same product | st.info |
| INSUFFICIENT_EVIDENCE | Not enough information to judge | st.info |
| PRICE_COMPARISON_ONLY | Price comparison only | st.info |

Every status shows its headline text, never color alone.

Savings line: "The men's version costs $X less per 100 ml. That's $Y less at
this size." Add "About $Z a year" if times bought per year is set.

## 5. States and copy
| State | Copy |
|---|---|
| Field error | "<Field> must be a number greater than 0." |
| Comparing | st.spinner("Checking whether these are the same product...") |
| Claude unavailable | "Couldn't check equivalence right now. Try again, or turn on Demo mode." |
| Photo read failed | "Couldn't read this photo. Fill in the fields by hand." |
| No alternatives | "No search terms for this product yet. Try adding more attributes." |
| Swap saved | st.toast("Saved to My Savings") |
| Swap already saved | Button shows "Saved to My Savings", disabled |
| No swaps yet | "No swaps yet. Compare a pair to find your first one." |

## 6. Interaction rules
- Store every result in st.session_state so reruns don't call Claude again.
- Demo pair buttons fill the forms only. The verdict always comes from
  compare().
- Swap is idempotent by pair key.
- Photo extraction fills editable fields only, and price only if visible.

## 7. Out of scope
React/FastAPI, product image grids, live product results, LocalStorage,
accounts, community totals, achievements/badges, animations beyond
Streamlit defaults.
