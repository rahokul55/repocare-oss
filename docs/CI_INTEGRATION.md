# CI integration guide

RegressionProof has two integration modes:

1. **Report comparison:** Consume JUnit XML that a trusted CI job already generated. This does not execute the repository's code through RegressionProof.
2. **Worktree comparison:** Run the same test command against committed baseline and candidate snapshots, then compare outcomes. This executes the code under test and therefore needs an isolated, short-lived runner.

## Checklist for public repositories

- Use `pull_request` and `contents: read`, never `pull_request_target` for running untrusted contributions.
- Choose GitHub-hosted ephemeral runners or similarly disposable isolated workers.
- Do not attach production credentials, write-scoped tokens, or protected caches.
- Checkout full Git history (`fetch-depth: 0`) so both commit SHAs can be resolved.
- Install target project test dependencies in a controlled manner. RegressionProof will not install them.
- Pin external actions and the RegressionProof package to reviewed, immutable revisions before production use.
- Upload the report using an `if: always()` artifact step; a regression intentionally exits 1.

## GitHub job summary

The CLI exposes two opt-in switches:

```bash
regressionproof check --base "$BASE_SHA" --head HEAD \
  --runs 2 --test-command '{python} -m pytest -q --junitxml={report}' \
  --github-summary --github-output
```

`GITHUB_STEP_SUMMARY` receives the Markdown report. `GITHUB_OUTPUT` receives `status`, `regressions`, `new_failures`, and `unstable`, `quality`, `shared_tests`, `baseline_tests`, `candidate_tests`, and `overlap_percent`. The tool does not need GitHub API permissions. It also produces `report.html` for download as an artifact.

`--min-overlap 80` independently fails the comparison when fewer than 80% of
baseline test identities also appear in the candidate. This is not source-code
coverage; see [evidence quality](EVIDENCE_QUALITY.md). You may add
`--schedule interleaved` to alternate repeated test invocations.

`--fail-on unstable` is stricter than the default and can make a PR fail even when no new deterministic regression is observed. Use this only if incomplete/missing test observations should block your merge process.

## Interpreting results

- `regression`: One or more observed tests passed consistently before and failed consistently after, or a new test fails consistently.
- `unstable`: No deterministic new failures, but one or more test identities vary or are missing across observations.
- `no_new_failures`: Neither of those situations was observed. This **does not** prove correctness.

Test identity depends on the upstream JUnit generator. Compare the same test suite, with comparable dependencies and runtime settings, for meaningful results.

## Example workflow

See [`examples/github-actions.yml`](../examples/github-actions.yml). The installation step uses a placeholder SHA intentionally: first inspect and pin the version you intend to run. Avoid using `@main` in a security-sensitive workflow.
