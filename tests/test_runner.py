import subprocess

import pytest

from regressionproof.cli import main
from regressionproof.runner import RunnerError, compare_in_worktrees, parse_command


@pytest.fixture
def git_project(tmp_path):
    repo = tmp_path / "project"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                              text=True, check=True).stdout.strip()

    git("init", "-b", "main")
    git("config", "user.name", "Example Contributor")
    git("config", "user.email", "dev@example.test")
    script = '''from pathlib import Path
import sys
status = Path("state.txt").read_text().strip()
case = '<testcase classname="example" name="test_value">'
if status == "broken":
    case += '<failure message="unexpected value"/>'
case += '</testcase>'
Path(sys.argv[1]).write_text('<testsuite>' + case + '</testsuite>', encoding='utf-8')
sys.exit(1 if status == "broken" else 0)
'''
    (repo / "suite.py").write_text(script)
    (repo / "state.txt").write_text("ok")
    git("add", ".")
    git("commit", "-m", "baseline")
    base = git("rev-parse", "HEAD")
    (repo / "state.txt").write_text("broken")
    git("commit", "-am", "introduce regression")
    head = git("rev-parse", "HEAD")
    return repo, base, head, git


def test_integration_with_real_git_worktrees(git_project, tmp_path):
    repo, base, head, git = git_project
    old_worktrees = git("worktree", "list", "--porcelain")
    result = compare_in_worktrees(repo, base, head,
                                  "{python} suite.py {report}", runs=2, timeout=10)
    assert len(result.regressions) == 1
    assert result.regressions[0].key == "example::test_value"
    assert not result.new_failures
    assert git("worktree", "list", "--porcelain") == old_worktrees
    assert len(result.base.runs) == 2
    assert (repo / "state.txt").read_text() == "broken"
    assert main(["check", "--project", str(repo), "--base", base, "--head", head,
                 "--test-command", "{python} suite.py {report}",
                 "--output", str(tmp_path / "report")]) == 1
    assert (tmp_path / "report" / "result.json").exists()


def test_rejects_bad_commands_and_limits(git_project):
    repo, base, head, _ = git_project
    with pytest.raises(RunnerError, match="report"):
        parse_command("python -m pytest")
    with pytest.raises(RunnerError, match="runs"):
        compare_in_worktrees(repo, base, head, "{python} suite.py {report}", 0, 10)
    with pytest.raises(RunnerError, match="Git command"):
        compare_in_worktrees(repo, "does-not-exist", head,
                             "{python} suite.py {report}", 1, 10)


def test_compare_mode_cli(write_junit, tmp_path):
    before = write_junit('<testsuite><testcase name="x"/></testsuite>', "a.xml")
    after = write_junit('<testsuite><testcase name="x"><failure/></testcase></testsuite>',
                        "b.xml")
    assert main(["compare", "--base-xml", str(before), "--head-xml", str(after),
                 "--output", str(tmp_path / "result")]) == 1
    assert main(["compare", "--base-xml", str(before), "--head-xml", str(after),
                 "--no-fail", "--output", str(tmp_path / "result2")]) == 0
    assert main(["compare", "--base-xml", str(before),
                 "--head-xml", str(tmp_path / "missing")]) == 2
