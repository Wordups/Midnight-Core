#Requires -Version 5.1
<#
.SYNOPSIS
    Canary deploy script for ECS service managed by deploymentController=ECS with CANARY strategy.

.DESCRIPTION
    Idempotent. Runs pre-deploy alarm check, optionally builds + pushes a new image,
    resolves or registers a task definition revision, triggers ECS update-service,
    watches rolloutState + RollbackAlarm until COMPLETED/FAILED/timeout, then smoke-tests.

    CRITICAL: This script never calls modify-rule. ECS owns ALB listener rule weights
    during managed canary deployments. Manual weight changes cause 503 incidents.

.PARAMETER ConfigPath
    Path to deploy.config.json. Defaults to ./scripts/deploy.config.json.

.PARAMETER ExpectedCommit
    Full SHA of the git commit being deployed. Script aborts if HEAD does not match.

.PARAMETER SkipBuild
    Skip docker build and push. Use for config-only deploys where the image is unchanged.

.PARAMETER TaskDefRevision
    Use an existing task definition revision instead of registering a new one.
    Required for config-only deploys (e.g., rotated env vars already set in console).
#>
[CmdletBinding()]
param(
    [string]$ConfigPath = './scripts/deploy.config.json',

    [Parameter(Mandatory)]
    [string]$ExpectedCommit,

    [switch]$SkipBuild,

    [int]$TaskDefRevision = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Helpers ───────────────────────────────────────────────────────────────────

function Write-Stage([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}
function Write-OK([string]$msg)   { Write-Host "    [OK]   $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Write-Fail([string]$msg) { Write-Host "    [FAIL] $msg" -ForegroundColor Red }
function Write-Info([string]$msg) { Write-Host "    $msg" -ForegroundColor Gray }

$StartTime      = Get-Date
$NewTaskDefArn  = $null
$tdFamily       = $null

# ── Stage 1: Load config ──────────────────────────────────────────────────────

Write-Stage 'Stage 1: Load config'

if (-not (Test-Path $ConfigPath)) {
    Write-Fail "Config file not found: $ConfigPath"
    exit 1
}
$cfg = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json

Write-OK "cluster  = $($cfg.ecs.cluster)"
Write-OK "service  = $($cfg.ecs.service)"
Write-OK "region   = $($cfg.region)"
Write-OK "ecr_repo = $($cfg.ecr.repository_uri)"

# ── Stage 2: Preflight checks ─────────────────────────────────────────────────

Write-Stage 'Stage 2: Preflight checks'

# 2a. Git HEAD matches expected commit
$head = (git rev-parse HEAD 2>&1).Trim()
if ($LASTEXITCODE -ne 0) {
    Write-Fail "git rev-parse failed: $head"
    exit 1
}
if ($head -ne $ExpectedCommit) {
    Write-Fail "Git HEAD $head does not match expected commit $ExpectedCommit"
    exit 1
}
Write-OK "Git HEAD matches: $head"

# 2b. Working tree is clean
$dirty = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "git status failed"
    exit 1
}
if ($dirty) {
    Write-Fail "Working tree is dirty. Commit or stash all changes before deploying."
    exit 1
}
Write-OK "Working tree clean"

# 2c. AWS account matches config
$identity = aws sts get-caller-identity --region $cfg.region | ConvertFrom-Json
if ($identity.Account -ne $cfg.account_id) {
    Write-Fail "Active AWS account ($($identity.Account)) does not match config account_id ($($cfg.account_id))"
    exit 1
}
Write-OK "AWS account: $($identity.Account)  ($($identity.Arn))"

# 2d. Docker daemon (skipped when -SkipBuild)
if (-not $SkipBuild) {
    docker info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Docker daemon is not running. Start Docker Desktop or use -SkipBuild for config-only deploys."
        exit 1
    }
    Write-OK "Docker daemon running"
} else {
    Write-Info "Docker check skipped (-SkipBuild)"
}

# ── Stage 3: Pre-deploy alarm check ──────────────────────────────────────────

Write-Stage "Stage 3: Pre-deploy alarm check  [$($cfg.cloudwatch.rollback_alarm)]"

$alarmResult = aws cloudwatch describe-alarms `
    --alarm-names $cfg.cloudwatch.rollback_alarm `
    --region $cfg.region | ConvertFrom-Json

if (-not $alarmResult.MetricAlarms -or $alarmResult.MetricAlarms.Count -eq 0) {
    Write-Fail "RollbackAlarm '$($cfg.cloudwatch.rollback_alarm)' not found in CloudWatch. Check config."
    exit 1
}

$alarmState = $alarmResult.MetricAlarms[0].StateValue

if ($alarmState -eq 'ALARM') {
    Write-Fail "RollbackAlarm is in ALARM state. Resolve the active incident before deploying."
    exit 1
} elseif ($alarmState -eq 'INSUFFICIENT_DATA') {
    Write-Warn "RollbackAlarm state is INSUFFICIENT_DATA (metrics may lack sufficient history)."
    $resp = Read-Host '    Proceed anyway? [y/N]'
    if ($resp -ne 'y' -and $resp -ne 'Y') {
        Write-Info "Deploy aborted by user."
        exit 0
    }
    Write-Warn "Proceeding with INSUFFICIENT_DATA alarm state at user request."
} else {
    Write-OK "RollbackAlarm state: $alarmState"
}

# ── Stage 4: Docker build + push ─────────────────────────────────────────────

$ShortSha  = $head.Substring(0, 7)
$DateStamp = (Get-Date -Format 'yyyyMMdd')
$ImageTag  = "cc-deploy-$DateStamp-$ShortSha"
$ImageUri  = $null

if (-not $SkipBuild) {
    Write-Stage 'Stage 4: Docker build + push'

    $FullImage = "$($cfg.ecr.repository_uri):$ImageTag"
    # Login to the registry host only (no /repo suffix); use cmd /c to avoid
    # PowerShell 5.1 pipe-encoding issues that corrupt the ECR bearer token.
    $ecrHost = ($cfg.ecr.repository_uri -split '/')[0]
    cmd /c "aws ecr get-login-password --region $($cfg.region) | docker login --username AWS --password-stdin $ecrHost"
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "ECR login failed."
        exit 1
    }
    Write-OK "ECR login successful"

    docker build -t $FullImage .
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "docker build failed."
        exit 1
    }
    Write-OK "Image built: $FullImage"

    docker push $FullImage
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "docker push failed."
        exit 1
    }
    Write-OK "Image pushed: $FullImage"

    $ImageUri = $FullImage
} else {
    Write-Stage 'Stage 4: Skipped (-SkipBuild)'
    Write-Info "Image unchanged from existing task definition revision."
}

# ── Stage 5: Resolve task definition ─────────────────────────────────────────

Write-Stage 'Stage 5: Task definition'

# Use task_family from config; read current ARN from PRIMARY deployment (service.taskDefinition can be empty)
$tdFamily    = $cfg.ecs.task_family
$svcDesc     = aws ecs describe-services --cluster $cfg.ecs.cluster --services $cfg.ecs.service --region $cfg.region | ConvertFrom-Json
$primaryDep  = $svcDesc.services[0].deployments | Where-Object { $_.status -eq 'PRIMARY' } | Select-Object -First 1
$currentArn  = if ($primaryDep -and $primaryDep.taskDefinition) { $primaryDep.taskDefinition } else { 'unknown' }
Write-Info "Task definition family: $tdFamily"
Write-Info "Current service task def: $currentArn"

if ($TaskDefRevision -gt 0) {
    # Use the pre-registered revision — validate it exists
    $tdRef  = "${tdFamily}:${TaskDefRevision}"
    $tdDesc = aws ecs describe-task-definition --task-definition $tdRef --region $cfg.region | ConvertFrom-Json
    $NewTaskDefArn = $tdDesc.taskDefinition.taskDefinitionArn
    Write-OK "Using pre-registered revision $TaskDefRevision : $NewTaskDefArn"
} else {
    # Clone current task def, swap image on container "Main", register new revision
    if (-not $ImageUri) {
        Write-Fail "No image URI available. Either set -SkipBuild with -TaskDefRevision, or omit -SkipBuild to build a new image."
        exit 1
    }

    $currentTd   = aws ecs describe-task-definition --task-definition $currentArn --region $cfg.region | ConvertFrom-Json
    $containerDefs = $currentTd.taskDefinition.containerDefinitions

    $mainIdx = -1
    for ($i = 0; $i -lt $containerDefs.Count; $i++) {
        if ($containerDefs[$i].name -eq $cfg.ecs.container_name) { $mainIdx = $i; break }
    }
    if ($mainIdx -lt 0) {
        Write-Fail "Container named '$($cfg.ecs.container_name)' not found in task definition $currentArn"
        exit 1
    }
    $containerDefs[$mainIdx].image = $ImageUri
    Write-Info "Swapped image on container '$($cfg.ecs.container_name)' to: $ImageUri"

    # Build registration payload — include only fields accepted by register-task-definition
    $td = $currentTd.taskDefinition
    $regPayload = [ordered]@{
        family               = $td.family
        containerDefinitions = $containerDefs
        networkMode          = $td.networkMode
        requiresCompatibilities = @($td.requiresCompatibilities)
        cpu                  = $td.cpu
        memory               = $td.memory
    }
    # Use PSObject.Properties to check optional fields safely under Set-StrictMode -Version Latest
    if ($td.PSObject.Properties['executionRoleArn'] -and $td.executionRoleArn) { $regPayload.executionRoleArn = $td.executionRoleArn }
    if ($td.PSObject.Properties['taskRoleArn']      -and $td.taskRoleArn)      { $regPayload.taskRoleArn      = $td.taskRoleArn }
    if ($td.PSObject.Properties['volumes'] -and $td.volumes -and $td.volumes.Count -gt 0) {
        $regPayload.volumes = $td.volumes
    }

    # Write to CWD and use file://./relative path — the only reliably cross-platform
    # format for AWS CLI on Windows (absolute file:// paths mis-parse the drive letter;
    # inline JSON has quotes stripped by PowerShell 5.1 before reaching the CLI).
    $relFile = "td-register-$ShortSha.json"
    $absFile = Join-Path (Get-Location).Path $relFile
    try {
        # PS 5.1 Set-Content -Encoding utf8 writes a BOM; Python's json.loads rejects it.
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($absFile, ($regPayload | ConvertTo-Json -Depth 20), $utf8NoBom)
        $regResult = aws ecs register-task-definition `
            --region $cfg.region `
            --cli-input-json "file://./$relFile" | ConvertFrom-Json
        $NewTaskDefArn = $regResult.taskDefinition.taskDefinitionArn
        Write-OK "Registered new task definition: $NewTaskDefArn"
    } finally {
        if (Test-Path $absFile) { Remove-Item -Path $absFile -Force }
    }
}

# ── Stage 6: Trigger ECS deployment ──────────────────────────────────────────

Write-Stage 'Stage 6: Trigger ECS deployment'
Write-Info "  cluster  : $($cfg.ecs.cluster)"
Write-Info "  service  : $($cfg.ecs.service)"
Write-Info "  task-def : $NewTaskDefArn"
Write-Warn "NOTE: ALB listener rules are NOT touched. ECS owns rule weights during canary."

$updateResult = aws ecs update-service `
    --cluster $cfg.ecs.cluster `
    --service $cfg.ecs.service `
    --task-definition $NewTaskDefArn `
    --region $cfg.region | ConvertFrom-Json

$primaryDep   = $updateResult.service.deployments | Where-Object { $_.status -eq 'PRIMARY' } | Select-Object -First 1
$deploymentId = if ($primaryDep) { $primaryDep.id } else { 'unknown' }
Write-OK "Deployment triggered.  ID: $deploymentId"

# ── Stage 7: Watch loop ───────────────────────────────────────────────────────

Write-Stage 'Stage 7: Watch loop'

$WatchStart  = Get-Date
$TimeoutSec  = [int]($cfg.deploy.watch_timeout_minutes * 60)
$IntervalSec = [int]$cfg.deploy.watch_interval_seconds
$FinalState  = 'TIMEOUT'

Write-Info "Interval: ${IntervalSec}s   Timeout: ${TimeoutSec}s"
Write-Info "Watching: rolloutState on PRIMARY deployment + $($cfg.cloudwatch.rollback_alarm)"
Write-Info ""

while ($true) {
    $elapsed = [int]((Get-Date) - $WatchStart).TotalSeconds
    if ($elapsed -ge $TimeoutSec) {
        Write-Fail "Watch loop timed out after ${TimeoutSec}s without reaching terminal state."
        $FinalState = 'TIMEOUT'
        break
    }

    # Poll service
    $svc     = aws ecs describe-services --cluster $cfg.ecs.cluster --services $cfg.ecs.service --region $cfg.region | ConvertFrom-Json
    $dep     = $svc.services[0].deployments | Where-Object { $_.status -eq 'PRIMARY' } | Select-Object -First 1
    $rollout = if ($dep -and $dep.rolloutState)  { $dep.rolloutState  } else { 'UNKNOWN' }
    $running = if ($dep) { $dep.runningCount  } else { '?' }
    $desired = if ($dep) { $dep.desiredCount  } else { '?' }
    $pending = if ($dep) { $dep.pendingCount  } else { '?' }

    # Poll alarm
    $alm        = aws cloudwatch describe-alarms --alarm-names $cfg.cloudwatch.rollback_alarm --region $cfg.region | ConvertFrom-Json
    $alarmState = if ($alm.MetricAlarms -and $alm.MetricAlarms.Count -gt 0) { $alm.MetricAlarms[0].StateValue } else { 'UNKNOWN' }

    $ts = (Get-Date).ToString('HH:mm:ss')
    Write-Info "[$ts] +${elapsed}s  rollout=$rollout  tasks=$running/$desired  pending=$pending  alarm=$alarmState"

    if ($rollout -eq 'COMPLETED') {
        Write-OK "Deployment COMPLETED."
        $FinalState = 'COMPLETED'
        break
    }
    if ($rollout -eq 'FAILED') {
        Write-Fail "Deployment FAILED (deploymentCircuitBreaker or ECS-reported failure)."
        $FinalState = 'FAILED'
        break
    }
    if ($alarmState -eq 'ALARM') {
        Write-Fail "RollbackAlarm entered ALARM state. ECS automatic rollback should be in progress."
        $FinalState = 'ALARM'
        break
    }

    Start-Sleep -Seconds $IntervalSec
}

# ── Stage 8: Smoke tests (COMPLETED only) ────────────────────────────────────

if ($FinalState -eq 'COMPLETED') {
    Write-Stage 'Stage 8: Smoke tests'
    $smokePass = $true
    foreach ($smokeHost in $cfg.deploy.smoke_test_hosts) {
        foreach ($path in $cfg.deploy.smoke_test_paths) {
            $url = "${smokeHost}${path}"
            try {
                $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
                if ($resp.StatusCode -eq 200) {
                    Write-OK "$url  -> $($resp.StatusCode)"
                } else {
                    Write-Warn "$url  -> $($resp.StatusCode)  (expected 200)"
                    $smokePass = $false
                }
            } catch {
                Write-Fail "$url  -> ERROR: $($_.Exception.Message)"
                $smokePass = $false
            }
        }
    }
    if (-not $smokePass) {
        Write-Warn "One or more smoke tests failed. Verify manually before declaring success."
    } else {
        Write-OK "All smoke tests passed."
    }
}

# ── Stage 9: Last 10 service events (non-COMPLETED) ──────────────────────────

if ($FinalState -ne 'COMPLETED') {
    Write-Stage 'Stage 9: Last 10 service events'
    $svc    = aws ecs describe-services --cluster $cfg.ecs.cluster --services $cfg.ecs.service --region $cfg.region | ConvertFrom-Json
    $events = $svc.services[0].events | Select-Object -First 10
    foreach ($evt in $events) {
        Write-Info "  $($evt.createdAt)  $($evt.message)"
    }
}

# ── Stage 10: Summary ─────────────────────────────────────────────────────────

Write-Stage 'Stage 10: Summary'

$TotalSec     = [int]((Get-Date) - $StartTime).TotalSeconds
$tdShort      = if ($NewTaskDefArn) { "${tdFamily}:$(($NewTaskDefArn -split ':')[-1])" } else { 'n/a' }
$summaryColor = if ($FinalState -eq 'COMPLETED') { 'Green' } else { 'Red' }

$lines = @(
    '',
    '  +------------------------------------------------------+',
    '  |  Deploy Summary                                       |',
    '  +------------------------------------------------------+',
    "  |  Service      : $($cfg.ecs.service.PadRight(36))|",
    "  |  Cluster      : $($cfg.ecs.cluster.PadRight(36))|",
    "  |  Task Def     : $($tdShort.PadRight(36))|",
    "  |  Commit       : $($head.Substring(0,7).PadRight(36))|",
    "  |  Final State  : $($FinalState.PadRight(36))|",
    "  |  Duration     : $("${TotalSec}s".PadRight(36))|",
    '  +------------------------------------------------------+',
    ''
)
foreach ($line in $lines) {
    Write-Host $line -ForegroundColor $summaryColor
}

exit $(if ($FinalState -eq 'COMPLETED') { 0 } else { 1 })
