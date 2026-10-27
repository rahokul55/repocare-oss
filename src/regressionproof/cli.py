"""Command-line interface. No network calls or telemetry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .compare import compare_revisions
from .junit import JUnitError, parse_junit
from .model import RevisionResult, TestRun
from .report import write_report
from .runner import RunnerError, compare_in_worktrees

DEFAULT_COMMAND = "{python} -m pytest -q --junitxml={report}"


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="regressionproof", description="Compare test outcomes across Git revisions."
    )
    parser.add_argument("--version", action="version", version=f"regressionproof {__version__}")
    sub = parser.add_subparsers(dest="mode", required=True)
    check = sub.add_parser("check", help="Run tests in two temporary Git worktrees")
    check.add_argument("--base", default="main", help="Baseline Git ref (default: main)")
    check.add_argument("--head", default="HEAD", help="Candidate Git ref (default: HEAD)")
    check.add_argument("--project", type=Path, default=Path.cwd(), help="Path in Git repository")
    check.add_argument("--test-command", default=DEFAULT_COMMAND,
                       help="No shell; must output JUnit XML to {report}; {python} supported")
    check.add_argument("--runs", type=int, default=1, help="Repeat tests per revision (1-10)")
    check.add_argument("--timeout", type=float, default=300,
                       help="Max seconds for each invocation (1-3600)")
    check.add_argument("--output", type=Path, default=Path(".regressionproof"))
    check.add_argument("--no-fail", action="store_true", help="Report without exit code 1")
    compare = sub.add_parser("compare", help="Compare previously generated JUnit XML files")
    compare.add_argument("--base-xml", type=Path, required=True)
    compare.add_argument("--head-xml", type=Path, required=True)
    compare.add_argument("--output", type=Path, default=Path(".regressionproof"))
    compare.add_argument("--no-fail", action="store_true")
    return parser


def _from_xml(base: Path, head: Path):
    baseline = RevisionResult(
        "base.xml", "not-applicable", (TestRun(parse_junit(base), 0, 0.0),)
    )
    candidate = RevisionResult(
        "head.xml", "not-applicable", (TestRun(parse_junit(head), 0, 0.0),)
    )
    return compare_revisions(baseline, candidate)


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.mode == "check":
            comparison = compare_in_worktrees(args.project, args.base, args.head,
                                              args.test_command, args.runs, args.timeout)
        else:
            comparison = _from_xml(args.base_xml, args.head_xml)
        json_file, markdown_file = write_report(comparison, args.output.resolve())
    except (RunnerError, JUnitError, OSError, ValueError) as exc:
        print(f"regressionproof: {exc}", file=sys.stderr)
        return 2
    print(f"Result: {'NEW FAILURES' if comparison.has_new_failure else 'NO NEW FAILURES'}")
    print(f"Regressions: {len(comparison.regressions)}; "
          f"new failing tests: {len(comparison.new_failures)}; "
          f"unstable/incomplete: {len(comparison.flaky)}")
    print(f"Report: {markdown_file}")
    print(f"JSON:   {json_file}")
    if comparison.has_new_failure and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
