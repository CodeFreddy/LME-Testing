$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

git -C $repoRoot config core.hooksPath .githooks
Write-Host "Configured core.hooksPath=.githooks for $repoRoot"
