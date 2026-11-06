# PinkTax Detective: design.md

Design system for `pinktax-detective-v3.html`. Every value below is taken from that file. If the file and this document disagree, the file wins; update this document.

## 1. Purpose and tone

PinkTax Detective compares two products, normalizes the price, and reports whether a price difference is real. The interface should feel like a careful tool, not a campaign.

- Plain and specific. Headings name the job ("Search with neutral terms", "Compare products", "Total savings").
- Evidence first. Every number sits next to what it was computed from (unit basis, size, label).
- Calm about claims. Say "potential premium for this pair on this date". Never say "discrimination". Never tell the shopper to "buy this".
- Light mode only (`color-scheme: light`).

## 2. Principles

1. **One accent.** A single deep rose is reserved for primary actions and the active tab. Nothing decorative uses it.
2. **Flat structure.** Sections are separated by 1px borders and flat fills. No shadows, blur, gradients or glows.
3. **Two tints, one job.** Pale pink and pale blue only identify Product A and Product B. They carry no other meaning.
4. **Report on demand.** The page stays at two steps plus a savings pane. The full report lives in a dialog.
5. **Mixed layout.** Open tables, a split summary, a sticky side pane and tinted product cards. Do not stack identical cards.

## 3. Color

Roughly 70% base, 20% structure, 10% accent.

| Token | Hex | Role |
|---|---|---|
| `--bg` | `#F6F5F3` | Page background, dialog background |
| `--surface` | `#FFFFFF` | Savings pane, inputs, savings block, search field |
| `--line` | `#E2DFDA` | Hairlines, table row dividers, pane border |
| `--line-strong` | `#CFCBC4` | Input, segmented control and ghost button borders |
| `--neutral-tint` | `#EEECE8` | Hover fill, disabled fill, bar track, neutral mark |
| `--a-tint` | `#FBEAF0` | Product A card fill, A table columns |
| `--a-deep` | `#E9B3C8` | Product A card border, A price bar, "potential premium" mark |
| `--b-tint` | `#E8F0F9` | Product B card fill, B table columns |
| `--b-deep` | `#A9C4E4` | Product B card border, B price bar, "no premium / price only" mark |
| `--ink` | `#1B1A1F` | Text, focus ring, selected segment, "withheld" mark |
| `--muted` | `#625F68` | Secondary text, labels, captions |
| `--accent` | `#B4145A` | Primary button, active tab underline, link hover |
| `--accent-hover` | `#97104B` | Primary button hover |

Rules:

- Accent is used for primary buttons, the active report tab underline, link hover and the error border. Nowhere else.
- Pink and blue tints identify A and B. Do not reuse them as status colors outside the verdict marks below.
- Contrast was checked by hand, not with a tool. Roughly: accent on white 6.6:1, muted on `--bg` 5.6:1. Re-check with a contrast tool before shipping.

### Verdict marks

The verdict is shown as a small mark carrying the code, plus the label in large display type. Color is never the only signal: the code and label always appear as text.

| Verdict code | Label | Mark fill |
|---|---|---|
| `POTENTIAL_PREMIUM` | Potential premium | `--a-deep` |
| `NO_OBSERVED_PREMIUM` | No observed premium | `--b-deep` |
| `PRICE_COMPARISON_ONLY` | Price comparison only | `--b-deep` |
| `NOT_COMPARABLE` | Not comparable | `--neutral-tint` |
| `INSUFFICIENT_EVIDENCE` | Insufficient evidence | `--neutral-tint` |

## 4. Typography

| Role | Family | Weight | Notes |
|---|---|---|---|
| Display | Bricolage Grotesque | 600 / 700 / 800 | Headings, big numbers. Tight tracking. |
| Body | DM Sans | 400 / 500 / 600 | Everything else |
| Mono | system mono stack | 400 | Search terms, verdict codes, Claude result |

Loaded from Google Fonts. Fallbacks: `system-ui`, `-apple-system`, `Segoe UI`, `sans-serif`.

| Style | Size | Weight | Tracking | Used for |
|---|---|---|---|---|
| Page title | 44px (34px under 600px) | 800 | -0.04em | `h1`, line-height 1 |
| Step heading | 26px | 700 | -0.035em | "Search…", "Compare…" |
| Verdict label | 44px (34px under 600px) | 800 | -0.035em | Report summary |
| Total savings figure | 52px | 800 | -0.04em | Savings pane |
| Pane / dialog heading | 22px / 24px | 700 | -0.035em | `h2` |
| Card title | 22px | 700 | -0.035em | Product name |
| Section heading | 20px, 18px | 700 | -0.035em | Report sections, sub-sections |
| Key number | 24px | 700 | -0.03em | Report summary numbers |
| Per-item saving | 20px | 700 | -0.03em | Savings pane rows |
| Body | 16px / 1.55 | 400–500 | normal | Default |
| Small | 14px | 400 | normal | Captions, help text |
| Label | 13px | 600 | normal | Form labels, "Product A" line, marks |
| Step number | 15px | 700 | 0 | The "1" and "2" before step headings |

Rules: sentence case everywhere. No all-caps labels. No tracked-out eyebrow text. Step numbers are allowed only because the two steps are a real sequence.

## 5. Spacing, radius, borders

- Page: `max-width: 1240px`, padding `48px 40px 80px`.
- Between the two steps: 64px. Between the header and the layout: 48px.
- Main and savings pane: grid, `minmax(0, 1fr)` and `340px`, 64px gap.
- Section interior gaps: 20 to 24px for cards and actions, 32 to 40px between report sections.
- Radii: 6px tag, 8px buttons, inputs and photos, 12px cards, pane and savings block, 14px dialog, 4px marks.
- Borders are 1px. The one exception is the active tab underline (3px, accent).
- No box shadows anywhere.

## 6. Layout

### Page

```
Header (title, one-line purpose, "Demo data" tag)
─────────────────────────────────────────────────
Main                                   | Total savings
 1  Search with neutral terms          | (sticky, top: 24px)
    search bar, example links,         |  total / year
    gender words removed,              |  list of added comparisons
    search terms table,                |  note
    candidates table                   |
 2  Compare products                   |
    mode switch (From search | Manual) |
    Product A | Product B cards        |
    Compare button                     |
Footer caveat
```

### Report dialog

```
Header (sticky): "A vs. B"                          [Close]
Tabs:  Summary | Details
Summary:  verdict + reasons (left)  |  key numbers (right)
          savings block: line, buys per year, per year, Add to total savings
          link to Details
Details:  Side by side (table + price bars)
          Checks run
          Blind equivalence check
          Attribute differences
          Missing data | Context warnings
```

### Breakpoints

| Width | Change |
|---|---|
| Under 980px | Layout becomes one column; savings pane is no longer sticky; report summary stacks |
| Under 600px | Smaller page padding (28px 18px 56px), 34px titles, card padding 18px, dialog padding 20px |

## 7. Components

### Buttons and links

| Component | Spec |
|---|---|
| Primary button | Min height 48px, padding 10 / 24, radius 8, accent fill, white text, weight 600. Hover: `--accent-hover`, 0.12s background change. |
| Ghost button | Transparent, ink text, `--line-strong` border. Hover: `--neutral-tint`. Used for "Compare with A", "Close". |
| Disabled button | `--neutral-tint` fill, muted text, `not-allowed` cursor. Used for "In total savings". |
| Text link button | Underlined, weight 600, min height 44px. Hover color: accent. Used for examples, "View report", "Remove". |
| Store links | Underlined text links in the search table. Never styled as buttons. |

Use one primary button per view. "Get search terms" and "Compare and open report" are the two primary actions on the page; "Add to total savings" is the primary action in the dialog.

### Segmented control

Two-option switch ("From search", "Manual"). 1px `--line-strong` border, radius 8, surface fill. Selected segment: ink fill, white text. Uses `aria-pressed`.

### Search bar

Min height 52px, radius 8, 17px text, magnifier icon inside at the left (the only decorative-looking icon, and it is functional). Focus: border turns ink, plus the global focus ring. Always paired with a visible "Get search terms" button.

### Search results

- A two-column definition list: "Removed from your search" (pink-deep marks) and "Neutral search" (mono).
- **Search terms table:** Type, Search term, Open in. Three rows: Neutral essence, Men's version, Commercial or professional. Each term shows a one-line check ("No gender words", "Men's version, an option", or "Contains a gender word"). The men's version is labeled as an option, never the default.
- **Candidates table:** Product, Price, Unit price, Label, action. Appears only when a cached result matches. If not, a single line explains how to continue manually.
- Claude writes search terms only. Links are built by code with `encodeURIComponent` for Google Shopping, Amazon and Target.

### Product card

- Radius 12, padding 24, flat fill and 1px border: A uses `--a-tint` / `--a-deep`, B uses `--b-tint` / `--b-deep`.
- Header: 112px photo square on the left, then "Product A · Marketed to women", the product name, and a muted source and date line.
- "From search" mode: a compact spec list (Price, Size, Attributes).
- "Manual" mode: a two-column form (name, price, quantity, unit, pack count, marketing label, key attributes, source URL, date seen). Every input has a visible label.
- Photo: demo images are random keyword images. A "Replace photo" text link uploads a local image. If an image fails or is missing, the frame shows "No photo yet".

### Form controls

Inputs, selects and textareas: min height 44px, radius 8, 1px `--line-strong` border, white fill, 13px / 600 muted label above. Validation errors appear in a white box with an accent border, announced with `role="alert"`, listing each field problem.

### Total savings pane

- Surface fill, 1px `--line`, radius 12, padding 28, sticky at the top on wide screens.
- Big yearly total (52px), "per year, estimated", then a list.
- Each row: "A → B" name, yearly amount (20px), "N buys × $X" caption, and two text links: View report, Remove.
- Empty state: "Run a comparison and add it here. Only equivalent products count toward savings."
- Counts only results with a saving: `POTENTIAL_PREMIUM`, or `PRICE_COMPARISON_ONLY` where one product is cheaper per unit.

### Report dialog

- Native `<dialog>` opened with `showModal()`. Width `min(1040px, 100vw - 32px)`, max height `100vh - 32px`, radius 14, `--bg` fill, 1px `--line-strong` border.
- Backdrop: flat `rgba(27, 26, 31, 0.5)`. No blur.
- Closes with Esc, the Close button, or a click on the backdrop.
- Sticky header with the title and tabs.

### Tabs

`role="tablist"` with two tabs. The selected tab has ink text and a 3px accent underline; the other is muted. Left and right arrow keys switch tabs. The panel is labelled by the active tab.

### Summary pieces

- **Verdict:** code mark, large label, and three reasons in a dotted list.
- **Key numbers:** open list with hairline dividers, label on the left, 24px figure and 13px note on the right.
- **Savings block:** surface fill, 1px border, radius 12. One sentence explaining the gap, a buys-per-year stepper, the yearly figure, and the add button.
- If there is no saving: "No saving to add for this result."

### Stepper

Inline control, 1px `--line-strong` border, radius 8, minus and plus buttons 44px square, current value between. Range 1 to 24. Defaults to 6 buys per year.

### Tables

13px muted header row with a strong bottom hairline, `--line` row dividers, no outer border. Row headers use `<th scope="row">`. Product A and B columns use the A and B tints. Wide tables scroll horizontally inside their own container.

### Marks

Small inline labels: 13px, weight 600, radius 4, padding 2 / 8. Variants: neutral (`--neutral-tint`), pink (`--a-deep`), blue (`--b-deep`), and ink (white text, used for "Withheld" items).

### Price bars

12px high, radius 3, `--neutral-tint` track. A uses `--a-deep`, B uses `--b-deep`. Widths are relative to the higher unit price. The unit basis always appears beside the value.

## 8. Interaction and motion

- Motion is limited to a 0.12s background color change on hover for buttons, the segmented control and steppers.
- No entrance animations, no scroll effects, no pulsing indicators.
- `prefers-reduced-motion: reduce` removes all transitions.
- Focus ring: 3px solid ink, 2px offset, on every focusable element.
- Touch targets are at least 44px high.

## 9. Accessibility

- Semantic HTML: `header`, `main`, `aside`, `section`, `dl` for specs, real `table` markup with `scope`.
- Search field has an `aria-label`; the search form has `role="search"`.
- Tabs follow the tablist pattern with `aria-selected`, `aria-controls` and arrow-key support.
- The dialog uses `aria-labelledby` and the native modal behavior.
- Form errors use `role="alert"`; the stepper value uses `aria-live="polite"`.
- Verdicts are text first; color only reinforces them.
- User-entered text is escaped before it is rendered.

## 10. Content rules

- Sentence case. Plain verbs. Buttons say what happens: "Get search terms", "Compare and open report", "Add to total savings".
- Never write "buy this" or imply a recommendation. Say "Found a candidate? Fill it into Product B and compare again."
- Always keep the caveat in the footer: one pair is not evidence of a market-wide pattern, and a potential premium is not proof of discrimination.
- Label demo content as demo content: the "Demo data" tag, "Synthetic pair, DEMO DATA", and the note about stock photos.
- A price gap without an equivalence check is never called a premium.

## 11. Never do

- Gradient backgrounds, ambient glow blobs, glassmorphism or backdrop blur.
- Animated gradient borders, pulsing dots, or plastic or abstract illustrations.
- An icon next to every label, header or list item.
- A second accent color, or using pink or blue as action colors.
- Identical stacked feature cards, or placeholder marketing copy.
- Letting Claude write URLs or set prices, quantities or verdicts.

## 12. Data and trust boundaries that shape the UI

- Claude's equivalence check sees attributes and sizes only. The report states this under "Blind equivalence check".
- Prices, units and verdicts come from deterministic code. The HTML file contains a JavaScript stand-in for the Python `normalize.py` and `verdict.py`; the Python `Decimal` code remains the source of truth.
- Search terms in the mockup are cached Claude output (demo mode). Terms for unmatched searches come from a code fallback.
- Manual mode uses a simulated Claude dropdown (yes, no, unclear). Replace it with the real call in the app.

## 13. Known gaps

- Demo photos load from a random image service and need an internet connection.
- Store search link formats were not tested.
- The file has not been checked in a browser or with an automated accessibility tool.
- No dark mode.
