# Architecture

RegressionProof is intentionally a CLI package with no daemon or server.

```text
CLI input
  ├── compare: JUnit XML (base, head)
  └── check: Git refs → resolve SHA → detached worktree → test command → JUnit XML
                               ↓
                         strict XML reader
                               ↓
                      repeated outcomes by ID
                               ↓
                     conservative comparison
                               ↓
                     JSON v1 + Markdown + offline HTML + CI outputs + exit
```

## Modules

- `junit.py`: validates and parses JUnit XML, enforces unique testcase identities.
- `runner.py`: resolves Git refs, creates and removes temporary worktrees, executes a command without shell interpretation, handles timeouts and report failures.
- `compare.py`: pure comparison logic: no I/O, no Git, and no network access.
- `report.py`: serializes a stable JSON schema, Markdown summary and self-contained HTML report.
- `cli.py`: validates arguments, selects execution modes, assigns exit codes.

## Failure classification

A definite introduced regression means `passed` on every base run and `failed` or `error` on every head run. An absent base test that fails in the head is **a new failing test**, not an introduced regression to an existing test. `failed` and `error` both count as failures; variation between success, failure and skip is reported as unstable. A missing testcase in just one of several reports means incomplete observation, not a pass.

Classification deliberately prefers "uncertain" over a false guarantee. The `other` group includes all unchanged tests and cases such as skipped → failed. Consumers should use `status`, not try to infer safety from an empty regression list.

## Known engineering tradeoffs

- Identity is based on the JUnit producer's `classname` and `name` fields; rewriting either can appear as removal/addition.
- Results do not attribute causality. Differences might be caused by external services, environment or timing rather than the change itself.
- Tests execute with the caller's Python environment, not separate dependency environments for each revision.
- `git worktree` provides detached copies, not container, network or system call isolation.
- Comparison loads a maximum of 16 MiB JUnit XML per invocation. Report outputs are deterministic except timestamps and input Git refs.
- A report written by a failing command must contain at least one failure/error testcase; otherwise exit code 2 is returned.

## JSON schema

`schema_version: 1` is the contract discriminator. Arrays for `regressions`, `new_failures`, `existing_failures`, `fixed`, `flaky`, `added`, `removed`, and `other` contain `{ key, base, head }` objects. The string `status` is `regression`, `unstable`, or `no_new_failures`. Backwards-compatible fields can be added within schema 1; breaking semantics require a new schema version.
