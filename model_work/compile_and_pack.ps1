# Compile Sully Abrams (bin_cs2) and pack a single addon VPK. Does not touch Steam pak01.
param(
  [string]$OutName = "pak69_dir.vpk"
)
$ErrorActionPreference = "Stop"
$root = "C:\TestCode\Abrams"
$csdk = Join-Path $root "tools\Reduced_CSDK_12"
$bin = Join-Path $csdk "game\bin_cs2\win64"
$game = Join-Path $csdk "game\citadel"
$vmdl = Join-Path $csdk "content\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.vmdl"
$compiled = Join-Path $csdk "game\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.vmdl_c"
$backup = Join-Path $root "model_work\abrams_backup.vmdl_c"
$outVpk = Join-Path $root "release\$OutName"
$s2v = Join-Path $root "tools\s2v-cli\Source2Viewer-CLI.exe"
$gamePak = "C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\pak01_dir.vpk"

if (-not (Test-Path $backup)) {
  Write-Host "Extracting stock abrams.vmdl_c as backup (read-only from game VPK)"
  $tmp = Join-Path $root "model_work\stock_vmdl_extract"
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  & $s2v -i $gamePak -o $tmp -f "models/heroes_wip/abrams/abrams.vmdl_c"
  $found = Get-ChildItem $tmp -Recurse -Filter "abrams.vmdl_c" | Select-Object -First 1
  if (-not $found) { throw "Could not extract stock abrams.vmdl_c" }
  Copy-Item $found.FullName $backup -Force
}

Write-Host "Compiling $vmdl"
$env:PATH = "$bin;C:\Windows\System32;C:\Windows"
Set-Location $bin
& (Join-Path $bin "resourcecompiler.exe") -game $game -f -nop4 $vmdl
if (-not (Test-Path $compiled)) { throw "Compile did not produce $compiled" }
Write-Host "COMPILED $compiled ($((Get-Item $compiled).Length) bytes)"

Write-Host "Packing VPK"
Set-Location $root
$packer = Join-Path $root "tools\VtexPacker\bin\Release\net8.0\VtexPacker.exe"
& $packer `
  (Join-Path $root "sully_textures") `
  $outVpk `
  "models/heroes_wip/abrams/abrams.vmdl_c" $compiled `
  "models/heroes_wip/abrams/abrams_backup.vmdl_c" $backup

Write-Host "WROTE $outVpk ($((Get-Item $outVpk).Length) bytes)"
