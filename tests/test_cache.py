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


def test_cache_upsert_updates_existing(cache):
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
    # Re-upsert with updated title — should replace, not ignore
    updated = ClassifiedChange(
        id="abc123",
        title="Test Updated",
        date=date(2026, 3, 15),
        url="http://example.com/1",
        source="eurlex",
        regulation="dora",
        type="guideline",
        urgency="medium",
        summary=None,
    )
    assert cache.upsert([updated]) == 1
    results = cache.query()
    assert len(results) == 1
    assert results[0].title == "Test Updated"


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


def test_cache_upsert_updates_existing_data(cache):
    """Edge: INSERT OR REPLACE should update changed fields."""
    change1 = ClassifiedChange(id="abc", title="Old title", date=date(2026, 3, 15),
              url="http://example.com/1", source="eurlex", regulation=None,
              type="legislative_act", urgency="medium", summary=None)
    cache.upsert([change1])

    change2 = ClassifiedChange(id="abc", title="Updated title", date=date(2026, 3, 15),
              url="http://example.com/1", source="eurlex", regulation="dora",
              type="guideline", urgency="high", summary="Now classified")
    cache.upsert([change2])

    results = cache.query()
    assert len(results) == 1
    assert results[0].title == "Updated title"
    assert results[0].regulation == "dora"
    assert results[0].summary == "Now classified"


def test_cache_query_multiple_regulations(cache):
    """Edge: filtering by multiple regulations at once."""
    changes = [
        ClassifiedChange(id="1", title="DORA", date=date(2026, 3, 15),
                         url="http://example.com/1", source="eurlex",
                         regulation="dora", type="guideline", urgency="medium", summary=None),
        ClassifiedChange(id="2", title="MiCA", date=date(2026, 3, 15),
                         url="http://example.com/2", source="eurlex",
                         regulation="mica", type="guideline", urgency="medium", summary=None),
        ClassifiedChange(id="3", title="AI Act", date=date(2026, 3, 15),
                         url="http://example.com/3", source="eurlex",
                         regulation="ai_act", type="guideline", urgency="medium", summary=None),
    ]
    cache.upsert(changes)
    results = cache.query(regulations=["dora", "mica"])
    assert len(results) == 2
    regs = {r.regulation for r in results}
    assert regs == {"dora", "mica"}


def test_cache_query_combined_filters(cache):
    """Edge: multiple filters applied simultaneously."""
    changes = [
        ClassifiedChange(id="1", title="DORA guideline", date=date(2026, 3, 15),
                         url="http://example.com/1", source="eurlex",
                         regulation="dora", type="guideline", urgency="medium", summary=None),
        ClassifiedChange(id="2", title="DORA consultation", date=date(2026, 3, 15),
                         url="http://example.com/2", source="esma",
                         regulation="dora", type="consultation", urgency="high", summary=None),
        ClassifiedChange(id="3", title="MiCA guideline", date=date(2026, 3, 15),
                         url="http://example.com/3", source="eurlex",
                         regulation="mica", type="guideline", urgency="medium", summary=None),
    ]
    cache.upsert(changes)
    results = cache.query(regulations=["dora"], sources=["eurlex"], types=["guideline"])
    assert len(results) == 1
    assert results[0].title == "DORA guideline"
