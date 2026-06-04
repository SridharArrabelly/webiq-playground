# One-time setup for webiq-playground.
# Run from the project root once the terminal is available:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1

Set-Location $PSScriptRoot

# Remove leftover temp files created while the shell was unavailable.
Remove-Item -ErrorAction SilentlyContinue .\test_webiq.py.tmp, .\.env.example.new

# Sync dependencies into the uv-managed venv.
uv sync

# Initialize git and make the first commit.
if (-not (Test-Path .\.git)) {
    git init
    git add .
    git commit -m "Initial commit: WebIQ Playground"
}

Write-Host "Done. Create a GitHub repo with:  gh repo create webiq-playground --private --source . --push"
