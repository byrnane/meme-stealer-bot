$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Сначала выполни .\scripts\setup.ps1"
}

& ".\.venv\Scripts\python.exe" -m meme_stealer_bot doctor
