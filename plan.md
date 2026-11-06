---
type: note
tags: [hackathon, topic/pink-tax]
status: in-progress
created: 2026-11-06
---

# PinkTax Detective — Hackathon Plan

Tailored from my teammate's 10-hour plan for **Code with Claude: Women in AI Hackathon** (Anthropic SF, Nov 6). Copy into the repo as `plan.md` for Claude Code.

- **Challenge:** 3, Economic mobility ("tools weren't designed with them in mind").
- **Build time:** about 2 hours. Hacking starts after the talks and workshop.
- **Submit:** demo video + public GitHub repo link, one per team, **by 12:45 PM**. A deploy isn't required.
- **Data rule:** public or synthetic data only. No real personal or health information.
- **Product statement:** compare two products marketed to women vs. men, decide whether they're really equivalent, normalize price per unit, and report a *potential* premium with evidence, plus what a shopper saves by picking the equivalent.

## What changed from the 10-hour plan
- **Cut** for time: deployment, SQLite, idempotency/concurrency, the agent orchestrator, the React + FastAPI split. A local app plus a video is enough.
- **Stack:** one Streamlit app in Python, so no CORS or API wiring.
- **Claude's role:** a *blind* equivalence check (it sees attributes and sizes only, never the price, gender label, or product name), plus optional photo extraction. All math stays deterministic Python with `Decimal`.
- **Units:** added `fl_oz` and `oz`, because US products are labeled that way.
- **Added** a shopper-facing savings line as a P0 must-have, so the build helps women's financial stability and doesn't stop at a verdict.
- **Credits:** the event gives API credits through the Claude Console claim link. Test the key at kickoff.

## 0. Scope

### P0: must ship (in this order)
1. Two product cards (manual form): name, price (USD), quantity, unit (`ml`, `l`, `fl_oz`, `g`, `kg`, `oz`, `count`), pack count, marketing label (`women` | `men` | `neutral` | `unknown`), key attributes (free text: function, ingredients, blade count, material…), source URL, date seen.
2. Deterministic engine: unit normalization, per-unit price, premium %, verdict gates (section 3).
3. Claude equivalence check (section 2), validated JSON, feeding Gate B.
4. Report: verdict, reasons, attribute differences, missing data, context warnings, a `DEMO DATA` label, and the caveat "one pair is not evidence of a market-wide pattern."
5. Savings line on `POTENTIAL_PREMIUM`: "The men's equivalent costs $X less per 100 ml ($Y less at this size)." Optional "times bought per year" → yearly savings. Deterministic `Decimal` math in `verdict.py`. This line is the link to Challenge 3.
6. Three demo pairs: `POTENTIAL_PREMIUM`, `NOT_COMPARABLE`, `INSUFFICIENT_EVIDENCE`.
7. About 6 pytest tests on the math, gates, and savings.

### P1: only if P0 works end to end before 11:50
- Photo upload → Claude vision fills the form fields, which stay editable. Never auto-fill the price unless it's visible on the label.

### Out of scope
Scraping, live prices, browser extension, accounts, payments, price tracking, deployment, persistence, multi-agent loops, causal claims about discrimination, market-wide statistics.

**Fallback:** if the API key or credits fail, manual input + deterministic compare + the demo pairs must still run.

## 1. Stack
| Layer | Choice |
|---|---|
| App | Streamlit (single `app.py`) |
| AI | Anthropic Python SDK; `ANTHROPIC_MODEL=claude-sonnet-5-5` |
| Math | pure Python modules + `Decimal` |
| Validation | Pydantic models for Claude's JSON |
| Tests | pytest |
| Config | `.env` (gitignored) with `ANTHROPIC_API_KEY`; commit `.env.example` |

If a teammate is much faster in React, keep FastAPI + one page instead, but budget 30 minutes for wiring. Decide at kickoff.

## 2. Architecture
```text
Streamlit page
  Product A card | Product B card   (manual; P1: photo -> Claude extract -> editable)
  [Compare]
    -> normalize.py    unit conversion, per-unit price          deterministic
    -> equivalence.py  Claude: attribute differences as JSON    AI, untrusted
    -> verdict.py      gates A-D, premium %, savings            deterministic
  Report panel
```

**Blind equivalence check.** Send Claude only the two products' attributes and sizes. Don't send the price, the marketing label, or the product name, because names like "Women's … razor" give the label away. Strip gendered words (women's, men's, for her, for him, pink…) from the attributes before sending. Ask for:
```json
{"comparable": "yes | no | unclear",
 "differences": [{"attribute": "blade count", "a": "5", "b": "3", "material": true}],
 "missing": ["ingredients for product B"],
 "note": "one sentence"}
```
**Trust boundary:** Claude's output and any text in an image are untrusted data. Validate against the schema. Claude never sets a price, a quantity, or the verdict directly. `unsafe_allow_html` only for one constant CSS string in app.py; never interpolate variables, user input, or Claude output. Everything else renders without it.

## 3. Verdict gates
- **Gate A, enough data:** both prices > 0, quantities > 0, units convertible to the same dimension. Otherwise `INSUFFICIENT_EVIDENCE`. A mismatch like ml vs g with no density is `NOT_COMPARABLE`.
- **Gate B, equivalence:** any difference with `material: true` → `NOT_COMPARABLE`. Invalid JSON or an API failure → `INSUFFICIENT_EVIDENCE`, with the reason "couldn't check equivalence". `unclear` → `INSUFFICIENT_EVIDENCE`, with the reason "Couldn't confirm these are the same product." (plus "See missing information." when Claude lists missing data).
- **Gate C, context:** a different retailer, date, or sale status adds a warning but doesn't block.
- **Gate D, observed difference:** only for a `women` vs `men` pair. If the women's per-unit price is higher → `POTENTIAL_PREMIUM`, otherwise `NO_OBSERVED_PREMIUM`. A `neutral` or `unknown` label gets a plain price comparison only, with no gender verdict.

`premium_pct = (women_unit_price - men_unit_price) / men_unit_price * 100`, using `Decimal`. Round only for display, and never divide by zero. Equal prices → 0% and `NO_OBSERVED_PREMIUM`.

**Conversions:** 1 l = 1000 ml; 1 fl_oz = 29.5735 ml; 1 kg = 1000 g; 1 oz = 28.3495 g. Per-unit basis: per 100 ml, per 100 g, or per item (count × pack count).

## 4. Edge cases to cover
| Case | Behavior |
|---|---|
| Empty, negative, or non-numeric price/quantity | Field error, no compare |
| 500 ml vs 1 l; 16 fl_oz vs 500 ml | Convert to the same basis |
| ml vs g | `NOT_COMPARABLE` (no density) |
| 2-pack vs 1-pack | Per-item price uses pack count |
| `unknown` label | No gender verdict |
| Claude returns bad JSON or times out | `INSUFFICIENT_EVIDENCE`, manual path still works |
| Image text says "ignore instructions…" | Treated as data; schema validation drops it |
| Identical prices | 0%, `NO_OBSERVED_PREMIUM` |

## 5. Schedule (fixed points come from the 12:45 deadline)
| When | What |
|---|---|
| Kickoff, first 15 min | Pick the stack, create the public GitHub repo, `.env`, one test API call; freeze units and verdicts |
| Next ~35 min | **M1** `normalize.py` + `verdict.py` + tests (person A). **M2** Streamlit form + report with a stub verdict (person B), in parallel |
| Next ~30 min | **M3** `equivalence.py` wired into Gate B; bad-output fallback (person C) |
| Until 11:50 | All 3 demo pairs run end to end. P1 only if green |
| **12:05** | **Feature freeze.** No new code |
| 12:05–12:25 | Record the 2-minute demo video; push; short README |
| **By 12:35** | Submit video + repo link (10 minutes of buffer) |

## 6. Team roles (up to 4)
- **A:** deterministic engine + tests
- **B:** Streamlit UI + report
- **C:** Claude prompts (equivalence, P1 vision) + Pydantic validation
- **D:** the 3 demo pairs, video script, pitch, README

With 2 people, merge A+C and B+D. Each person owns their own files, and one person merges, which avoids Git conflicts.

## 7. Demo data
- Find 3 pairs on a public retailer page (razors, body wash, deodorant…) and record the URL, date seen, price, and size. Or write synthetic pairs and label them `DEMO DATA`.
- Use "potential premium for this pair on this date" wording only. Real brand names show up in a public video and repo.
- No receipts, accounts, or anything personal.

## 8. Video + pitch (2 minutes)
1. Problem (20 s): products marketed to women can cost more for the same thing. Cite one named source, e.g. the NYC Department of Consumer Affairs 2015 study "From Cradle to Cane", and check the figure before quoting it.
2. Demo (70 s): the 3 pairs, ending on the savings line.
3. How it works (20 s): Claude judges equivalence *blind*, without seeing the price, gender label, or product name; all math is deterministic and tested.
4. Limits and next steps (10 s): one pair isn't proof of discrimination; next would be a matched-pair dataset and retailer APIs.

## 9. Claude Code protocol
One module at a time:
1. Plan and list the files to touch.
2. Implement only that module.
3. Run `pytest` and report the exact results.
4. Stop and report.

Commit after each module (`M1: engine`, `M2: UI`, …). Never hardcode demo verdicts: demo pairs are inputs, not overrides.

**Starter instruction:**
> Read `plan.md` in full. Implement **M1 only**: `pinktax/normalize.py` and `pinktax/verdict.py` per sections 3–4, with pytest tests in `tests/`. Pure Python and `Decimal`, no Claude calls, no UI. Run `pytest`, report results and changed files, then stop.

## 10. Risks
1. **Credits not landed / API down:** the manual + deterministic path is the demo's backbone.
2. **Claude misjudges equivalence:** the report lists every difference, so viewers can see why.
3. **Causality:** say "potential premium", never "discrimination".
4. **Time:** freeze at 12:05 no matter what. A working small demo beats a broken big one.

## Today's overrides (supersede earlier sections where they conflict)
- Team: 2 people, ~3 hours. Live demo + deploy on Streamlit Community Cloud.
- Roles: A = normalize.py, verdict.py, equivalence.py, extract.py, tests/.
  B = app.py, demo_pairs.py, README.md, deploy.
- Shared contract: pinktax/models.py (Product, Report, compare signature).
  Change only with both people's agreement.
- Equivalence rubric: material = function, active ingredients, blade count,
  SPF, performance specs. NOT material = scent, color, packaging look.
- Savings at size = per-unit difference × women's product quantity.
  Yearly = that × times bought per year.
- API key: st.secrets["ANTHROPIC_API_KEY"]; .streamlit/secrets.toml is gitignored.
- Cache Claude results in st.session_state keyed by input hash.
- Demo mode toggle: uses saved Claude JSON fixtures (equivalence + extraction),
  still passed through the same gates.
- P1 photo extraction is IN, behind a toggle. It fills editable form fields only,
  price only if visible. If the 3 manual pairs aren't end-to-end by T+110,
  photo stays off.
- Feature freeze at T+150.
- Approved scope: alternatives.py, savings.py, the three tabs (Compare,
  Discover alternatives, My Savings), and the session savings metric.
- Principle: look past the label. Essence terms come first; gendered swaps
  are secondary.
