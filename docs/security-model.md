# Threat model and security boundaries

## What is trusted

The user trusts the invoking Python process and chooses both the Git repository and the test command. The CLI makes no outbound requests and has no credential management. The repository's test code, its build hooks, its dependencies, and external services may be untrusted.

## Risks

1. Test code runs with the invoking account's filesystem, network access, and environment variables. A temporary worktree does not contain a malicious test process.
2. Secrets in environment variables can be exfiltrated by tests; do not expose them to fork PR workflows.
3. GitHub `pull_request_target` and privileged `workflow_run` can combine untrusted code with write-scoped tokens. The provided workflow deliberately uses `pull_request` with read-only permissions.
4. XML files and command output can be malicious or huge. We cap XML size to 16 MiB; this is not a complete resource isolation mechanism.
5. JUnit test names and result text may contain untrusted material. Markdown names are escaped and full command logs are stored only in a temporary directory, then removed. Reports still reveal test names.
6. Timeout and interruption handling attempt to terminate a process group (POSIX) or process tree (Windows). Detached processes, services, and noncooperating child trees may still outlive the tool. This is best-effort cleanup, not isolation.

## Safe setup for public repositories

Use GitHub-hosted ephemeral runners (or a vetted disposable VM/container), avoid production credentials, grant `contents: read`, do not use write permissions or caches shared with privileged workflows, and configure network egress controls where possible. In production, pin third-party actions and dependencies to immutable, reviewed versions.

Do not run this tool directly against untrusted code on an administrator workstation. CI enforcement should include normal unit/integration tests; RegressionProof is additional diagnostic evidence, not a security scan.

## Non-goals in 0.1

No secrets scanning, Docker isolation, package installation, artifact provenance, or automatic PR commenting is currently provided. Those would require design review and security testing before adding them.

## HTML report security

The HTML report is offline: no scripts, external stylesheets or network resources. All test names and Git refs are HTML-escaped. The document includes a restrictive Content Security Policy. Treat it as test-generated diagnostic data, not authenticated evidence.
