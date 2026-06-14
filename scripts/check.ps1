$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Сначала выполни .\scripts\setup.ps1"
}

& ".\.venv\Scripts\python.exe" -m pytest -q
& ".\.venv\Scripts\ruff.exe" check .
& ".\.venv\Scripts\ruff.exe" format --check .
