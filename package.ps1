# Builds a clean, portable EnerSight.zip to send to a colleague.
# Excludes the non-portable / huge folders (venv, node_modules, .git, caches) so the
# zip is ~30 MB instead of ~2.5 GB. The colleague unzips, runs setup.ps1, then start.ps1.
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File .\package.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$src       = $PSScriptRoot
$zipPath   = Join-Path (Split-Path $PSScriptRoot -Parent) "EnerSight.zip"
$stageRoot = Join-Path $env:TEMP "EnerSight_pkg"
$stage     = Join-Path $stageRoot "EnerSight"

Write-Host "Staging a clean copy (excluding venv, node_modules, .git, caches) ..." -ForegroundColor Yellow
if (Test-Path $stageRoot) { Remove-Item $stageRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

$excludeDirs = @(
    "venv", "node_modules", ".git", "__pycache__", ".next", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".vscode", ".idea", ".claude",
    "logs", "tmp", "temp", "dist", "build"
)
$excludeFiles = @("*.pyc", "*.pyo", "*.log")

# robocopy mirrors the tree, skipping excluded dir names (at any depth) and file patterns.
robocopy $src $stage /E /XD $excludeDirs /XF $excludeFiles /NFL /NDL /NJH /NJS /R:1 /W:1 | Out-Null
# robocopy exit codes 0-7 are success; 8+ is a real failure.
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
$global:LASTEXITCODE = 0

Write-Host "Compressing ..." -ForegroundColor Yellow
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $stage -DestinationPath $zipPath

Remove-Item $stageRoot -Recurse -Force

$mb = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Host ""
Write-Host "Created $zipPath ($mb MB)" -ForegroundColor Green
Write-Host "Send that file. Your colleague: unzip -> setup.ps1 -> start.ps1 (see QUICKSTART_COLLEAGUE.md)." -ForegroundColor Gray
Write-Host ""
