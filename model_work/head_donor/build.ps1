# Build V3 only.  This script does not install anything into Deadlock.
$ErrorActionPreference = 'Stop'
$project = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $project
$python = Join-Path $project '.venv\Scripts\python.exe'
$blender = Join-Path $project 'tools\blender-install\blender-4.5.10-windows-x64\blender.exe'
$viewer = Join-Path $project 'tools\s2v-cli\Source2Viewer-CLI.exe'
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'build_head_donor.py')
if ($LASTEXITCODE) { throw 'Head donor transfer/export failed.' }
& $python (Join-Path $PSScriptRoot 'prepare_compile.py')
if ($LASTEXITCODE) { throw 'Donor preparation failed.' }
& (Join-Path $PSScriptRoot 'compile_donor.ps1')
& $python (Join-Path $PSScriptRoot 'package_test.py')
if ($LASTEXITCODE) { throw 'Verification/packaging failed.' }
& $viewer -i (Join-Path $PSScriptRoot 'abrams_fullbody.vmdl_c') -o (Join-Path $PSScriptRoot 'compiled.gltf') -d --gltf_export_format gltf --gltf_export_animations --gltf_animation_list primary_stand_idle,primary_run_n,primary_stand_aim,melee_quick_1,slide_forward,ability_charge,ability_leap_smash
if ($LASTEXITCODE) { throw 'Compiled model round-trip failed.' }
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'preview_animations.py') -- --compiled
if ($LASTEXITCODE) { throw 'Compiled animation previews failed.' }
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'check_camera.py')
if ($LASTEXITCODE) { throw 'Offline camera check failed.' }
Write-Output 'V3 packaged; in-game testing remains required.'
