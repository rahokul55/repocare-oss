# RegressionProof

**Know whether a failing test is new, old, or unstable — before merging a pull request.**

RegressionProof is a dependency-free Python CLI for comparing JUnit test evidence across Git revisions. It runs your existing test command in temporary detached worktrees or compares reports produced elsewhere. It does not modify the working tree, install dependencies behind your back, or send source code to a service.

**Release:** `0.2.0` (alpha) · **License:** MIT · **Runtime:** Python 3.10+ and Git for `check` mode · **Cost:** Free; no API keys.

## What it tells you

- **Introduced regressions:** Tests consistently passing on the baseline and consistently failing on the candidate.
- **New failing tests:** A test did not exist on the baseline and consistently fails on the candidate.
- **Pre-existing failures:** Consistently failing on both revisions, independent of whether its result is an assertion failure or an error.
- **Fixed failures:** Failing on the baseline, consistently passing on the candidate.
- **Unstable or incomplete:** Results change across observations, or the test is missing from some runs.
- **Added, removed and other:** Separate groups; skipped tests are not mistaken for passing tests.

A single test run **cannot** establish that a test is not flaky. Classification is based on available observations, not statistical proof or the identity of a causal commit.

## Quick start

Clone the source and install it locally:

```bash
python -m pip install -e .
regressionproof --version
regressionproof compare --base-xml examples/base.xml --head-xml examples/head.xml
```

The last command produces `.regressionproof/result.json`, `.regressionproof/report.md` and `.regressionproof/report.html`. Open the HTML report in any browser: it is self-contained, has no scripts, and makes no network requests.

For a real Git project whose tests produce JUnit XML:

```bash
regressionproof check --base main --head HEAD \
  --test-command '{python} -m pytest -q --junitxml={report}' \
  --runs 3 --timeout 300 --output .regressionproof
```

On PowerShell use a single command line or PowerShell backtick continuation, and double quotes around the test command. Required placeholders: `{report}` (JUnit XML output path), optional `{python}` (the Python interpreter running RegressionProof). The command is parsed into arguments, not executed through a shell. Do not include pipes, redirects, or `&&`.

**Your test dependencies must already be installed** in the invoking environment. Tests are run against committed snapshots; uncommitted edits are ignored. A Git worktree is not a security sandbox.

## Analyze repeated JUnit evidence without executing test code

Repeat `--base-xml` or `--head-xml` to include up to 10 observations per revision:

```bash
regressionproof compare \
  --base-xml base-run-1.xml --base-xml base-run-2.xml \
  --head-xml head-run-1.xml --head-xml head-run-2.xml \
  --fail-on unstable
```

This is useful when other CI pipelines already collect tests and when comparing test suites written in JavaScript, Go, Java, Python, etc. The JUnit producer must emit stable `classname::name` identities.

### CI exit policy

| Option | Exit code 1 when... |
| --- | --- |
| `--fail-on new` (default) | An introduced or newly added failing test is found |
| `--fail-on unstable` | Any new failure **or** unstable/incomplete observation is found |
| `--fail-on none` / `--no-fail` | Never (analysis errors can still return 2) |

Exit code `0` means no failure under the chosen policy; code `2` means the tool could not trust the configuration, Git state, command, or XML input. **A green result is not evidence that all tests passed.**

### GitHub Actions integration

Opt into a Markdown job summary and machine-readable step outputs:

```bash
regressionproof check --base "$BASE_SHA" --head HEAD \
  --test-command '{python} -m pytest -q --junitxml={report}' \
  --runs 2 --github-summary --github-output
```

When running inside GitHub Actions, `--github-summary` appends to `GITHUB_STEP_SUMMARY` and `--github-output` appends `status`, `regressions`, `new_failures`, and `unstable` to `GITHUB_OUTPUT`. These flags explicitly require those environment variables; they do not post PR comments or need write-scoped tokens. See [CI integration guide](docs/CI_INTEGRATION.md) and the [example workflow](examples/github-actions.yml).

## Reports

- `result.json`: stable machine-readable **schema version 1**, group counts and per-test classifications.
- `report.md`: compact table format suitable for code review, limited to the first 100 entries in each group.
- `report.html`: standalone dark-themed dashboard with collapsible groups, HTML-escaped test identities and a restrictive CSP, up to 1,000 entries per group. Full results remain in JSON.

JSON schema version 1 is unchanged from 0.1.0. `write_report()` still returns its existing `(json_path, markdown_path)` tuple for API compatibility.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
ruff check .
```

The repository has real Git integration tests, JUnit parser tests, output escaping tests, timeout cleanup tests and CLI compatibility tests. Browse [architecture](docs/architecture.md), [contribution guide](CONTRIBUTING.md), [security boundaries](SECURITY.md), [changelog](CHANGELOG.md) and [roadmap](ROADMAP.md).

## Safety and scope

Tests execute **repository code** with the privileges and environment of the invoking process. Use disposable, unprivileged CI runners for unknown contributions. Detached worktrees separate files, not privileges, network or secrets. On timeout the tool attempts to stop the process group; this is not a complete process isolation guarantee. Do not use `pull_request_target` to run untrusted PR code or pass elevated credentials into tests.

No AI integration, browser server, GitHub App, PyPI release, telemetry, causal inference, or adoption claims are included in this release. The program is an additional diagnostic tool, **not** a replacement for the project's standard CI and security checks.
