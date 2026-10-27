# Security policy

## Supported versions

This is an early-stage project. Only the latest source version receives maintenance on a best-effort basis; no fixed patch window is promised.

## Reporting vulnerabilities

**Do not open a public issue containing a working exploit or credentials.** After the GitHub repository is published, use its private vulnerability reporting feature (Repository Settings → Security → Private vulnerability reporting), if enabled. If it is not enabled, request a private reporting channel in a non-sensitive issue without posting exploit details.

## Trust model

RegressionProof runs user-specified test executables against Git revisions. **These programs execute arbitrary code with the invoking process's permissions.** The tool does not sandbox processes, manage credentials, or restrict network access.

- Run third-party PR tests only on fresh ephemeral CI workers with no secrets or deployment tokens.
- Never use `pull_request_target` to execute head revision code.
- Grant GitHub Actions the minimum permissions (`contents: read`).
- Treat untrusted JUnit XML as data; reports use escaped Markdown for untrusted test names.
- Ignore generated output directories in version control and review reports before publishing; test failure text may contain sensitive information.
- Do not rely on worktree separation as a security boundary.

See [docs/security-model.md](docs/security-model.md) for more detail.
