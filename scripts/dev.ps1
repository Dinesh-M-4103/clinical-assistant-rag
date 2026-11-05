<#
.SYNOPSIS
    Developer tasks for Windows PowerShell (primary platform). Same tasks as scripts/dev.sh.

.DESCRIPTION
    .\scripts\dev.ps1 <setup|backend|frontend|dev|seed|test|lint|clean|eval|help>

    Every cache (Hugging Face models, uv, Playwright browsers) is kept inside the repo.
    If script execution is blocked, run it with:
    powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 <task>
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('setup', 'backend', 'frontend', 'dev', 'seed', 'test', 'lint', 'clean', 'eval', 'help')]
    [string]$Task = 'help',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$EvalArguments = @()
)

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'frontend'
$Python = Join-Path $Backend '.venv\Scripts\python.exe'
$ApiArguments = @('-m', 'uvicorn', 'app.main:app', '--reload', '--reload-dir', 'app', '--host', '127.0.0.1', '--port', '8000')

$env:HF_HOME = Join-Path $Backend '.cache\huggingface'
$env:UV_CACHE_DIR = Join-Path $Backend '.cache\uv'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $Frontend '.playwright'

function Invoke-Native {
    # Runs a native command in a directory and stops the task if it exits non-zero.
    param([string]$Directory, [string]$Command, [string[]]$Arguments)
    Push-Location $Directory
    try {
        & $Command @Arguments
        if ($LASTEXITCODE -ne 0) { throw "'$Command $Arguments' failed with exit code $LASTEXITCODE" }
    }
    finally { Pop-Location }
}

function Assert-Venv {
    if (-not (Test-Path $Python)) { throw 'Backend environment missing. Run: .\scripts\dev.ps1 setup' }
}

function Invoke-Setup {
    Invoke-Native $Backend 'uv' @('sync')
    Invoke-Native $Frontend 'npm' @('install')
    $envFile = Join-Path $Backend '.env'
    if (-not (Test-Path $envFile)) {
        Copy-Item (Join-Path $Backend '.env.example') $envFile
        Write-Host 'Created backend\.env - add your GEMINI_API_KEY to it.'
    }
}

function Invoke-Backend {
    Assert-Venv
    Invoke-Native $Backend $Python $ApiArguments
}

function Invoke-Frontend {
    Invoke-Native $Frontend 'npm' @('run', 'dev')
}

function Invoke-Dev {
    # The API runs as a child in this console while the web app stays in the foreground;
    # when the web app stops, the API and the reloader's worker are stopped with it.
    Assert-Venv
    $api = Start-Process -FilePath $Python -ArgumentList $ApiArguments -WorkingDirectory $Backend -NoNewWindow -PassThru
    try { Invoke-Frontend }
    finally { taskkill /PID $api.Id /T /F | Out-Null }
}

function Invoke-Seed {
    Assert-Venv
    Invoke-Native $Root $Python @((Join-Path $Backend 'scripts\seed_demo.py'))
}

function Invoke-Test {
    Assert-Venv
    Invoke-Native $Backend $Python @('-m', 'pytest')
    Invoke-Native $Frontend 'npm' @('test')
}

function Invoke-Lint {
    Assert-Venv
    Invoke-Native $Backend $Python @('-m', 'ruff', 'check', '.')
    Invoke-Native $Backend $Python @('-m', 'ruff', 'format', '--check', '.')
    Invoke-Native $Backend $Python @('-m', 'mypy', 'app', 'tests', 'scripts', 'evals')
    Invoke-Native $Frontend 'npm' @('run', 'lint')
    Invoke-Native $Frontend 'npm' @('run', 'typecheck')
}

function Invoke-Eval {
    # Extra arguments go to the CLI, e.g. .\scripts\dev.ps1 eval --answers
    Assert-Venv
    Invoke-Native $Backend $Python (@('-m', 'evals.run') + $EvalArguments)
}

function Invoke-Clean {
    foreach ($name in '.pytest_cache', '.mypy_cache', '.ruff_cache') {
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Backend $name)
    }
    foreach ($name in 'dist', 'coverage', 'test-results') {
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Frontend $name)
    }
    Get-ChildItem $Backend -Recurse -Directory -Filter __pycache__ -Force |
        Where-Object { $_.FullName -notmatch '\\(\.venv|\.cache)\\' } |
        Remove-Item -Recurse -Force
}

function Show-Usage {
    @'
Usage: .\scripts\dev.ps1 <task>

  setup     install backend (uv) and frontend (npm) dependencies, create backend\.env
  backend   run the API on http://localhost:8000 with auto-reload
  frontend  run the web app on http://localhost:5173
  dev       run backend and frontend together (Ctrl+C stops both)
  seed      load the synthetic demo patients into the running backend
  test      backend pytest (fast set) and frontend Vitest
  lint      ruff, mypy, ESLint and tsc
  eval      retrieval ablation over the golden questions (no LLM calls); --answers adds answer quality
  clean     remove build output and tool caches (keeps models, venv, node_modules, storage)
'@
}

switch ($Task) {
    'setup' { Invoke-Setup }
    'backend' { Invoke-Backend }
    'frontend' { Invoke-Frontend }
    'dev' { Invoke-Dev }
    'seed' { Invoke-Seed }
    'test' { Invoke-Test }
    'lint' { Invoke-Lint }
    'clean' { Invoke-Clean }
    'eval' { Invoke-Eval }
    'help' { Show-Usage }
}
