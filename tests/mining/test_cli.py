"""CLI smoke tests for new commands."""

import pytest
import yaml
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from mining.cli import cmd_forbidden, cmd_audit, cmd_logic
from mining.config import MiningConfig


@pytest.fixture
def cli_config(tmp_mining_dir, config):
    """Config pointing to temp directories."""
    return config


class TestForbiddenSuggest:
    def test_empty_data_no_crash(self, cli_config, capsys):
        """forbidden suggest with no result files should not crash."""
        args = type("Args", (), {"forbidden_action": "suggest"})()
        with patch("mining.cli.MiningConfig", return_value=cli_config):
            cmd_forbidden(args)
        captured = capsys.readouterr()
        assert "No forbidden" in captured.out

    def test_list_empty(self, cli_config, capsys):
        """forbidden list with empty forbidden.yaml should show message."""
        args = type("Args", (), {"forbidden_action": "list"})()
        with patch("mining.cli.MiningConfig", return_value=cli_config):
            cmd_forbidden(args)
        captured = capsys.readouterr()
        assert "No forbidden" in captured.out


class TestAudit:
    def test_empty_directions_no_crash(self, cli_config, capsys):
        """audit with no direction files should not crash."""
        args = type("Args", (), {})()
        with patch("mining.cli.MiningConfig", return_value=cli_config):
            cmd_audit(args)
        captured = capsys.readouterr()
        assert "consistent" in captured.out or "0 mismatches" in captured.out or "Found" in captured.out


class TestLogicCreate:
    def test_empty_stdin_reports_error(self, cli_config, capsys):
        """logic create with empty stdin should report error."""
        args = type("Args", (), {"logic_action": "create", "status": None})()
        with patch("mining.cli.MiningConfig", return_value=cli_config), \
             patch("sys.stdin", StringIO("")), \
             pytest.raises(SystemExit) as exc:
            cmd_logic(args)
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "expected YAML dict" in captured.out

    def test_missing_fields_reports_error(self, cli_config, capsys):
        """logic create with missing fields should report error."""
        args = type("Args", (), {"logic_action": "create", "status": None})()
        yaml_input = yaml.dump({"name": "test"})  # missing category, hypothesis
        with patch("mining.cli.MiningConfig", return_value=cli_config), \
             patch("sys.stdin", StringIO(yaml_input)), \
             pytest.raises(SystemExit) as exc:
            cmd_logic(args)
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "missing required fields" in captured.out
