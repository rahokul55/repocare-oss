# Roadmap

Items below are proposals, not shipped features. Scope will depend on community usage and compatibility reports.

## v0.1: local verification (implemented)

- [x] Compare two previously created JUnit reports
- [x] Compare Git revisions using detached worktrees
- [x] Repeat observations to detect inconsistent outcomes
- [x] JSON and Markdown output
- [x] Tests, package metadata, contribution and security policies

## v0.2: CI and reporting (implemented)

- [x] Multi-run report-only comparisons
- [x] Standalone HTML dashboard
- [x] Explicit CI failure policy and GitHub job summaries
- [x] Best-effort process group cleanup on timeout
- [x] CLI, HTML escaping and timeout integration tests

## v0.3: evidence continuity and PR verification (implemented)

- [x] Detect zero or partial test-identity overlap; report evidence quality warnings
- [x] Optional `--min-overlap` CI failure policy without changing defaults
- [x] Alternate repeated attempts for baseline and candidate
- [x] Self-test the regression engine on pull requests in a read-only GitHub Action
- [x] Add focused regression tests and documentation of the confidence model

## Near term

- [ ] Better per-test identity normalization across popular JUnit producers
- [ ] Explicit environment provisioning hooks with safe opt-in controls
- [ ] Self-contained GitHub Action with published immutable version
- [ ] Compatibility tests for pytest, Jest, Go and Maven reports
- [ ] CI-controlled log redaction and optional retention for troubleshooting
- [ ] Release artifacts and a reproducible packaging process

## Later (design needed)

- [ ] Read-only GitHub checks API integration, with maintainer review
- [ ] Baseline-aware flaky test history across CI runs
- [ ] Optional opt-in AI summaries from *redacted* test evidence
- [ ] Causal hypothesis assistance, clearly separated from test evidence
- [ ] Evaluate the tool on real open-source PRs; publish measured error rates

Features involving external APIs must be opt-in, auditable, and usable without the AI path.
