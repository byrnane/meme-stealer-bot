$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv")) {
    Write-Host "Создаю виртуальное окружение .venv..."
    python -m venv .venv
}

Write-Host "Устанавливаю зависимости..."
& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Создан .env. Впиши в него BOT_TOKEN и OWNER_ID."
} else {
    Write-Host ".env уже существует, оставляю его без изменений."
}

Write-Host "Создаю SQLite-базу..."
& ".\.venv\Scripts\python.exe" -m meme_stealer_bot init-db

Write-Host ""
Write-Host "Готово. Заполни .env и запусти: .\scripts\start.ps1"
