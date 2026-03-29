from datetime import date

from click.testing import CliRunner

from regwatch.cache import Cache
from regwatch.cli import cli
from regwatch.models import ClassifiedChange


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Monitor EU regulatory changes" in result.output


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_regulations():
    runner = CliRunner()
    result = runner.invoke(cli, ["regulations"])
    assert result.exit_code == 0
    assert "dora" in result.output


def test_cli_status_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["status"], env={"REGWATCH_CACHE_DIR": str(tmp_path)})
    assert result.exit_code == 0
    assert "0 items" in result.output


def test_cli_check_empty_json(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["check", "--format", "json"], env={"REGWATCH_CACHE_DIR": str(tmp_path)}
    )
    assert result.exit_code == 0


def test_cli_check_renders_unclassified_items(tmp_path):
    """Regression: CLI must handle NaN/None regulation without crashing."""
    cache = Cache(str(tmp_path / "cache.db"))
    cache.upsert([ClassifiedChange(
        id="test1", title="Generic news item", date=date(2026, 3, 15),
        url="http://example.com/1", source="esma",
        regulation=None,  # This becomes NaN in pandas
        type="legislative_act", urgency="medium", summary=None,
    )])
    cache.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--since", "2025-01-01"],
                           env={"REGWATCH_CACHE_DIR": str(tmp_path)})
    assert result.exit_code == 0
    assert "---" in result.output  # Should show "---" for unclassified
    assert "Generic news item" in result.output


def test_cli_check_invalid_date(tmp_path):
    """Regression: invalid date should show clean error, not traceback."""
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--since", "not-a-date"],
                           env={"REGWATCH_CACHE_DIR": str(tmp_path)})
    assert result.exit_code != 0
    assert "YYYY-MM-DD" in result.output or "Invalid" in result.output
