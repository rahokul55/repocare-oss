# Creates a LOCAL commit and pushes to a GitHub repository you have already created.
# The script never changes an existing remote branch without a normal fast-forward.
param(
    [string]$RepoUrl = "https://github.com/rahokul55/repocare-oss.git"
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
if (-not (Test-Path 'pyproject.toml')) { throw 'Run inside the RegressionProof project folder.' }
if (-not (Test-Path '.git')) {
    git init
    if ($LASTEXITCODE -ne 0) { throw 'Git init failed.' }
}
git branch -M main
if ($LASTEXITCODE -ne 0) { throw 'Could not select main branch.' }
$remotes = @(git remote)
if ($remotes -notcontains 'origin') {
    git remote add origin $RepoUrl
    if ($LASTEXITCODE -ne 0) { throw 'Could not add origin.' }
} elseif ((git remote get-url origin) -ne $RepoUrl) {
    throw 'Existing origin URL differs. Check git remote -v before proceeding.'
}
git add .
if ($LASTEXITCODE -ne 0) { throw 'Git add failed.' }
git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    git commit -m 'Initial RegressionProof source release'
    if ($LASTEXITCODE -ne 0) { throw 'Commit failed; configure git user.name and user.email.' }
}
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'Push failed. Ensure you created a public empty GitHub repository and authenticated Git.' }
Write-Host 'Push completed. Review the GitHub Actions CI results before sharing the repository.'
