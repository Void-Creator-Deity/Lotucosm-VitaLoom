param(
    [string]$ActionsPath = (Join-Path $PSScriptRoot 'cleanup-actions.tsv')
)

$ErrorActionPreference = 'Stop'
$archiveRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$payloadCandidate = Join-Path $archiveRoot 'payload'
$payloadRoot = if (Test-Path -LiteralPath $payloadCandidate) {
    (Resolve-Path -LiteralPath $payloadCandidate).Path
} else {
    [IO.Path]::GetFullPath($payloadCandidate)
}
$root = (Resolve-Path -LiteralPath (Join-Path $archiveRoot '..\..\..\..')).Path.TrimEnd(
    [IO.Path]::DirectorySeparatorChar
)
$rootPrefix = $root + [IO.Path]::DirectorySeparatorChar
$payloadPrefix = $payloadRoot + [IO.Path]::DirectorySeparatorChar
$workspaceRoot = Join-Path $root 'workspace'
$workspacePrefix = $workspaceRoot + [IO.Path]::DirectorySeparatorChar
$workspaceTestTempRoot = Join-Path $workspaceRoot 'state\test_temps'
$workspaceTestTempPrefix = $workspaceTestTempRoot + [IO.Path]::DirectorySeparatorChar
$logPath = Join-Path $archiveRoot 'locked-cleanup.log'

function Write-CleanupLog {
    param([string]$Message)
    $line = '{0} {1}' -f [DateTime]::UtcNow.ToString('o'), $Message
    Add-Content -LiteralPath $logPath -Value $line -Encoding utf8
}

if (-not $archiveRoot.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Archive root is outside workspace: $archiveRoot"
}
if (-not $payloadRoot.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Payload root is outside workspace: $payloadRoot"
}
if (-not (Test-Path -LiteralPath $ActionsPath -PathType Leaf)) {
    throw "Cleanup actions manifest not found: $ActionsPath"
}

$rows = @(Import-Csv -LiteralPath $ActionsPath -Delimiter "`t")
$pending = @($rows | Where-Object { $_.status -eq 'retained_locked' })
if ($pending.Count -eq 0) {
    Write-Output 'No retained_locked items.'
    exit 0
}

Set-Content -LiteralPath $logPath -Value '' -Encoding utf8
Write-CleanupLog "START pending=$($pending.Count) archive=$archiveRoot"
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$deleted = 0
$failed = 0

foreach ($row in $pending) {
    $path = [IO.Path]::GetFullPath((Join-Path $root $row.relative_path))
    $directChild = [IO.Path]::GetDirectoryName($path) -eq $root
    $underPayload = $path.StartsWith($payloadPrefix, [StringComparison]::OrdinalIgnoreCase)
    $workspaceTemp = $false
    if ($path.StartsWith($workspacePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        $workspaceLeaf = Split-Path -Leaf $path
        $workspaceTemp = (
            ($workspaceLeaf -like 'viewport_event_node_history_*') -or
            ($path.StartsWith($workspaceTestTempPrefix, [StringComparison]::OrdinalIgnoreCase))
        )
    }
    if (-not $underPayload -and -not $directChild -and -not $workspaceTemp) {
        $row.status = 'delete_failed'
        Write-CleanupLog "REJECT outside allowed roots: $path"
        $failed++
        continue
    }
    if ($directChild -and $row.relative_path -notlike '.pytest-*' -and $row.relative_path -notlike '.tmp-*') {
        $row.status = 'delete_failed'
        Write-CleanupLog "REJECT unexpected root path: $path"
        $failed++
        continue
    }
    if (-not (Test-Path -LiteralPath $path)) {
        $row.status = 'deleted_missing'
        Write-CleanupLog "MISSING_ALREADY_ABSENT=$path"
        continue
    }

    Write-CleanupLog "ITEM path=$path"
    try {
        & takeown.exe /F $path /R /D Y *>> $logPath
        Write-CleanupLog "TAKEOWN_EXIT=$LASTEXITCODE path=$path"
        & icacls.exe $path /reset /T /C /Q *>> $logPath
        $resetCode = $LASTEXITCODE
        Write-CleanupLog "ICACLS_RESET_EXIT=$resetCode path=$path"
        if ($resetCode -ne 0) {
            & icacls.exe $path /grant:r "*$sid`:(OI)(CI)F" /T /C /Q *>> $logPath
            Write-CleanupLog "ICACLS_GRANT_EXIT=$LASTEXITCODE path=$path sid=$sid"
        }

        if (Test-Path -LiteralPath $path -PathType Container) {
            $measured = Get-ChildItem -LiteralPath $path -Force -Recurse -File -ErrorAction Stop |
                Measure-Object Length -Sum
            $row.file_count = [int]$measured.Count
            $row.size_bytes = [int64]$measured.Sum
            Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
        } else {
            $file = Get-Item -LiteralPath $path
            $row.file_count = 1
            $row.size_bytes = [int64]$file.Length
            Remove-Item -LiteralPath $path -Force -ErrorAction Stop
        }
        $row.status = 'deleted_after_acl_reset'
        $row.reason = 'historical pytest/smoke temp deleted after explicit ACL reset'
        $deleted++
        Write-CleanupLog "DELETE_OK path=$path files=$($row.file_count) bytes=$($row.size_bytes)"
    } catch {
        $row.status = 'delete_failed'
        $row.reason = $_.Exception.Message
        $failed++
        Write-CleanupLog "DELETE_FAILED path=$path error=$($_.Exception.Message)"
    }
}

$working = Join-Path $payloadRoot 'working'
if (Test-Path -LiteralPath $working) {
    try {
        if (@(Get-ChildItem -LiteralPath $working -Force -ErrorAction Stop).Count -eq 0) {
            Remove-Item -LiteralPath $working -Force
        }
    } catch {
        Write-CleanupLog "WORKING_DIR_REMAINS path=$working error=$($_.Exception.Message)"
    }
}

if (Test-Path -LiteralPath $payloadRoot) {
    $remainingPayloadFiles = @(
        Get-ChildItem -LiteralPath $payloadRoot -Force -Recurse -File -ErrorAction SilentlyContinue
    )
    if ($remainingPayloadFiles.Count -eq 0) {
        $remainingDirectories = @(
            Get-ChildItem -LiteralPath $payloadRoot -Force -Recurse -Directory -ErrorAction SilentlyContinue |
                Sort-Object { $_.FullName.Length } -Descending
        )
        foreach ($directory in $remainingDirectories) {
            if (@(Get-ChildItem -LiteralPath $directory.FullName -Force -ErrorAction SilentlyContinue).Count -eq 0) {
                Remove-Item -LiteralPath $directory.FullName -Force -ErrorAction SilentlyContinue
            }
        }
        if (@(Get-ChildItem -LiteralPath $payloadRoot -Force -ErrorAction SilentlyContinue).Count -eq 0) {
            Remove-Item -LiteralPath $payloadRoot -Force
            Write-CleanupLog "REMOVED_EMPTY_PAYLOAD_ROOT=$payloadRoot"
        }
    }
}

$rows | ConvertTo-Csv -Delimiter "`t" -NoTypeInformation |
    Set-Content -LiteralPath $ActionsPath -Encoding utf8
$summary = [pscustomobject]@{
    attempted = $pending.Count
    deleted = $deleted
    failed = $failed
    log = 'locked-cleanup.log'
}
$summary | ConvertTo-Json |
    Set-Content -LiteralPath (Join-Path $archiveRoot 'locked-cleanup-summary.json') -Encoding utf8

$finalActions = @(Import-Csv -LiteralPath $ActionsPath -Delimiter "`t")
$payloadFiles = @(Get-ChildItem -LiteralPath $payloadRoot -Force -Recurse -File -ErrorAction SilentlyContinue)
$statusCounts = @{}
foreach ($group in ($finalActions | Group-Object status)) {
    $statusCounts[$group.Name] = $group.Count
}
$inventory = [pscustomobject]@{
    archive_date = '2026-10-23'
    manifest_role = 'pre-cleanup archive provenance'
    manifest_total_items = @(Import-Csv -LiteralPath (Join-Path $archiveRoot 'manifest.tsv') -Delimiter "`t").Count
    cleanup_actions = $finalActions.Count
    action_status_counts = $statusCounts
    payload_files = $payloadFiles.Count
    payload_bytes = [int64](($payloadFiles | Measure-Object Length -Sum).Sum)
    legacy_tool_count = @(
        Get-ChildItem -LiteralPath (Join-Path $payloadRoot 'legacy-tools') -Force -File -ErrorAction SilentlyContinue
    ).Count
    pytest_log_file_count = @(
        Get-ChildItem -LiteralPath (Join-Path $payloadRoot 'pytest') -Force -File -ErrorAction SilentlyContinue
    ).Count
    locked_pending = @($finalActions | Where-Object { $_.status -eq 'retained_locked' }).Count
    cleanup_log = 'cleanup-actions.tsv'
    locked_cleanup_log = 'locked-cleanup.log'
}
$inventory | ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath (Join-Path $archiveRoot 'inventory.json') -Encoding utf8

Write-CleanupLog "END attempted=$($pending.Count) deleted=$deleted failed=$failed"
$summary | ConvertTo-Json
