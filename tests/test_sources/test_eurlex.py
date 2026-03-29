from datetime import date

import pytest

from regwatch.models import RawChange
from regwatch.regulations import ALL_REGULATIONS
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


def test_eurlex_query_uses_correct_cdm_predicates():
    """Regression: query must use expression_belongs_to_work, not work_has_expression."""
    source = EurLexSource()
    query = source._build_query(since=date(2026, 1, 1), regulations=ALL_REGULATIONS)
    assert "expression_belongs_to_work" in query
    assert "work_has_expression" not in query
    assert "expression_uses_language" in query
    assert "LANG(?title)" not in query  # Must use URI, not LANG() function
    assert "language/ENG" in query


def test_eurlex_fetch_empty_regulations():
    """Regression: empty regulations list should return [], not crash with invalid SPARQL."""
    source = EurLexSource()
    result = source.fetch(since=date(2026, 1, 1), regulations=[])
    assert result == []


def test_eurlex_parses_datetime_string_in_date_field():
    """Edge: EUR-Lex may return datetime strings, not just dates."""
    source = EurLexSource()
    mock_response = {
        "results": {
            "bindings": [
                {
                    "title": {"type": "literal", "value": "Test Act"},
                    "date": {"type": "literal", "value": "2026-03-15T00:00:00"},
                    "cellarURI": {"type": "uri", "value": "http://example.com/work"},
                }
            ]
        }
    }
    changes = source._parse_response(mock_response)
    assert len(changes) == 1
    assert changes[0].date == date(2026, 3, 15)  # Should truncate to date


def test_eurlex_skips_entries_without_url():
    """Edge: entries with missing URL should be skipped."""
    source = EurLexSource()
    mock_response = {
        "results": {
            "bindings": [
                {
                    "title": {"type": "literal", "value": "No URL"},
                    "date": {"type": "literal", "value": "2026-03-15"},
                    "cellarURI": {"type": "uri", "value": ""},
                }
            ]
        }
    }
    changes = source._parse_response(mock_response)
    assert len(changes) == 0


def test_eurlex_skips_entries_without_title():
    """Edge: entries with missing title should be skipped."""
    source = EurLexSource()
    mock_response = {
        "results": {
            "bindings": [
                {
                    "title": {"type": "literal", "value": ""},
                    "date": {"type": "literal", "value": "2026-03-15"},
                    "cellarURI": {"type": "uri", "value": "http://example.com"},
                }
            ]
        }
    }
    changes = source._parse_response(mock_response)
    assert len(changes) == 0


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
