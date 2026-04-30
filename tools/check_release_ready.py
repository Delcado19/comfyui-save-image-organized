from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = Path(r"H:\ComfyUI-Easy-Install\python_embeded\python.exe")


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str


def _short_output(text: str, *, limit: int = 600) -> str:
    compact = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 4] + " ..."


def run_command(command: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def command_result(name: str, command: list[str], *, timeout: int = 120) -> CheckResult:
    try:
        completed = run_command(command, timeout=timeout)
    except FileNotFoundError:
        return CheckResult(name, False, f"command not found: {command[0]}")
    except subprocess.TimeoutExpired:
        return CheckResult(name, False, f"timed out after {timeout}s")

    output = _short_output(completed.stdout) or _short_output(completed.stderr)
    if completed.returncode == 0:
        return CheckResult(name, True, output or "ok")
    return CheckResult(name, False, output or f"exit code {completed.returncode}")


def check_clean_worktree() -> CheckResult:
    completed = run_command(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    if completed.returncode != 0:
        return CheckResult("git status", False, _short_output(completed.stderr))
    if completed.stdout.strip():
        return CheckResult("git status", False, "working tree has local changes")
    return CheckResult("git status", True, "working tree clean")


def check_branch_tracking() -> CheckResult:
    completed = run_command(["git", "status", "--short", "--branch"])
    if completed.returncode != 0:
        return CheckResult("branch tracking", False, _short_output(completed.stderr))
    line = completed.stdout.splitlines()[0] if completed.stdout else ""
    if "ahead" in line or "behind" in line or "gone" in line:
        return CheckResult("branch tracking", False, line)
    return CheckResult("branch tracking", True, line or "ok")


def check_local_tag(tag: str) -> CheckResult:
    completed = run_command(["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"])
    if completed.returncode != 0:
        return CheckResult("local tag", False, f"missing local tag: {tag}")

    head = run_command(["git", "rev-parse", "HEAD"])
    if head.returncode != 0:
        return CheckResult("local tag", False, _short_output(head.stderr))

    tag_sha = completed.stdout.strip()
    head_sha = head.stdout.strip()
    if tag_sha != head_sha:
        return CheckResult("local tag", False, f"{tag} points at {tag_sha[:7]}, HEAD is {head_sha[:7]}")
    return CheckResult("local tag", True, f"{tag} -> HEAD")


def check_remote_tag(tag: str) -> CheckResult:
    completed = run_command(["git", "ls-remote", "--tags", "origin", tag])
    if completed.returncode != 0:
        return CheckResult("remote tag", False, _short_output(completed.stderr))
    if completed.stdout.strip():
        return CheckResult("remote tag", True, tag)
    return CheckResult("remote tag", False, f"missing origin tag: {tag}")


def check_github_release(tag: str) -> CheckResult:
    if not shutil.which("gh"):
        return CheckResult("GitHub release", False, "gh not found")
    completed = run_command(
        [
            "gh",
            "release",
            "view",
            tag,
            "--json",
            "tagName,name,isDraft,isPrerelease,url",
        ]
    )
    if completed.returncode != 0:
        return CheckResult("GitHub release", False, _short_output(completed.stderr))

    data = json.loads(completed.stdout)
    if data.get("isDraft") or data.get("isPrerelease"):
        return CheckResult("GitHub release", False, f"not final: {data}")
    return CheckResult("GitHub release", True, data.get("url", tag))


def check_github_actions() -> CheckResult:
    if not shutil.which("gh"):
        return CheckResult("GitHub Actions", False, "gh not found")
    completed = run_command(
        [
            "gh",
            "run",
            "list",
            "--branch",
            "main",
            "--limit",
            "1",
            "--json",
            "status,conclusion,headSha,displayTitle,url",
        ]
    )
    if completed.returncode != 0:
        return CheckResult("GitHub Actions", False, _short_output(completed.stderr))

    runs = json.loads(completed.stdout)
    if not runs:
        return CheckResult("GitHub Actions", False, "no workflow runs found")
    run = runs[0]
    if run.get("status") == "completed" and run.get("conclusion") == "success":
        return CheckResult("GitHub Actions", True, f"{run.get('displayTitle')} {run.get('url')}")
    return CheckResult("GitHub Actions", False, f"{run.get('status')} {run.get('conclusion')}")


def build_checks(args: argparse.Namespace) -> list[CheckResult]:
    python = str(args.python)
    checks = []
    if not args.allow_dirty:
        checks.append(check_clean_worktree())

    checks.extend(
        [
            check_branch_tracking(),
            command_result("pytest", [python, "-m", "pytest", "-q"]),
        ]
    )
    checks.extend(
        [
            command_result("ruff", [python, "-m", "ruff", "check", "."]),
            command_result(
                "py_compile",
                [
                    python,
                    "-m",
                    "py_compile",
                    "nodes.py",
                    "tools/validate_local_workflows.py",
                    "tools/check_release_ready.py",
                ],
            ),
            command_result("node syntax", ["node", "--check", "web/save_image_clean.js"], timeout=30),
        ]
    )

    if args.workflows:
        workflow_command = [python, "tools/validate_local_workflows.py"]
        if args.workflow_limit is not None:
            workflow_command.extend(["--limit", str(args.workflow_limit)])
        if args.fail_on_detection_miss:
            workflow_command.append("--fail-on-miss")
        checks.append(command_result("workflow validator", workflow_command))

    if args.tag:
        checks.append(check_local_tag(args.tag))
        if args.github:
            checks.extend(
                [
                    check_remote_tag(args.tag),
                    check_github_release(args.tag),
                    check_github_actions(),
                ]
            )

    return checks


def print_results(checks: list[CheckResult]) -> None:
    for check in checks:
        marker = "OK" if check.ok else "FAIL"
        print(f"[{marker}] {check.name}: {check.details}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local and optional GitHub release-readiness checks.")
    parser.add_argument("--tag", help="Release tag to verify, for example v0.3.1.")
    parser.add_argument("--github", action="store_true", help="Also verify origin tag, GitHub release, and Actions.")
    parser.add_argument(
        "--workflows",
        action="store_true",
        help="Run the local workflow detection validator.",
    )
    parser.add_argument("--workflow-limit", type=int, default=12, help="Limit workflow validator rows.")
    parser.add_argument(
        "--fail-on-detection-miss",
        action="store_true",
        help="Make workflow validation fail on PARTIAL or MISS rows.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Skip the clean-worktree check. Use only while developing the checker itself.",
    )
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON, help="Python executable to use.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = build_checks(args)
    print_results(checks)
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
