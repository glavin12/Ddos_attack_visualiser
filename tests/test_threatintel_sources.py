"""Tests for the three threat-intel source adapters (URLhaus/Feodo/ThreatFox)."""

from __future__ import annotations

import json

import httpx

from ddos_attack_project.threatintel.sources.feodo import FeodoAdapter
from ddos_attack_project.threatintel.sources.threatfox import ThreatFoxAdapter
from ddos_attack_project.threatintel.sources.urlhaus import URLhausAdapter


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        headers={"Accept": "application/json"},
    )


# --- URLhaus -----------------------------------------------------------------


URLHAUS_PAYLOAD = {
    # Real URLhaus responses have no "host" field at all (the adapter derives
    # it from the URL) and append " UTC" to dateadded — both confirmed
    # against the live feed. Fixtures mirror that shape so a regression in
    # either assumption fails here instead of only in production.
    "3456789": [
        {
            "id": "3456789",
            "urlhaus_link": "https://urlhaus.abuse.ch/url/3456789/",
            "url": "http://bad.example/dropper.bin",
            "threat": "malware_download",
            "tags": ["Emotet", "dropper"],
            "dateadded": "2026-08-19 14:00:00 UTC",
        }
    ],
    "3456790": [
        {
            "id": "3456790",
            "urlhaus_link": "https://urlhaus.abuse.ch/url/3456790/",
            "url": "http://another.example/x.exe",
            "threat": "malware_download",
            "tags": [],
            "dateadded": "2026-08-19 13:45:00 UTC",
        }
    ],
}


async def test_urlhaus_parses_recent_feed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "urlhaus.abuse.ch" in str(request.url)
        return httpx.Response(200, content=json.dumps(URLHAUS_PAYLOAD).encode())

    adapter = URLhausAdapter(http_client=_client(handler))
    indicators = await adapter.fetch()
    assert len(indicators) == 2
    first = indicators[0]
    assert first.indicator == "http://bad.example/dropper.bin"
    assert first.host == "bad.example"
    assert first.indicator_type == "url"
    assert first.threat_family == "malware_download"
    assert first.source_url == "https://urlhaus.abuse.ch/url/3456789/"
    await adapter.aclose()


async def test_urlhaus_http_error_returns_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    adapter = URLhausAdapter(http_client=_client(handler))
    assert await adapter.fetch() == []
    await adapter.aclose()


async def test_urlhaus_respects_max_indicators() -> None:
    big_payload = {
        str(i): [
            {
                "id": str(i),
                "url": f"http://x.example/{i}",
                "threat": None,
                "tags": [],
                "dateadded": "2026-08-19 12:00:00 UTC",
                "urlhaus_link": f"https://urlhaus.abuse.ch/url/{i}/",
            }
        ]
        for i in range(500)
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=json.dumps(big_payload).encode())

    adapter = URLhausAdapter(http_client=_client(handler), max_indicators=25)
    assert len(await adapter.fetch()) == 25
    await adapter.aclose()


# --- Feodo -------------------------------------------------------------------


FEODO_PAYLOAD = [
    {
        "ip_address": "185.220.101.42",
        "port": 443,
        "status": "online",
        "hostname": None,
        "as_number": 12345,
        "as_name": "Example AS",
        "country": "NL",
        "first_seen": "2026-08-18 10:00:00",
        # Real Feodo Tracker reports last_online as a bare date (no time) —
        # confirmed against the live feed. This must still parse.
        "last_online": "2026-08-19",
        "malware": "Emotet",
    },
    {
        "ip_address": "1.2.3.4",
        "port": 80,
        "status": "online",
        "country": "US",
        "first_seen": "2026-08-19 12:00:00",
        "last_online": "2026-08-19 13:30:00",
        "malware": "TrickBot",
    },
]


async def test_feodo_parses_ip_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "feodotracker.abuse.ch" in str(request.url)
        return httpx.Response(200, content=json.dumps(FEODO_PAYLOAD).encode())

    adapter = FeodoAdapter(http_client=_client(handler))
    indicators = await adapter.fetch()
    assert len(indicators) == 2
    first = indicators[0]
    assert first.indicator == "185.220.101.42"
    assert first.host == "185.220.101.42"
    assert first.indicator_type == "ip"
    assert first.threat_family == "Emotet"
    assert "feodotracker.abuse.ch" in first.source_url
    await adapter.aclose()


async def test_feodo_skips_entries_without_timestamps() -> None:
    payload = [
        {"ip_address": "9.9.9.9", "country": "US"},  # no timestamps
        {
            "ip_address": "8.8.8.8",
            "country": "US",
            "first_seen": "2026-08-19 12:00:00",
            "last_online": "2026-08-19 12:00:00",
            "malware": "X",
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=json.dumps(payload).encode())

    adapter = FeodoAdapter(http_client=_client(handler))
    indicators = await adapter.fetch()
    assert len(indicators) == 1
    assert indicators[0].indicator == "8.8.8.8"
    await adapter.aclose()


# --- ThreatFox ---------------------------------------------------------------


THREATFOX_PAYLOAD = {
    "query_status": "ok",
    "data": [
        {
            "id": 555,
            "ioc": "3.3.3.3:8443",
            "ioc_type": "ip:port",
            "malware_printable": "Cobalt Strike",
            # Real ThreatFox timestamps carry a " UTC" suffix — confirmed
            # against the live API. This must still parse.
            "first_seen": "2026-08-19 09:00:00 UTC",
            "last_seen": "2026-08-19 14:00:00 UTC",
        },
        {
            "id": 556,
            "ioc": "https://phishy.example/pay",
            "ioc_type": "url",
            "malware_printable": "AgentTesla",
            "first_seen": "2026-08-19 10:00:00 UTC",
            "last_seen": "2026-08-19 12:00:00 UTC",
        },
    ],
}


async def test_threatfox_requires_key_but_returns_empty_without() -> None:
    adapter = ThreatFoxAdapter(api_key=None)
    assert await adapter.fetch() == []
    await adapter.aclose()


async def test_threatfox_parses_ip_and_url_iocs() -> None:
    received_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received_headers.update(dict(request.headers))
        return httpx.Response(200, content=json.dumps(THREATFOX_PAYLOAD).encode())

    adapter = ThreatFoxAdapter(
        api_key="tf-key",
        http_client=_client(handler),
    )
    indicators = await adapter.fetch()
    assert received_headers.get("auth-key") == "tf-key"
    assert len(indicators) == 2
    ip_ioc = next(i for i in indicators if i.indicator_type == "ip")
    assert ip_ioc.host == "3.3.3.3"
    assert ip_ioc.threat_family == "Cobalt Strike"
    url_ioc = next(i for i in indicators if i.indicator_type == "url")
    assert url_ioc.host == "phishy.example"
    assert "threatfox.abuse.ch/ioc/556" in (url_ioc.source_url or "")
    await adapter.aclose()


async def test_threatfox_skips_when_query_status_not_ok() -> None:
    payload = {"query_status": "illegal_search"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=json.dumps(payload).encode())

    adapter = ThreatFoxAdapter(api_key="tf-key", http_client=_client(handler))
    assert await adapter.fetch() == []
    await adapter.aclose()
