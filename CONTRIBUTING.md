# Contributing

Thanks for taking the time to improve RegressionProof. Before opening a change, search existing issues for related discussion. For behaviour changes, include a real or minimal JUnit XML example demonstrating the current and expected output.

## Development setup

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check .
```

Run tests on Python 3.10+ and keep changes narrowly scoped. New classification rules need tests covering failure, skipped, absent, and inconsistent observations. Avoid modifications that execute arbitrary shell commands. If adjusting a security boundary, include an accompanying security-model update.

## Pull request checklist

- [ ] Add or update tests for user-visible behaviour.
- [ ] Update README and CHANGELOG where applicable.
- [ ] Keep CLI flags and JSON schema backward-compatible within 0.x where possible.
- [ ] State limitations rather than claiming false positives are impossible.

## Project decisions

Small PRs with a clear rationale are preferred. Changes that add dependencies, external network calls, privileged workflows or automated publishing should be discussed in an issue before implementation.

Please follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security issues should be disclosed privately as described in [SECURITY.md](SECURITY.md).
