import sqlite3
from datetime import date

import pytest

from regwatch.cache import Cache
from regwatch.models import ClassifiedChange


@pytest.fixture
def cache(tmp_path):
    return Cache(str(tmp_path / "test_cache.db"))


def test_cache_creates_db(cache, tmp_path):
    assert (tmp_path / "test_cache.db").exists()


def test_cache_creates_schema(cache):
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "changes" in tables
    assert "schema_version" in tables
    conn.close()


def test_cache_upsert_new_items(cache):
    changes = [
        ClassifiedChange(
            id="abc123",
            title="Test",
            date=date(2026, 3, 15),
            url="http://example.com/1",
            source="eurlex",
            regulation="dora",
            type="guideline",
            urgency="medium",
            summary=None,
        )
    ]
    assert cache.upsert(changes) == 1


def test_cache_upsert_deduplicates(cache):
    change = ClassifiedChange(
        id="abc123",
        title="Test",
        date=date(2026, 3, 15),
        url="http://example.com/1",
        source="eurlex",
        regulation="dora",
        type="guideline",
        urgency="medium",
        summary=None,
    )
    cache.upsert([change])
    assert cache.upsert([change]) == 0


def test_cache_query_no_filters(cache):
    change = ClassifiedChange(
        id="abc123",
        title="Test",
        date=date(2026, 3, 15),
        url="http://example.com/1",
        source="eurlex",
        regulation="dora",
        type="guideline",
        urgency="medium",
        summary=None,
    )
    cache.upsert([change])
    results = cache.query()
    assert len(results) == 1
    assert results[0].regulation == "dora"


def test_cache_query_filter_regulation(cache):
    changes = [
        ClassifiedChange(
            id="1",
            title="DORA",
            date=date(2026, 3, 15),
            url="http://example.com/1",
            source="eurlex",
            regulation="dora",
            type="guideline",
            urgency="medium",
            summary=None,
        ),
        ClassifiedChange(
            id="2",
            title="MiCA",
            date=date(2026, 3, 15),
            url="http://example.com/2",
            source="eurlex",
            regulation="mica",
            type="guideline",
            urgency="medium",
            summary=None,
        ),
    ]
    cache.upsert(changes)
    results = cache.query(regulations=["dora"])
    assert len(results) == 1
    assert results[0].regulation == "dora"


def test_cache_query_filter_since(cache):
    changes = [
        ClassifiedChange(
            id="1",
            title="Old",
            date=date(2026, 1, 1),
            url="http://example.com/1",
            source="eurlex",
            regulation="dora",
            type="guideline",
            urgency="medium",
            summary=None,
        ),
        ClassifiedChange(
            id="2",
            title="New",
            date=date(2026, 3, 15),
            url="http://example.com/2",
            source="eurlex",
            regulation="dora",
            type="guideline",
            urgency="medium",
            summary=None,
        ),
    ]
    cache.upsert(changes)
    results = cache.query(since=date(2026, 3, 1))
    assert len(results) == 1
    assert results[0].title == "New"


def test_cache_query_filter_source(cache):
    changes = [
        ClassifiedChange(
            id="1",
            title="EUR-Lex",
            date=date(2026, 3, 15),
            url="http://example.com/1",
            source="eurlex",
            regulation="dora",
            type="guideline",
            urgency="medium",
            summary=None,
        ),
        ClassifiedChange(
            id="2",
            title="ESMA",
            date=date(2026, 3, 15),
            url="http://example.com/2",
            source="esma",
            regulation="dora",
            type="guideline",
            urgency="medium",
            summary=None,
        ),
    ]
    cache.upsert(changes)
    results = cache.query(sources=["esma"])
    assert len(results) == 1
    assert results[0].source == "esma"


def test_cache_last_update_returns_date(cache):
    change = ClassifiedChange(
        id="1",
        title="Test",
        date=date(2026, 3, 15),
        url="http://example.com/1",
        source="eurlex",
        regulation="dora",
        type="guideline",
        urgency="medium",
        summary=None,
    )
    cache.upsert([change])
    assert cache.last_update("eurlex") == date(2026, 3, 15)


def test_cache_last_update_returns_none(cache):
    assert cache.last_update("eurlex") is None


def test_cache_schema_version(cache):
    assert cache.schema_version() == 1
