"""Tests for RegWatch.update() pipeline — the core fetch→classify→cache flow."""

from datetime import date, timedelta
from unittest.mock import MagicMock

from regwatch import DEFAULT_INITIAL_LOOKBACK_DAYS, RegWatch
from regwatch.models import RawChange


def _make_raw(title="Test DORA update", url="http://example.com/1", source="eurlex"):
    return RawChange(
        title=title,
        date=date(2026, 3, 15),
        url=url,
        source=source,
    )


def test_update_happy_path_classifies_and_caches(tmp_path):
    """update() should fetch from sources, classify, and upsert into cache."""
    rw = RegWatch(cache_dir=str(tmp_path / ".rw"))
    fake_source = MagicMock()
    fake_source.id = "fake"
    fake_source.fetch.return_value = [_make_raw()]
    rw._sources = [fake_source]

    stats = rw.update()

    assert stats["fake"] >= 0
    fake_source.fetch.assert_called_once()
    # Verify item landed in cache
    df = rw.check(since="2026-01-01")
    assert len(df) == 1
    assert df.iloc[0]["title"] == "Test DORA update"


def test_update_source_failure_returns_minus_one(tmp_path):
    """When a source raises, update() logs and returns -1 for that source."""
    rw = RegWatch(cache_dir=str(tmp_path / ".rw"))
    failing_source = MagicMock()
    failing_source.id = "broken"
    failing_source.fetch.side_effect = ConnectionError("timeout")
    rw._sources = [failing_source]

    stats = rw.update()

    assert stats["broken"] == -1


def test_update_source_filter(tmp_path):
    """update(source='x') only fetches from source x."""
    rw = RegWatch(cache_dir=str(tmp_path / ".rw"))
    src_a = MagicMock()
    src_a.id = "a"
    src_a.fetch.return_value = []
    src_b = MagicMock()
    src_b.id = "b"
    src_b.fetch.return_value = []
    rw._sources = [src_a, src_b]

    stats = rw.update(source="a")

    assert "a" in stats
    assert "b" not in stats
    src_a.fetch.assert_called_once()
    src_b.fetch.assert_not_called()


def test_update_since_none_defaults_to_180_days(tmp_path):
    """When cache has no last_update, update uses 180 days ago as since."""
    rw = RegWatch(cache_dir=str(tmp_path / ".rw"))
    fake_source = MagicMock()
    fake_source.id = "test"
    fake_source.fetch.return_value = []
    rw._sources = [fake_source]

    rw.update()

    call_args = fake_source.fetch.call_args
    since_arg = call_args.kwargs["since"]
    expected = date.today() - timedelta(days=DEFAULT_INITIAL_LOOKBACK_DAYS)
    assert since_arg == expected


def test_update_classification_pipeline(tmp_path):
    """update() correctly classifies regulation, type, and urgency."""
    rw = RegWatch(cache_dir=str(tmp_path / ".rw"))
    fake_source = MagicMock()
    fake_source.id = "test"
    fake_source.fetch.return_value = [
        _make_raw(title="DORA consultation on ICT risk management"),
    ]
    rw._sources = [fake_source]

    rw.update()

    df = rw.check(since="2026-01-01")
    assert len(df) == 1
    row = df.iloc[0]
    assert row["regulation"] == "dora"
    assert row["type"] == "consultation"
    assert row["urgency"] == "high"


def test_update_with_llm_fallback_integration(tmp_path):
    """update() passes llm_classify to classify_regulation when configured."""
    fake_llm = MagicMock(return_value="mica")
    rw = RegWatch(cache_dir=str(tmp_path / ".rw"))
    rw._llm_classify = fake_llm
    fake_source = MagicMock()
    fake_source.id = "test"
    fake_source.fetch.return_value = [
        _make_raw(title="Something ambiguous about crypto", url="http://example.com/2"),
    ]
    rw._sources = [fake_source]

    rw.update()

    df = rw.check(since="2026-01-01")
    assert len(df) == 1
    assert df.iloc[0]["regulation"] == "mica"
    fake_llm.assert_called_once()
