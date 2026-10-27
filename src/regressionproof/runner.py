"""Run a test command against detached Git worktrees.

This is a convenience isolation of *files*, not a security sandbox. Test code
runs with the permissions, network and secrets of the current process.
"""

from __future__ import annotations

import os
import signal
import shlex
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator

from .junit import JUnitError, parse_junit
from .model import Outcome, RevisionResult, TestRun


class RunnerError(RuntimeError):
    """Failed to prepare a repository or obtain a valid test result."""


def _git(repo: Path, *args: str) -> str:
    try:
        process = subprocess.run(
            ["git", "-C", str(repo), *args], check=True, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        raise RunnerError(f"Git command failed: git {' '.join(args)}: {exc}") from exc
    return process.stdout.strip()


def find_repository(path: Path) -> Path:
    top = _git(path, "rev-parse", "--show-toplevel")
    return Path(top).resolve()


def resolve_commit(repo: Path, ref: str) -> str:
    sha = _git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
    if len(sha) not in {40, 64} or any(char not in "0123456789abcdef" for char in sha):
        raise RunnerError(f"Ref did not resolve to a Git commit: {ref}")
    return sha


@contextmanager
def detached_worktree(repo: Path, sha: str, directory: Path) -> Iterator[Path]:
    # Worktree paths must not exist before `git worktree add`.
    _git(repo, "worktree", "add", "--detach", str(directory), sha)
    try:
        yield directory
    finally:
        # Best-effort Git metadata cleanup; TemporaryDirectory removes the tree.
        try:
            _git(repo, "worktree", "remove", "--force", str(directory))
        except RunnerError:
            _git(repo, "worktree", "prune")


def parse_command(template: str) -> tuple[str, ...]:
    if not template.strip():
        raise RunnerError("Test command cannot be empty")
    try:
        argv = shlex.split(template, posix=(os.name != "nt"))
    except ValueError as exc:
        raise RunnerError(f"Invalid test command: {exc}") from exc
    if not argv:
        raise RunnerError("Test command cannot be empty")
    if not any("{report}" in item for item in argv):
        raise RunnerError("Test command must include {report} for its JUnit XML output")
    return tuple(argv)


def _stop_process_tree(process: subprocess.Popen) -> None:
    """Best effort: terminate direct children and the process group on timeout."""
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                           capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _run_once(
    directory: Path, scratch: Path, template: tuple[str, ...], timeout: float
) -> TestRun:
    report = scratch / "junit.xml"
    argv = [item.replace("{python}", sys.executable).replace("{report}", str(report))
            for item in template]
    environment = os.environ.copy()
    src = directory / "src"
    paths = [str(directory)]
    if src.is_dir():
        paths.insert(0, str(src))
    if environment.get("PYTHONPATH"):
        paths.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    started = time.monotonic()
    scratch.mkdir(parents=True, exist_ok=True)
    output_path = scratch / "command.log"
    # A process group lets us terminate children started by the test command on
    # POSIX after a timeout or Ctrl-C. This is lifecycle management, not a sandbox.
    popen_options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
        else {"start_new_session": True}
    )
    with output_path.open("wb") as log:
        try:
            process = subprocess.Popen(argv, cwd=directory, env=environment, stdout=log,
                                       stderr=subprocess.STDOUT, **popen_options)
        except OSError as exc:
            raise RunnerError(f"Cannot start test command: {exc}") from exc
        try:
            return_code = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            _stop_process_tree(process)
            if isinstance(exc, KeyboardInterrupt):
                raise
            raise RunnerError(f"Test command timed out after {timeout:g} seconds") from exc
    elapsed = time.monotonic() - started
    try:
        parsed = parse_junit(report)
    except JUnitError as exc:
        tail = output_path.read_bytes()[-2000:].decode("utf-8", errors="replace")
        raise RunnerError(f"{exc}; command exit={return_code}; output tail:\n{tail}") from exc
    failures = [test for test in parsed.values()
                if test.outcome in {Outcome.FAILED, Outcome.ERROR}]
    if return_code != 0 and not failures:
        tail = output_path.read_bytes()[-2000:].decode("utf-8", errors="replace")
        raise RunnerError(
            f"Test command exit={return_code} but JUnit contains no failures; "
            f"possible execution error. Output tail:\n{tail}"
        )
    return TestRun(tests=parsed, exit_code=return_code, elapsed_seconds=elapsed)


def run_revision(
    ref: str,
    sha: str,
    worktree: Path,
    scratch: Path,
    argv: tuple[str, ...],
    runs: int,
    timeout: float,
) -> RevisionResult:
    results = tuple(_run_once(worktree, scratch / str(i + 1), argv, timeout)
                    for i in range(runs))
    return RevisionResult(ref=ref, sha=sha, runs=results)


def compare_in_worktrees(
    project: Path, base_ref: str, head_ref: str, test_command: str,
    runs: int, timeout: float,
):
    from .compare import compare_revisions

    if not 1 <= runs <= 10:
        raise RunnerError("--runs must be between 1 and 10")
    if not 1 <= timeout <= 3600:
        raise RunnerError("--timeout must be between 1 and 3600 seconds")
    repo = find_repository(project)
    before = resolve_commit(repo, base_ref)
    after = resolve_commit(repo, head_ref)
    template = parse_command(test_command)
    with tempfile.TemporaryDirectory(prefix="regressionproof-") as temporary:
        root = Path(temporary)
        with detached_worktree(repo, before, root / "base") as base_tree:
            baseline = run_revision(base_ref, before, base_tree, root / "logs-base",
                                    template, runs, timeout)
        with detached_worktree(repo, after, root / "head") as head_tree:
            candidate = run_revision(head_ref, after, head_tree, root / "logs-head",
                                     template, runs, timeout)
        return compare_revisions(baseline, candidate)
