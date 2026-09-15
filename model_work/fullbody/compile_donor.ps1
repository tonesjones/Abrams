$ErrorActionPreference = 'Stop'
$experiment = $PSScriptRoot
$project = Split-Path (Split-Path $experiment -Parent) -Parent
$sdk = Join-Path $project 'tools\Reduced_CSDK_12'
$source = Join-Path $sdk 'content\citadel_addons\sulley_fullbody\models\heroes_wip\abrams\sulley_donor.vmdl'
$output = Join-Path $sdk 'game\citadel_addons\sulley_fullbody\models\heroes_wip\abrams\sulley_donor.vmdl_c'
$log = Join-Path $experiment 'compile.log'
$errors = Join-Path $experiment 'compile_stderr.log'
$started = Get-Date
$worker = Start-Process -FilePath (Join-Path $sdk 'game\bin_cs2\win64\resourcecompiler.exe') -ArgumentList @('-game', (Join-Path $sdk 'game\citadel'), '-f', '-nop4', $source) -WorkingDirectory (Join-Path $sdk 'game\bin_cs2\win64') -WindowStyle Hidden -PassThru -RedirectStandardOutput $log -RedirectStandardError $errors
if (-not $worker.WaitForExit(60000)) {
    # This older compiler can leave its process running after logging success.
    # Stop only the child created by this invocation, never another compiler.
    $worker.Kill()
    $worker.WaitForExit()
    Write-Warning 'Compiler process did not exit in 60 seconds; stopped this child after collecting its output.'
}
if (-not (Test-Path -LiteralPath $output)) { throw 'No donor was produced.' }
if ((Get-Item -LiteralPath $output).LastWriteTime -lt $started) { throw 'Donor is stale.' }
if (-not (Select-String -LiteralPath $log -Pattern 'OK: 1 compiled, 0 failed')) { throw 'Compiler did not report success. Read compile.log.' }
Get-Content -LiteralPath $log | Select-Object -Last 8
Write-Output "Fresh donor: $output"
