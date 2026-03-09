"""
test_cli.py
~~~~~~~~~~~
Integration tests for the :mod:`ipam_subnet_toolkit.cli` module.

Tests exercise the full argument-parsing and command-dispatch pipeline
without invoking a real subprocess, keeping the suite fast and dependency-free.
"""

import json
import pytest

from ipam_subnet_toolkit.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_main(argv: list[str]) -> int:
    """Invoke main() and capture the exit code via SystemExit."""
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    return exc_info.value.code


# ---------------------------------------------------------------------------
# ipam info
# ---------------------------------------------------------------------------


class TestCmdInfo:
    def test_table_output(self, capsys):
        code = run_main(["info", "192.168.1.0/24"])
        assert code == 0
        captured = capsys.readouterr()
        assert "192.168.1.0/24" in captured.out
        assert "255.255.255.0" in captured.out
        assert "192.168.1.1" in captured.out
        assert "192.168.1.254" in captured.out

    def test_json_output_flag(self, capsys):
        code = run_main(["info", "10.0.0.0/8", "--json"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["cidr"] == "10.0.0.0/8"
        assert data["prefix_length"] == 8
        assert data["usable_hosts"] == 2**24 - 2

    def test_non_network_input_is_normalized(self, capsys):
        code = run_main(["info", "192.168.1.50/24"])
        assert code == 0
        captured = capsys.readouterr()
        assert "192.168.1.0/24" in captured.out

    def test_invalid_cidr_returns_1(self, capsys):
        code = run_main(["info", "bad-input"])
        assert code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_slash32_host_route(self, capsys):
        code = run_main(["info", "10.1.2.3/32"])
        assert code == 0
        captured = capsys.readouterr()
        assert "10.1.2.3" in captured.out

    def test_slash31_point_to_point(self, capsys):
        code = run_main(["info", "10.0.0.0/31", "--json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["usable_hosts"] == 2

    def test_class_b_subnet(self, capsys):
        code = run_main(["info", "172.16.0.0/16", "--json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["ip_class"] == "B"
        assert data["is_private"] is True


# ---------------------------------------------------------------------------
# ipam contains
# ---------------------------------------------------------------------------


class TestCmdContains:
    def test_returns_exit_code_0_for_ip_in_subnet(self, capsys):
        code = run_main(["contains", "192.168.1.0/24", "192.168.1.100"])
        assert code == 0
        assert " is in " in capsys.readouterr().out

    def test_returns_exit_code_2_for_ip_outside_subnet(self, capsys):
        code = run_main(["contains", "192.168.1.0/24", "10.0.0.1"])
        assert code == 2
        assert " is NOT in " in capsys.readouterr().out

    def test_network_address_in_subnet(self, capsys):
        code = run_main(["contains", "10.0.0.0/8", "10.0.0.0"])
        assert code == 0

    def test_broadcast_in_subnet(self, capsys):
        code = run_main(["contains", "10.0.0.0/8", "10.255.255.255"])
        assert code == 0

    def test_returns_exit_code_1_for_invalid_cidr(self, capsys):
        code = run_main(["contains", "not-a-network", "10.0.0.1"])
        assert code == 1

    def test_class_a_ip_in_class_c_subnet_exit_2(self, capsys):
        code = run_main(["contains", "192.168.0.0/24", "10.0.0.1"])
        assert code == 2


# ---------------------------------------------------------------------------
# ipam export
# ---------------------------------------------------------------------------


class TestCmdExport:
    def test_writes_json_file(self, tmp_path, capsys):
        out_file = tmp_path / "output.json"
        code = run_main(["export", "192.168.1.0/24", "--output", str(out_file)])
        assert code == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["cidr"] == "192.168.1.0/24"
        assert data["usable_hosts"] == 254

    def test_default_filename(self, tmp_path, monkeypatch, capsys):
        # Change cwd so the default file lands in tmp_path
        monkeypatch.chdir(tmp_path)
        code = run_main(["export", "10.0.0.0/8"])
        assert code == 0
        default_file = tmp_path / "subnet_info.json"
        assert default_file.exists()
        data = json.loads(default_file.read_text())
        assert data["prefix_length"] == 8

    def test_export_slash30(self, tmp_path, capsys):
        out_file = tmp_path / "wan.json"
        run_main(["export", "10.1.1.0/30", "--output", str(out_file)])
        data = json.loads(out_file.read_text())
        assert data["usable_hosts"] == 2
        assert data["first_usable_host"] == "10.1.1.1"

    def test_returns_exit_code_1_for_invalid_cidr(self, capsys, tmp_path):
        out_file = tmp_path / "output.json"
        code = run_main(["export", "999.999.999.999/99", "--output", str(out_file)])
        assert code == 1
        assert not out_file.exists()

    def test_short_output_flag_writes_json(self, tmp_path, capsys):
        out_file = tmp_path / "out.json"
        code = run_main(["export", "172.16.0.0/12", "-o", str(out_file)])
        assert code == 0
        data = json.loads(out_file.read_text())
        assert data["is_private"] is True


# ---------------------------------------------------------------------------
# Parser / help
# ---------------------------------------------------------------------------


class TestParser:
    def test_no_subcommand_exits_0(self):
        code = run_main([])
        assert code == 0

    def test_version_flag(self):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0

    def test_info_help_exits_0(self):
        with pytest.raises(SystemExit) as exc:
            main(["info", "--help"])
        assert exc.value.code == 0

    def test_contains_help_exits_0(self):
        with pytest.raises(SystemExit) as exc:
            main(["contains", "--help"])
        assert exc.value.code == 0

    def test_export_help_exits_0(self):
        with pytest.raises(SystemExit) as exc:
            main(["export", "--help"])
        assert exc.value.code == 0
