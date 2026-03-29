from datetime import date

import pytest

from regwatch.models import RawChange
from regwatch.regulations.dora import dora
from regwatch.sources.eba import EbaSource


def test_eba_source_has_id():
    source = EbaSource()
    assert source.id == "eba"
    assert source.name == "EBA"


def test_eba_parse_entry_with_pubdate():
    source = EbaSource()
    # feedparser converts published_parsed to a time.struct_time
    import time

    entry = {
        "title": "EBA publishes DORA technical standards",
        "link": "https://www.eba.europa.eu/news-press/news/example",
        "summary": "<p>Some description about DORA standards.</p>",
        "published_parsed": time.strptime("2026-03-15", "%Y-%m-%d"),
    }
    result = source._parse_entry(entry)
    assert isinstance(result, RawChange)
    assert result.title == "EBA publishes DORA technical standards"
    assert result.source == "eba"
    assert result.date == date(2026, 3, 15)
    assert "<" not in result.description


def test_eba_parse_entry_missing_pubdate():
    source = EbaSource()
    entry = {
        "title": "EBA update",
        "link": "https://www.eba.europa.eu/news-press/news/example2",
        "summary": "Some update",
    }
    result = source._parse_entry(entry)
    assert result.date == date.today()


@pytest.mark.integration
def test_eba_fetch_live():
    source = EbaSource()
    results = source.fetch(since=date(2025, 1, 1), regulations=[dora])
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, RawChange)
        assert r.source == "eba"
        assert r.title
        assert r.url
