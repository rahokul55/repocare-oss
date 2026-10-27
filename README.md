# RegressionProof

[Source repository](https://github.com/rahokul55/repocare-oss) · [Issues](https://github.com/rahokul55/repocare-oss/issues)

**Find introduced test failures without mistaking old failures for new ones.**

RegressionProof is a small, open-source CLI that compares JUnit XML results for two Git revisions. It can execute a test command in a temporary worktree for each revision or compare existing XML reports without executing code. It reports introduced regressions, tests added in a failing state, pre-existing failures, fixes, and tests with inconsistent observations.

**Status:** `0.1.0` (alpha). The core CLI is implemented and tested. No hosted service, GitHub App, AI feature, or registry publication is available yet.

## Why this exists

A red CI run doesn't always mean a pull request introduced the failing test. The same suite may have failed on the base commit, the new change may fix an existing issue, or the outcome may vary between runs. RegressionProof compares what was actually observed on each revision and avoids calling an absent or skipped test a confirmed pass.

RegressionProof does **not** tell you which commit caused a failure, replace your CI system, or prove the code is safe.

## Requirements

- Python 3.10+ and Git installed.
- A project whose test command can produce JUnit XML, such as pytest.
- A **trusted local environment or an isolated, ephemeral CI runner**. Git worktrees are not security sandboxes.

No runtime Python dependencies or accounts are required.

## Installation

Until a package is published to a registry, install from a local checkout:

```bash
python -m pip install -e .
regressionproof --version
```

For development:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## First run: no code execution

The repository includes example XML reports. Run this from its root:

```bash
regressionproof compare --base-xml examples/base.xml --head-xml examples/head.xml
```

See `.regressionproof/report.md` for a human-readable summary and `.regressionproof/result.json` for a stable, versioned JSON contract. A generated example is saved at [examples/sample-report.md](examples/sample-report.md).

## Run a test suite on two revisions

In your **target project's** Git working directory:

```bash
regressionproof check --base main --head HEAD \
  --test-command "{python} -m pytest -q --junitxml={report}" \
  --runs 2 \
  --output .regressionproof
```

On Windows PowerShell, place the entire command on one line, or use PowerShell's backtick continuation character instead of `\\`.

The placeholders have the following meaning:

- `{python}`: interpreter running RegressionProof.
- `{report}`: absolute location for that invocation's JUnit XML report.

The command is split into arguments and executed **without a shell**. Do not use pipes, redirects, or `&&`. Your test dependencies must already be available to the selected Python interpreter; if they differ between revisions, provision compatible environments outside this tool. The tool does not automatically run `pip install` against untrusted branches.

RegressionProof resolves the base and head refs to commits, creates two detached worktrees **sequentially**, runs the command in each, compares outcomes, writes the reports, and removes the temporary directories. Uncommitted local changes are **not** included in either revision.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | No new confirmed failures found (other unstable tests may still exist) |
| `1` | Introduced regression or newly added failing test found |
| `2` | Invalid configuration, test invocation, Git operation, or XML report |

Use `--no-fail` to generate reports without failing a CI job. You can use `--timeout 600` for large test suites (maximum 3,600 seconds per invocation). Set `--runs 3` to look for result instability; **one run cannot detect flakiness**.

## Classification

| Before | After | Classification |
| --- | --- | --- |
| Consistently passed | Consistently failed/error | Introduced regression |
| Not present | Consistently failed/error | New failing test |
| Consistently failed/error | Consistently failed/error | Pre-existing failure |
| Consistently failed/error | Consistently passed | Fixed failure |
| Any variation across runs, or missing in one of several runs | Any | Unstable/incomplete |
| Not present | Consistently passed/skipped | Added test |
| Present | Not present | Removed test |
| Skipped | Failed | Unconfirmed (not a proven regression) |

`failed` and `error` are treated as failures when assessing consistency. Test identity uses `classname::name` from JUnit XML. Duplicate identities fail validation rather than silently merging unrelated tests. Different test parameterizations should use unique names.

## CI integration

- See [the example GitHub workflow](examples/github-actions.yml).
- The repository's own quality gate is in [.github/workflows/ci.yml](.github/workflows/ci.yml).
- The example uses a read-only `pull_request` workflow, not `pull_request_target`.
- The example currently references a local development installation path; replace it with a pinned, published source revision before using it in another repository. **A GitHub App and automated PR commenting are not implemented.**

## Security boundary

**Running tests executes the code under test.** A detached Git worktree separates source files, not processes, network access, permissions, secrets, or the filesystem. Never run untrusted PR test code on a privileged machine, with deployment credentials, or in a `pull_request_target` workflow. Use isolated short-lived runners and grant `contents: read` only. See [SECURITY.md](SECURITY.md) and [docs/security-model.md](docs/security-model.md).

## Scope and limitations

- Python CLI; any language is usable if its tests emit compatible JUnit XML.
- Test dependencies are not automatically installed for each revision.
- Memory usage depends on the number of XML testcases and output; XML files are limited to 16 MiB.
- An execution timeout applies to the invoked process. This is not a full process-tree sandbox.
- Comparison assumes test identities and environment are comparable across revisions.
- Multi-run comparisons detect inconsistency but cannot determine statistical flake probability.
- All output is local; there are no API calls or telemetry.
- JUnit XML report inconsistencies are treated conservatively; an invalid or missing report fails with code 2.

## Project

Read [the architecture notes](docs/architecture.md) before changing the comparison rules. Refer to [CONTRIBUTING.md](CONTRIBUTING.md) for local testing and contribution expectations. Planned work is in [ROADMAP.md](ROADMAP.md); proposals and bug reports are welcome through GitHub Issues after repository publication.

MIT licensed. Maintained as an early-stage community project; no adoption or production reliability claims are made.
