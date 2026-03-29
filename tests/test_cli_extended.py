"""Extended CLI tests covering update, check --format csv, and status with data."""

from datetime import date
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from regwatch.cache import Cache
from regwatch.cli import cli
from regwatch.models import ClassifiedChange


def _seed_cache(tmp_path, items=None):
    """Helper to seed a cache with test data."""
    cache = Cache(str(tmp_path / "cache.db"))
    if items is None:
        items = [
            ClassifiedChange(
                id="item1", title="DORA consultation paper",
                date=date(2026, 3, 10), url="http://example.com/1",
                source="esma", regulation="dora", type="consultation",
                urgency="high", summary=None,
            ),
            ClassifiedChange(
                id="item2", title="MiCA technical standards",
                date=date(2026, 3, 12), url="http://example.com/2",
                source="eba", regulation="mica", type="rts_its",
                urgency="medium", summary=None,
            ),
        ]
    cache.upsert(items)
    cache.close()
    return items


def test_cli_update_passes_llm_api_key(tmp_path):
    """update command reads REGWATCH_LLM_API_KEY from env and passes to RegWatch."""
    runner = CliRunner()
    with patch("regwatch.cli.RegWatch") as mock_rw:
        instance = MagicMock()
        instance.update.return_value = {"eurlex": 0}
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        mock_rw.return_value = instance
        runner.invoke(cli, ["update"], env={
            "REGWATCH_CACHE_DIR": str(tmp_path),
            "REGWATCH_LLM_API_KEY": "sk-ant-test123",
        })
    mock_rw.assert_called_once_with(cache_dir=str(tmp_path), llm_api_key="sk-ant-test123")


def test_cli_update_happy_path(tmp_path):
    """update command prints source stats and total."""
    runner = CliRunner()
    mock_stats = {"eurlex": 3, "esma": 5, "eba": 2}
    with patch("regwatch.cli.RegWatch") as mock_rw:
        instance = MagicMock()
        instance.update.return_value = mock_stats
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        mock_rw.return_value = instance
        result = runner.invoke(cli, ["update"], env={"REGWATCH_CACHE_DIR": str(tmp_path)})

    assert result.exit_code == 0
    assert "10 new regulatory changes" in result.output


def test_cli_update_with_failures(tmp_path):
    """update command handles failed sources gracefully."""
    runner = CliRunner()
    mock_stats = {"eurlex": 3, "esma": -1, "eba": 2}
    with patch("regwatch.cli.RegWatch") as mock_rw:
        instance = MagicMock()
        instance.update.return_value = mock_stats
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        mock_rw.return_value = instance
        result = runner.invoke(cli, ["update"], env={"REGWATCH_CACHE_DIR": str(tmp_path)})

    assert result.exit_code == 0
    assert "ERROR" in result.output
    assert "1 source(s) failed" in result.output


def test_cli_check_csv_format(tmp_path):
    """check --format csv outputs CSV with headers."""
    _seed_cache(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["check", "--format", "csv", "--since", "2026-01-01"],
        env={"REGWATCH_CACHE_DIR": str(tmp_path)},
    )
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    assert "date" in lines[0]  # CSV header
    assert len(lines) >= 3  # header + 2 data rows


def test_cli_check_regulation_filter(tmp_path):
    """check --regulation dora only shows DORA items."""
    _seed_cache(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["check", "--regulation", "dora", "--since", "2026-01-01", "--format", "json"],
        env={"REGWATCH_CACHE_DIR": str(tmp_path)},
    )
    assert result.exit_code == 0
    assert "dora" in result.output
    assert "mica" not in result.output


def test_cli_status_with_data(tmp_path):
    """status command shows item counts by source and regulation."""
    _seed_cache(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["status"], env={"REGWATCH_CACHE_DIR": str(tmp_path)})
    assert result.exit_code == 0
    assert "2 items" in result.output
    assert "esma" in result.output
    assert "dora" in result.output


def test_cli_check_empty_table(tmp_path):
    """check with no results shows 'No regulatory changes found'."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["check", "--since", "2099-01-01"],
        env={"REGWATCH_CACHE_DIR": str(tmp_path)},
    )
    assert result.exit_code == 0
    assert "No regulatory changes found" in result.output
