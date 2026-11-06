# PinkTax Detective

**Same purpose. Better choices.** Put two products side by side, find out
whether they're really the same thing, and see what you'd save by buying the
equivalent.

Live app: https://pinktax-detective.streamlit.app

Built at the Code with Claude: Women in AI Hackathon (Challenge 3, economic mobility).

## Why we built it

In Chinese online shopping communities, shoppers pass around a tip: search
with substitute words to skip gendered markups, for example looking for a
medical "prep razor" instead of a women's razor. It's an observation from
those communities, not survey data, but it captures the idea behind this app:
the product you need is often sold under a name that doesn't target you.

## Research

- **NYC Department of Consumer Affairs, "From Cradle to Cane: The Cost of
  Being a Female Consumer" (2015):** across nearly 800 products, women's
  versions cost 7% more on average. Women paid more in 42% of comparisons;
  men paid more in 18%.
- **Moshary, Tuchman & Bhatia, "Gender-Based Pricing in Consumer Packaged
  Goods: A Pink Tax?" (*Marketing Science*, 2023):** when women's and men's
  products with similar ingredients are compared, price gaps are small, and
  the women's version was cheaper in 3 of 5 categories.

So the useful question for a shopper isn't "is there a pink tax?" but "is
*this* pair the same product, and which one is the better buy?"

## Principle: look past the label

Judge a product by what it is (its function, active ingredients, and specs),
not by who it's marketed to. Essence terms come first; gendered swaps are
secondary.

The pink look is deliberate: the app is dressed like every product marketed to
women, and underneath it judges products blind. "Yes, it's pink. That's the
point."

## How it works

- **Essence search.** Describe a product ("women's sun protection jacket")
  and Claude suggests search terms for what it actually is ("UPF 50+ hooded
  jacket"), with gendered words stripped first and rejected from essence
  terms. Claude returns terms only; the app builds the Google Shopping,
  Amazon, and Target links itself from a fixed list.
- **Blind equivalence check.** Claude sees only each product's attributes and
  size, never the price, the marketing label, or the product name. It judges
  differences with a fixed rubric: function, active ingredients, blade count,
  SPF, and performance specs are material; scent, color, and packaging look
  are not.
- **Deterministic math.** Unit conversion, per-unit prices, the premium %, and
  savings are plain Python with `Decimal`, rounded only for display. Four
  gates decide the verdict in order (enough data, equivalence, context,
  observed difference); Claude never sets a price, quantity, or verdict.
- **Photo extraction.** Upload a label photo and Claude reads it into the
  form. Every field stays editable, the price is filled only if one is
  printed, and text in the image is treated as data, never instructions.
- **Savings hero.** A card at the top shows your potential savings this
  session, swaps saved, and your best swap, always recomputed from the
  saved list; duplicates don't double-count.
- **Illustrative product cards.** For the "women's razor" example, Discover
  also shows two illustrative cards: AI-generated images and example
  prices, labeled as such, with links to real retailer searches. They are not
  live prices or scraped data.

All Claude output is untrusted: it's validated with Pydantic, anything
outside the schema is dropped, and any failure falls back to the manual form.

Verdicts: `POTENTIAL_PREMIUM`, `NO_OBSERVED_PREMIUM`, `NOT_COMPARABLE`,
`INSUFFICIENT_EVIDENCE`, `PRICE_COMPARISON_ONLY`.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Demo mode (on by default) uses saved Claude answers in `fixtures/`, so the app
runs without an API key. For live checks, add your key to
`.streamlit/secrets.toml` (gitignored):

```toml
ANTHROPIC_API_KEY = "your-key-here"
```

## Try the demo

Everything below works with Demo mode on (no API key). The full 2-minute
script with exact numbers is in [docs/demo_script.md](docs/demo_script.md).

1. **Discover:** click the "women's razor" example, pick "5 blade disposable
   razor", and see the store links. "Compare it" switches to Compare.
2. **Compare, the main story:** click **Pink vs blue label**. Same Everyday
   Body Wash, only the label color differs: women's $12.99 vs men's $9.99
   (DEMO DATA), so **$2.75 vs $2.11 per 100 ml**, a 30% potential premium,
   **$3.00 less at this size**. Optionally turn on Photo upload and upload
   `fixtures/demo_images/pink_label.png` and `blue_label.png`: the fields fill
   from the label, and the price stays yours to enter.
3. **The other verdicts:** Body wash (potential premium), Disposable razors
   (not comparable: 3 vs. 5 blades), and Deodorant (insufficient evidence: no
   active ingredient listed). Each card shows a synthetic demo label.
4. **Report:** the Summary tab has the verdict, per-unit prices, and savings;
   Details has the blind equivalence check and every attribute difference.
   "Add to total savings" saves a premium pair, once.
5. **My Savings:** saved swaps, the total, and the yearly estimate.

## Tests

```bash
pytest
```

184 tests cover unit conversion, the verdict gates, savings, Claude output
validation, prompt blindness, and the UI flows, including the full Pink vs
blue storyline offline. Tests never call the real
API; the client is mocked.

## Limits

- **One pair is not evidence of discrimination**, or of a market-wide
  pattern. The app reports a *potential* premium for one pair on one date.
- **Demo prices are DEMO DATA.** Demo products, prices, and URLs are
  invented, and the demo label images are synthetic with no real brands.
- Equivalence is only as good as the attributes entered or read from a
  photo; the report lists every difference and missing detail so you can
  check it.
- No live prices, scraping, or price history.

## Team

- [santiaojun](https://github.com/santiaojun): engine, Claude integration,
  tests, docs
- [ch3nxi1iu](https://github.com/ch3nxi1iu): UI and design
