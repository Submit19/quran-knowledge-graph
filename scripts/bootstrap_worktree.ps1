<#
.SYNOPSIS
    Hydrate a fresh worktree with the local-only fixtures that aren't tracked in git.

.DESCRIPTION
    When you create a new worktree via `git worktree add .claude/worktrees/foo origin/main`,
    two gitignored files are missing:
      - .env                    (secrets - Neo4j password, API keys)
      - data/answer_cache.json  (~49 MB cached Q&A; safe to start empty)

    This script tries to copy them from the parent checkout (../../..). If it can't find
    a parent checkout, it falls back to:
      - .env                    -> copy .env.example to .env, prompt to fill in
      - data/answer_cache.json  -> copy data/answer_cache.example.json (empty [])

    Idempotent: skips files that already exist.

.NOTES
    The verse_analysis prompt files (prompts/verse_analysis/v2_system.txt, v2_1_system.txt)
    are now tracked in git as of 2026-05-20 - they don't need bootstrapping.

    Verification after running:
        python -m pytest tests/ -q
    Expect: 204 passed, 1 skipped.
#>

[CmdletBinding()]
param(
    [string]$ParentRepo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
)

$ErrorActionPreference = "Stop"
$Worktree = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "Bootstrapping worktree: $Worktree"
Write-Host "Looking for parent repo:  $ParentRepo"
Write-Host ""

function Copy-IfMissing {
    param(
        [string]$RelativePath,
        [string]$FallbackRelativePath = $null
    )
    $dest = Join-Path $Worktree $RelativePath
    if (Test-Path $dest) {
        Write-Host "  [skip] $RelativePath already exists"
        return
    }

    $src = Join-Path $ParentRepo $RelativePath
    if (Test-Path $src) {
        $destDir = Split-Path $dest -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item $src $dest
        $size = (Get-Item $dest).Length
        Write-Host "  [copy] $RelativePath  ($size bytes from parent)"
        return
    }

    if ($FallbackRelativePath) {
        $fallback = Join-Path $Worktree $FallbackRelativePath
        if (Test-Path $fallback) {
            Copy-Item $fallback $dest
            Write-Host "  [fallback] $RelativePath  (from $FallbackRelativePath)"
            if ($RelativePath -eq ".env") {
                Write-Host "             ACTION: edit .env and fill in real secret values" -ForegroundColor Yellow
            }
            return
        }
    }

    Write-Host "  [missing] $RelativePath - no parent and no fallback" -ForegroundColor Red
}

Copy-IfMissing -RelativePath ".env"                    -FallbackRelativePath ".env.example"
Copy-IfMissing -RelativePath "data/answer_cache.json"  -FallbackRelativePath "data/answer_cache.example.json"

Write-Host ""
Write-Host "Done. Verify with:  python -m pytest tests/ -q"
