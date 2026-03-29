from datetime import date

import pytest

from regwatch.models import RawChange
from regwatch.regulations.dora import dora
from regwatch.sources.esma import EsmaSource


def test_esma_source_has_id():
    source = EsmaSource()
    assert source.id == "esma"
    assert source.name == "ESMA"


def test_esma_extract_date_from_html_time_tag():
    source = EsmaSource()
    html = '<p><time datetime="2026-03-15T10:00:00Z">15 March 2026</time></p>'
    result = source._extract_date(html)
    assert result == date(2026, 3, 15)


def test_esma_extract_date_regex_fallback():
    source = EsmaSource()
    text = "Published on 15 March 2026 by ESMA"
    result = source._extract_date(text)
    assert result == date(2026, 3, 15)


def test_esma_extract_date_none_fallback():
    source = EsmaSource()
    result = source._extract_date("No date here at all")
    assert result == date.today()


def test_esma_parse_entry():
    source = EsmaSource()
    entry = {
        "title": "ESMA publishes DORA guidelines",
        "link": "https://www.esma.europa.eu/press-news/esma-news/example",
        "summary": (
            '<p><time datetime="2026-03-15T10:00:00Z">15 March 2026</time></p>'
            "<p>Some description about DORA guidelines.</p>"
        ),
    }
    result = source._parse_entry(entry)
    assert isinstance(result, RawChange)
    assert result.title == "ESMA publishes DORA guidelines"
    assert result.source == "esma"
    assert result.date == date(2026, 3, 15)
    assert "<" not in result.description  # HTML stripped


def test_esma_returns_items_without_keyword_in_title():
    """Regression: RSS source must not pre-filter by keywords. Classifier handles that."""
    source = EsmaSource()
    entry = {
        "title": "New regulatory standards published",  # No regulation keywords
        "link": "https://www.esma.europa.eu/test",
        "summary": (
            '<time datetime="2026-03-15T10:00:00+01:00">15 March 2026</time>'
            " About MiCA crypto-assets"
        ),
    }
    result = source._parse_entry(entry)
    assert result is not None
    assert result.title == "New regulatory standards published"
    # The source returns it; the classifier (not the source) decides relevance


def test_esma_date_extraction_iso_datetime():
    """Edge: time tag might have full ISO datetime."""
    source = EsmaSource()
    html = '<time datetime="2026-03-15T14:30:00+01:00">15 March 2026</time>'
    assert source._extract_date(html) == date(2026, 3, 15)


def test_esma_date_extraction_no_html():
    """Edge: plain text with no HTML tags."""
    source = EsmaSource()
    result = source._extract_date("Just some text with no dates")
    assert result == date.today()


def test_esma_parse_entry_empty_title_returns_none():
    """Edge: entry with empty title should be skipped."""
    source = EsmaSource()
    entry = {"title": "", "link": "https://example.com", "summary": "content"}
    assert source._parse_entry(entry) is None


def test_esma_parse_entry_empty_link_returns_none():
    """Edge: entry with empty link should be skipped."""
    source = EsmaSource()
    entry = {"title": "Some title", "link": "", "summary": "content"}
    assert source._parse_entry(entry) is None


@pytest.mark.integration
def test_esma_fetch_live():
    source = EsmaSource()
    results = source.fetch(since=date(2025, 1, 1), regulations=[dora])
    assert isinstance(results, list)
    # ESMA feed may or may not have DORA-related entries; just check structure
    for r in results:
        assert isinstance(r, RawChange)
        assert r.source == "esma"
        assert r.title
        assert r.url
