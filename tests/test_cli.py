from click.testing import CliRunner

from regwatch.cli import cli


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
