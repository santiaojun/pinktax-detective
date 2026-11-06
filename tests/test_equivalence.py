import json
from decimal import Decimal
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from demo_pairs import DEMO_PAIRS
from pinktax.equivalence import blind_prompt, cache_key, check, parse
from pinktax.gendered import contains_gendered
from pinktax.models import INSUFFICIENT_EVIDENCE, POTENTIAL_PREMIUM, Product
from pinktax.verdict import COULDNT_CHECK, compare

VALID = {
    "comparable": "yes",
    "differences": [{"attribute": "scent", "a": "rose", "b": "cedar", "material": False}],
    "missing": [],
    "note": "Same formula; only the scent differs.",
}
REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


class FakeClient:
    """Stands in for anthropic.Anthropic; records each request."""

    def __init__(self, text=None, stop_reason="end_turn", error=None):
        self.calls = []
        self._text, self._stop, self._error = text, stop_reason, error
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return SimpleNamespace(
            stop_reason=self._stop,
            content=[SimpleNamespace(type="text", text=self._text)],
        )


def product(side):
    fields = DEMO_PAIRS["body_wash"][side]
    return Product(**{**fields, "price": Decimal(fields["price"]),
                      "quantity": Decimal(fields["quantity"])})


def sent_text(call):
    return call["system"] + "\n" + "\n".join(m["content"] for m in call["messages"])


# Valid / invalid JSON

def test_valid_json_returns_dict_for_gate_b():
    client = FakeClient(json.dumps(VALID))
    result = check(product("a"), product("b"), client=client)
    assert result == VALID
    assert compare(product("a"), product("b"), result).verdict == POTENTIAL_PREMIUM


def test_extra_fields_dropped():
    result = parse({**VALID, "verdict": "NO_OBSERVED_PREMIUM", "price": "0.01"})
    assert set(result) == {"comparable", "differences", "missing", "note"}


@pytest.mark.parametrize("raw", [
    "not json",
    "{\"comparable\": \"maybe\"}",
    {"comparable": "yes", "differences": "none"},
    {"comparable": "yes", "differences": [{"attribute": "x", "a": "1", "b": "2"}]},
    {"comparable": "yes", "differences": [], "missing": [], "note": "x" * 501},
    ["yes"],
])
def test_invalid_json_returns_none(raw):
    assert parse(raw) is None
    client = FakeClient(raw if isinstance(raw, str) else json.dumps(raw))
    result = check(product("a"), product("b"), client=client)
    assert result is None
    r = compare(product("a"), product("b"), result)
    assert r.verdict == INSUFFICIENT_EVIDENCE and r.reasons == [COULDNT_CHECK]


# Timeout / API errors

@pytest.mark.parametrize("error", [
    anthropic.APITimeoutError(request=REQUEST),
    anthropic.APIConnectionError(request=REQUEST),
    anthropic.InternalServerError(
        "boom", response=httpx2.Response(500, request=REQUEST), body=None),
])
def test_api_errors_return_none(error):
    assert check(product("a"), product("b"), client=FakeClient(error=error)) is None


@pytest.mark.parametrize("stop", ["refusal", "max_tokens"])
def test_non_end_turn_returns_none(stop):
    client = FakeClient(json.dumps(VALID), stop_reason=stop)
    assert check(product("a"), product("b"), client=client) is None


def test_request_sets_timeout():
    client = FakeClient(json.dumps(VALID))
    check(product("a"), product("b"), client=client)
    assert client.calls[0]["timeout"] > 0


# Blindness

def test_price_label_name_never_sent():
    a = product("a")
    b = product("b")
    # A careless shopper pastes the name, price, and label into attributes.
    a.attributes = f"{a.name}, $6.49, for women. " + a.attributes
    b.attributes = f"{b.name} USD 6.49 men's " + b.attributes
    client = FakeClient(json.dumps(VALID))
    check(a, b, client=client)
    text = sent_text(client.calls[0])
    for p in (a, b):
        assert p.name not in text
        assert p.label not in text.lower().split()
    assert "6.49" not in text
    assert not contains_gendered(blind_prompt(a, b))
    # Attributes and sizes do get through.
    assert "glycerin" in text and "12 fl_oz" in text and "18 fl_oz" in text


def test_cache_key_ignores_price_label_name():
    a, b = product("a"), product("b")
    key = cache_key(a, b, model="m")
    a.price, a.name, a.label = Decimal("1"), "Other", "neutral"
    assert cache_key(a, b, model="m") == key
    a.attributes += " Blade count: 5."
    assert cache_key(a, b, model="m") != key
