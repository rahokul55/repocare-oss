"""Command-line entry point. Analysis remains local unless CI output is explicitly enabled."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .compare import compare_revisions
from .junit import JUnitError, parse_junit
from .model import Comparison, RevisionResult, TestRun
from .report import to_markdown, to_payload, write_report
from .runner import RunnerError, compare_in_worktrees

DEFAULT_COMMAND = "{python} -m pytest -q --junitxml={report}"


def _common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", type=Path, default=Path(".regressionproof"),
                        help="Directory for JSON, Markdown and HTML reports")
    parser.add_argument("--min-overlap", type=float, default=0.0,
                        help="Fail if less than this percentage of baseline test identities "
                             "appear in the candidate (0-100, default 0)")
    parser.add_argument("--fail-on", choices=("new", "unstable", "none"), default="new",
                        help="CI failure policy: new failures (default), also unstable, or never")
    parser.add_argument("--no-fail", action="store_true",
                        help="Backwards-compatible alias for --fail-on none")
    parser.add_argument("--github-summary", action="store_true",
                        help="Append Markdown report to GITHUB_STEP_SUMMARY when set")
    parser.add_argument("--github-output", action="store_true",
                        help="Append status and counts to GITHUB_OUTPUT when set")


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
                       help="No shell; must produce JUnit XML at {report}; {python} supported")
    check.add_argument("--runs", type=int, default=1, help="Repeat tests per revision (1-10)")
    check.add_argument("--schedule", choices=("grouped", "interleaved"),
                       default="grouped", help="Test each revision in blocks or alternate "
                                               "attempts between revisions")
    check.add_argument("--timeout", type=float, default=300,
                       help="Max seconds per invocation (1-3600)")
    _common_options(check)

    compare = sub.add_parser("compare", help="Compare existing JUnit XML reports")
    compare.add_argument("--base-xml", type=Path, action="append", required=True,
                         help="Baseline JUnit XML file (repeat for additional observations)")
    compare.add_argument("--head-xml", type=Path, action="append", required=True,
                         help="Candidate JUnit XML file (repeat for additional observations)")
    _common_options(compare)
    return parser


def _from_xml(base_files: list[Path], head_files: list[Path]) -> Comparison:
    def revision(ref: str, files: list[Path]) -> RevisionResult:
        if not 1 <= len(files) <= 10:
            raise ValueError("Provide between 1 and 10 XML reports per revision")
        runs = tuple(TestRun(parse_junit(path), 0, 0.0) for path in files)
        return RevisionResult(ref, "not-applicable", runs)

    return compare_revisions(revision("base.xml", base_files),
                             revision("head.xml", head_files))


def _github_append(variable: str, content: str) -> None:
    location = os.environ.get(variable)
    if not location:
        raise ValueError(f"{variable} is not set; this option requires GitHub Actions")
    with Path(location).open("a", encoding="utf-8", newline="\n") as output:
        output.write(content)


def _emit_github(comparison: Comparison, summary: bool, output: bool) -> None:
    if summary:
        _github_append("GITHUB_STEP_SUMMARY", to_markdown(comparison) + "\n")
    if output:
        result = to_payload(comparison)
        counts = result["counts"]
        lines = [f"status={result['status']}",
                 f"regressions={counts['regressions']}",
                 f"new_failures={counts['new_failures']}",
                 f"unstable={counts['flaky']}"]
        evidence = comparison.evidence
        lines.extend((f"quality={evidence.quality}",
                      f"shared_tests={evidence.shared_tests}",
                      f"baseline_tests={evidence.baseline_tests}",
                      f"candidate_tests={evidence.candidate_tests}",
                      f"overlap_percent={evidence.overlap_percent:.2f}"))
        _github_append("GITHUB_OUTPUT", "\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if not 0 <= args.min_overlap <= 100:
            raise ValueError("--min-overlap must be in the range 0..100")
        if args.mode == "check":
            comparison = compare_in_worktrees(args.project, args.base, args.head,
                                              args.test_command, args.runs, args.timeout,
                                              args.schedule)
        else:
            comparison = _from_xml(args.base_xml, args.head_xml)
        json_file, markdown_file = write_report(comparison, args.output.resolve())
        _emit_github(comparison, args.github_summary, args.github_output)
    except (RunnerError, JUnitError, OSError, ValueError) as exc:
        print(f"regressionproof: {exc}", file=sys.stderr)
        return 2
    print(f"Result: {'NEW FAILURES' if comparison.has_new_failure else 'NO NEW FAILURES'}")
    print(f"Regressions: {len(comparison.regressions)}; "
          f"new failing tests: {len(comparison.new_failures)}; "
          f"unstable/incomplete: {len(comparison.flaky)}")
    evidence = comparison.evidence
    print(f"Shared identities: {evidence.shared_tests}/{evidence.baseline_tests} "
          f"({evidence.overlap_percent:.2f}%); evidence: {evidence.quality}")
    for warning in evidence.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(f"Report: {markdown_file}")
    print(f"JSON:   {json_file}")
    print(f"HTML:   {markdown_file.with_suffix('.html')}")
    if evidence.overlap_percent < args.min_overlap:
        print(f"Baseline overlap {evidence.overlap_percent:.2f}% below "
              f"required {args.min_overlap:.2f}%", file=sys.stderr)
        return 1
    policy = "none" if args.no_fail else args.fail_on
    if comparison.has_new_failure and policy != "none":
        return 1
    if comparison.flaky and policy == "unstable":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
