[CmdletBinding()]
param(
  [string]$HelixDir,
  [switch]$IncludeFullTest
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$resultsDir = Join-Path $repositoryRoot 'results'
if ([string]::IsNullOrWhiteSpace($HelixDir)) {
  $HelixDir = Join-Path $repositoryRoot '..\HELIX-git'
}
$resolvedHelixDir = (Resolve-Path -LiteralPath $HelixDir).Path

if (-not (Test-Path -LiteralPath (Join-Path $resolvedHelixDir 'package.json'))) {
  throw "HelixDir must contain package.json: $resolvedHelixDir"
}

$null = New-Item -ItemType Directory -Force -Path $resultsDir
$failures = [System.Collections.Generic.List[string]]::new()

function Invoke-HelixExperiment {
  param(
    [string]$Name,
    [string]$Command
  )

  $log = Join-Path $resultsDir "$Name.txt"
  $header = @(
    "# HELIX offline experiment: $Name",
    "# Timestamp: $(Get-Date -Format o)",
    "# HelixDir: $resolvedHelixDir",
    "# Commit: $(git -c safe.directory=$resolvedHelixDir -C $resolvedHelixDir rev-parse HEAD)",
    "# Node: $(node --version)",
    "# npm: $(npm --version)",
    "# Command: $Command",
    ""
  )
  Set-Content -LiteralPath $log -Value $header -Encoding utf8

  Push-Location $resolvedHelixDir
  try {
    $output = Invoke-Expression $Command 2>&1
    $exitCode = $LASTEXITCODE
    $output | Tee-Object -FilePath $log -Append
    if ($exitCode -ne 0) {
      $failures.Add("$Name (exit $exitCode)")
      Write-Warning "Experiment '$Name' failed with exit code $exitCode. See $log"
    }
  } finally {
    Pop-Location
  }
}

Invoke-HelixExperiment -Name 'typecheck' -Command 'npm.cmd run typecheck'
Invoke-HelixExperiment -Name 'cadence-verify' -Command 'npm.cmd run task:parity:cadence:verify'
Invoke-HelixExperiment -Name 'assembly-verify' -Command 'npm.cmd run assembly:contract:verify'

if ($IncludeFullTest) {
  Invoke-HelixExperiment -Name 'tests' -Command 'npm.cmd test'
}

if ($failures.Count -gt 0) {
  Write-Host "Completed with failures: $($failures -join ', '). Logs are in $resultsDir"
  exit 1
}

Write-Host "Completed successfully. Logs are in $resultsDir"
