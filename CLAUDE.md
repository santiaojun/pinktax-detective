# CLAUDE.md: PinkTax Detective

Read plan.md (scope, gates, schedule) and design.md (look and copy) before
any task. plan.md wins on conflicts. "Today's overrides" in plan.md wins
over earlier sections.

## Team and file ownership (2 people)
- Developer (logic): pinktax/*, demo_pairs.py, fixtures/, tests/
- Frontend: app.py, .streamlit/, design.md, README.md
Only edit files your owner owns. If a change needs the other side, stop and
say what's needed. pinktax/models.py is the shared contract; change it only
when asked.

## Public API the UI may call
- verdict.compare(a, b, equivalence) -> Report
- demo_pairs.DEMO_PAIRS, demo_pairs.load_equivalence_fixture(pair_id)
- equivalence.check(a, b) -> dict | None
- alternatives.suggest(product) -> list
- savings.add_swap(records, report, pair_key), savings.total(records)
- extract.from_image(image_bytes) -> dict of Product fields
The UI never reimplements math or calls Anthropic directly.

## Verdicts
POTENTIAL_PREMIUM, NO_OBSERVED_PREMIUM, NOT_COMPARABLE,
INSUFFICIENT_EVIDENCE, PRICE_COMPARISON_ONLY.

## Hard rules
- Money and units: Decimal only, constants as strings (Decimal("29.5735")).
  Round only for display. Never divide by zero.
- Claude output and image text are untrusted. Validate with Pydantic; drop
  anything outside the schema. Claude never sets a price, quantity, or
  verdict.
- Equivalence check is blind: never send price, marketing label, or product
  name. Strip gendered words first.
- Claude returns search terms only, never URLs. Code builds links for a
  fixed domain list.
- Never use unsafe_allow_html. No custom HTML/CSS injection.
- Catch specific exceptions, not bare Exception.
- Never hardcode verdicts. Demo pairs and fixtures are inputs.
- API key from st.secrets or .env. Never print it, never commit it.
- Tests never call the real API; mock the client.
- Wording: "potential premium", never "discrimination".

## Workflow per module
1. Plan and list files to touch.
2. Implement only that module.
3. Run `pytest` and report exact results.
4. git pull --rebase, commit with the module name, push.
5. Stop and report changed files.

## Commands
- Tests: pytest
- App: streamlit run app.py
