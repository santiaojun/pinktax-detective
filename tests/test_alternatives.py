import json
from types import SimpleNamespace
from urllib.parse import urlparse

import anthropic
import httpx2
import pytest

from pinktax.alternatives import EMPTY, RETAILERS, build_links, from_payload, suggest
from pinktax.gendered import contains_gendered, strip_gendered

GOOD = {"essence_terms": ["UPF 50+ hooded jacket", "sun protection hoodie"],
        "other_terms": ["unisex UPF 50 hoodie"]}
ALLOWED_HOSTS = {"www.google.com", "www.amazon.com", "www.target.com"}


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


# Gendered words

def test_strip_gendered():
    assert strip_gendered("Women's sun protection jacket") == "sun protection jacket"
    assert strip_gendered("razor for her, pink") == "razor"
    assert strip_gendered("Men's 3-blade razor, aloe") == "3-blade razor, aloe"
    assert strip_gendered("Herbal garment for this mantel") == "Herbal garment for this mantel"


def test_contains_gendered():
    assert contains_gendered("MEN'S razor")
    assert contains_gendered("ladies’ watch")
    assert not contains_gendered("human-made steel mantel, this herbal")


# Links

def test_links_url_encoded():
    links = build_links("UPF 50+ jacket & hood/zip")
    assert links[1].url == "https://www.amazon.com/s?k=UPF%2050%2B%20jacket%20%26%20hood%2Fzip"


def test_links_only_whitelisted_domains():
    result = from_payload(GOOD)
    links = [l for s in result.essence + result.other for l in s.links]
    assert len(links) == 3 * len(RETAILERS)
    assert {urlparse(l.url).netloc for l in links} == ALLOWED_HOSTS
    assert all(urlparse(l.url).scheme == "https" for l in links)


def test_injected_term_cannot_change_domain():
    links = build_links("x&tbm=&q=@evil.com/#")
    assert {urlparse(l.url).netloc for l in links} <= ALLOWED_HOSTS


# Validation

@pytest.mark.parametrize("payload", [
    "not json",
    "{\"essence_terms\": [\"one\"]}",                       # too few
    {"essence_terms": ["a", "b", "c", "d"], "other_terms": []},  # too many
    {"essence_terms": ["a", "b"], "other_terms": ["x", "y", "z"]},
    {"essence_terms": ["razor", "https://evil.com"], "other_terms": []},
    {"essence_terms": ["razor", "buy at shop.com"], "other_terms": []},
    {"other_terms": []},
    ["a", "b"],
])
def test_bad_json_returns_empty(payload):
    assert from_payload(payload) is EMPTY


def test_gendered_essence_term_rejected():
    payload = {"essence_terms": ["women's razor", "5 blade razor"], "other_terms": []}
    assert from_payload(payload) is EMPTY


def test_gendered_other_term_allowed():
    payload = {"essence_terms": ["5 blade razor", "aloe strip razor"],
               "other_terms": ["men's 5 blade razor"]}
    assert [s.term for s in from_payload(payload).other] == ["men's 5 blade razor"]


def test_extra_fields_dropped():
    result = from_payload({**GOOD, "urls": ["https://evil.com"], "verdict": "X"})
    assert [s.term for s in result.essence] == GOOD["essence_terms"]


# suggest() with a mocked client

def test_suggest_strips_gender_before_sending():
    client = FakeClient(json.dumps(GOOD))
    result = suggest("Women's sun protection jacket for her", client=client)
    sent = client.calls[0]["messages"][0]["content"]
    assert "sun protection jacket" in sent
    assert not contains_gendered(sent)
    assert [s.term for s in result.essence] == GOOD["essence_terms"]


@pytest.mark.parametrize("client", [
    FakeClient("{bad json"),
    FakeClient(json.dumps(GOOD), stop_reason="refusal"),
    FakeClient(json.dumps(GOOD), stop_reason="max_tokens"),
    FakeClient(error=anthropic.APIConnectionError(
        request=httpx2.Request("POST", "https://api.anthropic.com"))),
])
def test_suggest_failures_return_empty(client):
    assert suggest("razor", client=client) is EMPTY


def test_empty_after_stripping_skips_call():
    client = FakeClient(json.dumps(GOOD))
    assert suggest("for her", client=client) is EMPTY
    assert client.calls == []


# Demo mode

@pytest.mark.parametrize("query", [
    "women's razor", "Women's sun protection jacket", "jewelry organizer",
])
def test_demo_fixtures(query):
    result = suggest(query, demo=True, client=FakeClient(error=AssertionError("no API in demo")))
    assert 2 <= len(result.essence) <= 3
    assert not any(contains_gendered(s.term) for s in result.essence)


def test_demo_unknown_query_empty():
    assert suggest("garden hose", demo=True) is EMPTY
