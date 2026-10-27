# Maintainer release checklist

This is a checklist, not a record of tasks already completed.

## Before publishing source

- [ ] Review generated code and documentation for secrets and private data.
- [ ] Verify dependencies and licensed files.
- [ ] Test Windows install and PowerShell publish instructions on an actual Windows machine.
- [ ] Run `python -m pytest -q` on supported Python versions.
- [ ] Run `ruff check .` and resolve all reported findings.
- [ ] Verify example JUnit outputs produce the documented classification.
- [ ] Publish the repo under the intended GitHub account and enable Actions.
- [ ] Verify CI actually passes on GitHub-hosted runners.

## Before creating a release

- [ ] Review merged changes and update `CHANGELOG.md`.
- [ ] Check CLI exit-code semantics and `schema_version` compatibility.
- [ ] Test offline install from the wheel artifact.
- [ ] Pin and review third-party GitHub Actions to immutable commits.
- [ ] Configure GitHub branch protection and private vulnerability reporting.
- [ ] Create signed or reviewed version tag (e.g. `v0.1.0`) only after checks pass.
- [ ] Publish release notes with known limitations; do not imply broad adoption.

## Evaluation goals

- Test against public Git repositories with owners' permission and publish reproducible cases.
- Track number and type of true regressions, inconclusive outcomes and false positives.
- Accept outside contributions and improve producer compatibility based on real issues.
