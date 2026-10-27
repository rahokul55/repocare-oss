# Changelog

Notable changes to RegressionProof. Versions follow semantic versioning for the CLI, while the project remains alpha.

## 0.2.0 — 2026-10-27

### Added

- Offline standalone HTML report with escaped test identifiers and a restrictive content security policy.
- Multiple `--base-xml` and `--head-xml` observations for flaky/incomplete test detection without executing test code.
- Configurable `--fail-on new|unstable|none` CI failure policy; `--no-fail` remains supported.
- Opt-in GitHub Actions Markdown step summaries and machine-readable outputs.
- Best-effort process-group termination on test timeout or interruption.
- End-to-end CLI tests and HTML rendering safety coverage.
- CI integration guidance for public GitHub repositories.

### Compatibility

- Python 3.10+; zero runtime third-party dependencies.
- JSON report schema stays at version 1. Previous `check`, `compare` and `--no-fail` commands continue working.
- `write_report()` returns the same two paths and also writes `report.html`.

## 0.1.0 — 2026-10-27

Initial Python CLI: detached worktree testing, deterministic JUnit test result comparison, Markdown and JSON reports, community documents and CI test matrix.
