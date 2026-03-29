import pandas as pd
import pytest

from regwatch import RegWatch


def test_regwatch_creates_cache(tmp_path):
    RegWatch(cache_dir=str(tmp_path / ".regwatch"))
    assert (tmp_path / ".regwatch" / "cache.db").exists()


def test_regwatch_regulations(regwatch_instance):
    regs = regwatch_instance.regulations()
    assert "dora" in regs and "mica" in regs
    assert len(regs) == 5


def test_regwatch_sources(regwatch_instance):
    sources = regwatch_instance.sources()
    assert "eurlex" in sources and "esma" in sources and "eba" in sources
    assert len(sources) == 3


def test_regwatch_check_returns_dataframe(regwatch_instance):
    df = regwatch_instance.check()
    assert isinstance(df, pd.DataFrame)
    expected_cols = {"date", "title", "regulation", "type", "source", "urgency", "url", "summary"}
    assert set(df.columns) == expected_cols


def test_regwatch_check_empty_cache(regwatch_instance):
    df = regwatch_instance.check()
    assert len(df) == 0


def test_regwatch_check_invalid_since_raises(tmp_path):
    """Regression: invalid date string should raise ValueError with message."""
    rw = RegWatch(cache_dir=str(tmp_path / ".regwatch"))
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        rw.check(since="not-a-date")


@pytest.mark.integration
def test_regwatch_update_and_check(tmp_path):
    rw = RegWatch(cache_dir=str(tmp_path / ".regwatch"))
    stats = rw.update()
    assert isinstance(stats, dict)
    assert "eurlex" in stats
    df = rw.check(since="2025-01-01")
    assert isinstance(df, pd.DataFrame)
    if len(df) > 0:
        assert "regulation" in df.columns
