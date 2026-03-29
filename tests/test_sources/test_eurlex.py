from datetime import date

import pytest

from regwatch.models import RawChange
from regwatch.regulations.dora import dora
from regwatch.sources.eurlex import EurLexSource


def test_eurlex_source_has_id():
    source = EurLexSource()
    assert source.id == "eurlex"
    assert source.name == "EUR-Lex"


def test_eurlex_builds_sparql_query():
    source = EurLexSource()
    query = source._build_query(since=date(2026, 3, 1), regulations=[dora])
    assert "2026-03-01" in query
    assert "FILTER" in query
    assert "DORA" in query or "dora" in query.lower()


def test_eurlex_parses_sparql_response():
    source = EurLexSource()
    mock_response = {
        "results": {
            "bindings": [
                {
                    "cellarURI": {"value": "http://publications.europa.eu/resource/cellar/abc123"},
                    "title": {"value": "Commission Delegated Regulation on DORA"},
                    "date": {"value": "2026-03-15"},
                    "celex": {"value": "32022R2554"},
                },
                {
                    "cellarURI": {"value": "http://publications.europa.eu/resource/cellar/def456"},
                    "title": {"value": "DORA technical standards"},
                    "date": {"value": "2026-03-10"},
                    "celex": {"value": "32026R0001"},
                },
            ]
        }
    }
    results = source._parse_response(mock_response)
    assert len(results) == 2
    assert isinstance(results[0], RawChange)
    assert results[0].title == "Commission Delegated Regulation on DORA"
    assert results[0].date == date(2026, 3, 15)
    assert results[0].source == "eurlex"
    assert results[0].celex_id == "32022R2554"


def test_eurlex_handles_empty_response():
    source = EurLexSource()
    mock_response = {"results": {"bindings": []}}
    results = source._parse_response(mock_response)
    assert results == []


def test_eurlex_handles_missing_celex():
    source = EurLexSource()
    mock_response = {
        "results": {
            "bindings": [
                {
                    "cellarURI": {"value": "http://publications.europa.eu/resource/cellar/xyz"},
                    "title": {"value": "Some regulation"},
                    "date": {"value": "2026-03-20"},
                },
            ]
        }
    }
    results = source._parse_response(mock_response)
    assert len(results) == 1
    assert results[0].celex_id == ""


@pytest.mark.integration
def test_eurlex_fetch_live():
    source = EurLexSource()
    results = source.fetch(since=date(2026, 1, 1), regulations=[dora])
    assert isinstance(results, list)
    if len(results) > 0:
        r = results[0]
        assert isinstance(r, RawChange)
        assert r.source == "eurlex"
        assert r.title
        assert r.url
        assert r.date
