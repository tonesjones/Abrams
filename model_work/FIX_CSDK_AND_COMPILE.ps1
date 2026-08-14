# Run this in PowerShell as the logged-in Steam user (Steam must be running).
# Downloads DepotDownloader, refreshes CSDK game files, re-applies CSDK zip overlays, compiles Sully model.
# Does NOT modify your Steam Deadlock install — only C:\TestCode\Abrams\tools\Reduced_CSDK_12

$ErrorActionPreference = "Stop"
$tools = "C:\TestCode\Abrams\tools"
$csdk = Join-Path $tools "Reduced_CSDK_12"
$ddDir = Join-Path $tools "DepotDownloader"
$zip = Join-Path $tools "Reduced_CSDK_12.zip"

Write-Host "=== 1) DepotDownloader ==="
New-Item -ItemType Directory -Force -Path $ddDir | Out-Null
$rel = Invoke-RestMethod "https://api.github.com/repos/SteamRE/DepotDownloader/releases/latest" -Headers @{"User-Agent"="Abrams"}
$asset = $rel.assets | Where-Object { $_.name -match "windows-x64|win-x64" } | Select-Object -First 1
if (-not $asset) { throw "No windows-x64 DepotDownloader asset found" }
$zipDd = Join-Path $ddDir "dd.zip"
Invoke-WebRequest $asset.browser_download_url -OutFile $zipDd
Expand-Archive $zipDd $ddDir -Force
$dd = Get-ChildItem $ddDir -Recurse -Filter "DepotDownloader.exe" | Select-Object -First 1 -ExpandProperty FullName
Write-Host "DD = $dd"

Write-Host "=== 2) Download Deadlock depots into CSDK (QR login in browser) ==="
# Manifests from https://deadlockmodding.pages.dev/modding-tools/csdk-12 — update if site lists newer
& $dd -app 1422450 -depot 1422451 -manifest 2639812037154209539 -qr -dir $csdk
& $dd -app 1422450 -depot 1422456 -manifest 6378769520310560496 -qr -dir $csdk

Write-Host "=== 3) Re-apply Reduced CSDK zip overlays ==="
if (-not (Test-Path $zip)) { throw "Missing $zip" }
Expand-Archive $zip $tools -Force

Write-Host "=== 4) Compile Sully Abrams vmdl ==="
$bin = Join-Path $csdk "game\bin_tools\win64"
$rc = Join-Path $bin "resourcecompiler.exe"
$vmdl = Join-Path $csdk "content\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.vmdl"
$game = Join-Path $csdk "game\citadel"
$env:PATH = "$bin;C:\Windows\System32;C:\Windows"
Set-Location $bin
& $rc -game $game -f -nop4 $vmdl
if ($LASTEXITCODE -ne 0) { throw "resourcecompiler failed with $LASTEXITCODE" }

$out = Join-Path $csdk "game\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.vmdl_c"
if (-not (Test-Path $out)) {
  # search
  $found = Get-ChildItem (Join-Path $csdk "game\citadel_addons\sully_abrams") -Recurse -Filter "abrams.vmdl_c" -ErrorAction SilentlyContinue
  $found | ForEach-Object { Write-Host "Found $($_.FullName)" }
  if (-not $found) { throw "Compile finished but abrams.vmdl_c not found" }
  $out = $found[0].FullName
}
Write-Host "COMPILED: $out"
Write-Host "Next: tell the agent to pack VPK from game/citadel_addons/sully_abrams"
