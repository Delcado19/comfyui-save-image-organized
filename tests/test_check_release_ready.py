from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from tools import check_release_ready


def test_short_output_compacts_and_truncates():
    text = "first line\n\nsecond line\n" + "x" * 700

    output = check_release_ready._short_output(text, limit=40)

    assert output == "first line second line xxxxxxxxxxxxx ..."


def test_command_result_reports_success(monkeypatch):
    def fake_run_command(command, *, timeout=120):
        assert command == ["tool", "arg"]
        assert timeout == 30
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(check_release_ready, "run_command", fake_run_command)

    result = check_release_ready.command_result("sample", ["tool", "arg"], timeout=30)

    assert result.ok is True
    assert result.details == "ok"


def test_command_result_reports_failure(monkeypatch):
    def fake_run_command(command, *, timeout=120):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="bad\n")

    monkeypatch.setattr(check_release_ready, "run_command", fake_run_command)

    result = check_release_ready.command_result("sample", ["tool"])

    assert result.ok is False
    assert result.details == "bad"


def test_clean_worktree_detects_local_changes(monkeypatch):
    def fake_run_command(command, *, timeout=120):
        assert command == ["git", "status", "--porcelain=v1", "--untracked-files=all"]
        return subprocess.CompletedProcess(command, 0, stdout=" M README.md\n", stderr="")

    monkeypatch.setattr(check_release_ready, "run_command", fake_run_command)

    result = check_release_ready.check_clean_worktree()

    assert result.ok is False
    assert result.details == "working tree has local changes"


def test_local_tag_must_point_to_head(monkeypatch):
    def fake_run_command(command, *, timeout=120):
        if command == ["git", "rev-parse", "--verify", "--quiet", "refs/tags/v1.0.0"]:
            return subprocess.CompletedProcess(command, 0, stdout="abc123\n", stderr="")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, stdout="def456\n", stderr="")
        raise AssertionError(command)

    monkeypatch.setattr(check_release_ready, "run_command", fake_run_command)

    result = check_release_ready.check_local_tag("v1.0.0")

    assert result.ok is False
    assert result.details == "v1.0.0 points at abc123, HEAD is def456"


def test_github_release_rejects_drafts(monkeypatch):
    def fake_which(command):
        assert command == "gh"
        return "gh"

    def fake_run_command(command, *, timeout=120):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"tagName":"v1.0.0","name":"v1.0.0","isDraft":true,"isPrerelease":false}',
            stderr="",
        )

    monkeypatch.setattr(check_release_ready.shutil, "which", fake_which)
    monkeypatch.setattr(check_release_ready, "run_command", fake_run_command)

    result = check_release_ready.check_github_release("v1.0.0")

    assert result.ok is False
    assert "not final" in result.details


def test_build_checks_can_fail_only_on_unresolved_detection(monkeypatch):
    workflow_commands = []

    monkeypatch.setattr(
        check_release_ready,
        "check_branch_tracking",
        lambda: check_release_ready.CheckResult("branch tracking", True, "ok"),
    )

    def fake_command_result(name, command, *, timeout=120):
        if name == "workflow validator":
            workflow_commands.append(command)
        return check_release_ready.CheckResult(name, True, "ok")

    monkeypatch.setattr(check_release_ready, "command_result", fake_command_result)

    args = argparse.Namespace(
        allow_dirty=True,
        fail_on_detection_miss=False,
        fail_on_unresolved_detection=True,
        github=False,
        python=Path("python"),
        tag=None,
        workflow_limit=12,
        workflows=True,
    )

    checks = check_release_ready.build_checks(args)

    assert all(check.ok for check in checks)
    assert workflow_commands == [
        ["python", "tools/validate_local_workflows.py", "--limit", "12", "--fail-on-unresolved"]
    ]
