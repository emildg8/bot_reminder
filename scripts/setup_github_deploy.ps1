# Одноразовая настройка GitHub Secrets для автодеплоя (push → restart Wispbyte).
# Использование:
#   1. Скопируй .env.deploy.local.example → .env.deploy.local и заполни
#   2. .\scripts\setup_github_deploy.ps1
# Или передай переменные окружения BOT_TOKEN, ADMIN_TELEGRAM_IDS, WISP_*.

param(
    [string]$EnvFile = ".env.deploy.local",
    [string]$Repo = "emildg8/bot_reminder"
)

$ErrorActionPreference = "Stop"

function Read-EnvFile($path) {
    $vars = @{}
    if (-not (Test-Path $path)) { return $vars }
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        if ($line -match "^([^=]+)=(.*)$") {
            $vars[$matches[1].Trim()] = $matches[2].Trim().Trim('"').Trim("'")
        }
    }
    return $vars
}

$fileVars = Read-EnvFile $EnvFile
$names = @(
    "BOT_TOKEN",
    "ADMIN_TELEGRAM_IDS",
    "WISP_PANEL_URL",
    "WISP_API_TOKEN",
    "WISP_SERVER_UUID"
)

$values = @{}
foreach ($name in $names) {
    if ($fileVars.ContainsKey($name) -and $fileVars[$name]) {
        $values[$name] = $fileVars[$name]
    } elseif ([Environment]::GetEnvironmentVariable($name)) {
        $values[$name] = [Environment]::GetEnvironmentVariable($name)
    }
}

$missing = @($names | Where-Object { -not $values.ContainsKey($_) -or -not $values[$_] })
if ($missing.Count -gt 0) {
    Write-Host "Не хватает значений: $($missing -join ', ')"
    Write-Host "Создай $EnvFile из .env.deploy.local.example или задай переменные окружения."
    exit 1
}

Write-Host "==> gh auth status"
gh auth status -h github.com | Out-Null

foreach ($name in $names) {
    Write-Host "==> Setting secret $name"
    $values[$name] | gh secret set $name -R $Repo --body -
}

Write-Host ""
Write-Host "Готово. Secrets настроены для $Repo"
Write-Host "Проверка: gh secret list -R $Repo"
Write-Host "Тест деплоя: gh workflow run CI -R $Repo --ref main"
