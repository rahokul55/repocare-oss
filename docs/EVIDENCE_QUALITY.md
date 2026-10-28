# Evidence quality and test identity overlap

RegressionProof measures **test identity overlap**, not line, branch, or statement coverage.
A matching test identity is the same `classname::name` in baseline and candidate
JUnit XML. Such a match does not prove that both revisions execute identical code.

## Why overlap matters

If a candidate renames or removes every baseline test and all remaining tests pass,
there is no confirmed new regression but there is also no evidence that the old test
suite still runs. Earlier versions could report `no_new_failures` without highlighting
this uncertainty.

Version 0.3.0 adds the **additive** `evidence` field in `result.json`:

```json
{
  "evidence": {
    "baseline_tests": 100,
    "candidate_tests": 95,
    "shared_tests": 90,
    "added_tests": 5,
    "removed_tests": 10,
    "overlap_percent": 90.0,
    "quality": "partial",
    "warnings": ["Some baseline test identities are absent from the candidate."]
  }
}
```

The `evidence` object is a sibling of existing keys. The report's `schema_version`
remains `1`, the original groups and status values are unchanged, and existing
consumers can ignore `evidence`.

Quality is a hint, not a probability or guarantee:

- `comparable`: at least one shared test, without known missing tests, unstable
  evidence, or consistently skipped candidate tests.
- `partial`: shared tests exist, but baseline tests have disappeared or observations
  are unstable/incomplete, or candidate tests are consistently skipped.
- `insufficient`: no shared test identities were observed.

Each revision's identity count is the **union** over its repeated test runs. When a
particular test is absent in only some runs, it is marked incomplete (in the `flaky`
category) and reduces confidence. A skipped test is not a successful test.

## Fail closed when test identity continuity matters

```bash
regressionproof check --base main --head HEAD --runs 2 \
  --schedule interleaved --min-overlap 85 \
  --test-command '{python} -m pytest -q --junitxml={report}'
```

The overlap percentage is `100 * shared_ids / baseline_ids`, rounded to two decimal
places for reporting. A specified `--min-overlap` threshold from `0` to `100`
returns exit code `1` when the observed value is lower; malformed thresholds return
`2`. The default threshold `0` preserves the existing CLI exit behavior. The
continuity guard is independent of `--fail-on` and `--no-fail`: an explicitly enabled
overlap requirement cannot be disabled by suppressing test failure exits.

Use an appropriate threshold rather than blindly setting 100: legitimate test
renames, suite splits, test-selection rules, and plugin JUnit naming differences can
lower the ratio. Inspect the `removed` and `added` groups and the report artifacts.

## Interleaved repeated observations

`--schedule interleaved` runs `base1, head1, base2, head2, ...` rather than
`base1, base2, ..., head1, head2, ...` (the old default `grouped`). This reduces
one source of time-dependent bias, but does not make observations statistically
independent or control random seeds, dependency drift, parallel jobs, machine load,
or external services. Only use it on trusted test code and a disposable runner.

`--github-output` additionally includes `quality`, `shared_tests`,
`baseline_tests`, `candidate_tests` and `overlap_percent`. No token or GitHub API
permission is required to generate these outputs.
