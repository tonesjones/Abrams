# Full-body Sulley prototype — September 5, 2026

**Status: user confirmed the baseline animations and crosshair work. Face v2 is
compiled and checked offline; its appearance and restored HUD need a game check.**

Current candidate addon: `../../release/fullbody/pak69_sulley_head_donor_v3_dir.vpk`.
It is unapproved and must remain an offline test artifact until the face is
accepted in game. The accepted rollback is under `accepted_baseline/`.
The sibling `manifest.json` identifies its contents and hashes.

Installed for the local playtest at
`C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\addons\pak69_dir.vpk`.
The installed copy's SHA256 matches the release manifest. It replaces the prior
full-body test. Start/restart Deadlock to load it. To return to stock Abrams, move
only this installed `pak69_dir.vpk` out of `addons`, then fully restart the game.
Do not remove the game's main `citadel\pak01_dir.vpk`.

This experiment replaces the complete visible body and head with the existing
local Sulley GLB. The old head-on-Abrams builds remain separate. The new mesh is
35,336 source body vertices plus 292 eye vertices, driven by 46 stock
Abrams bones. Stock gun/book meshes are retained.

## Face v2 and portrait restoration

- Restored all five compiled Sulley HUD portraits from the previous stock-host
  release. Extracting this VPK and comparing SHA256 confirms identical bytes.
- Broadened the head, shortened the chin, opened the smile to expose teeth,
  preserved round eyes, and lightly smoothed cheeks/chin.
- Added 7,386 short head-bound fur strands and the source normal texture.
  This is still the existing stylized asset, not a film-quality sculpt or coat.
- `face_revision_verification.json` confirms identical skeleton and original
  skin weights, with zero movement in all 3,483 original vertices outside the head.
- Baseline source and VPK are preserved in `accepted_baseline/` and
  `../../release/fullbody/accepted_baseline/`. Restore that VPK as the installed
  `pak69_dir.vpk` to roll back this face revision.
- `face_front.png` and `face_threequarter.png` are Blender previews, not game captures.

## What has been verified

- Fresh extraction from the installed game exactly matches the old stock backup
  (SHA256 `e77a3feadd321c98488186e777555c04c5956f680c327c810e714fa1dffd3135`).
- Stock animation, sequence, physics and other original blocks are byte-identical;
  only CTRL, DATA and RERL differ. DATA changes are limited to mesh bone-remap tables.
- The entire stock skeleton, camera settings, attachments, graph references and
  gameplay metadata are preserved. New material references are appended to RERL.
- Donor bind positions match stock within 0.105 inch / 2.66 mm in the raw compiled
  comparison (Blender's separate import comparison measures about 2.8 mm).
- The actual compiled output has been re-exported and rendered through stock idle,
  run, melee, slide, charge and leap-smash samples. See `compiled_previews/`.
- Both original and compiled meshes respond similarly to those sampled clips;
  this does not exercise the runtime animation graph, IK, transitions or ragdoll.
- `primary_stand_aim` is **not a passing standalone preview**: the isolated clip
  also collapses the stock reference. Its runtime layering/interpretation needs
  in-game verification; do not diagnose the whole rig from that isolated render.
- 60 hypothetical center rays clear the compiled body: two clips, five frames,
  two stored camera distances and three viewing pitches. `camera_report.json`
  states the assumptions. This is not proof that Deadlock honors these settings.
- VPK checksum validation succeeds. Custom materials use unique names; shared
  default masks are supplied by the installed game, not overridden by this addon.

## What remains to test in Deadlock

The user has confirmed baseline animations and crosshair placement. For v2,
first verify the top HUD portrait and face appearance under game lighting.
The broader checklist below records coverage not individually confirmed.

Use only this Abrams replacement, fully restart the game, then test in the hero
practice area. Keep the same location and target for stock/custom comparisons.

1. Normal movement and aimed firing at a level target: reticle visibility, gun
   grip, shot impacts, and whether the paws cross the sight line.
2. Look up/down, crouch, slide, reload, and aim close to a wall.
3. Light/heavy melee, charge, leap, other abilities, and movement transitions.
4. Check tail/feet clipping, weapon/book attachment, death and ragdoll.

Most useful feedback: normal and aimed screenshots from the same position, plus
a short movement/attack recording. Record whether the whole character is offset
or whether only the shoulder/head blocks the reticle.

If overlap remains, first confirm which addon is loaded. Then perform the planned
single stock-mesh camera diagnostic to establish whether model-level camera
values are honored. Do not resume blind side/back-offset tuning.

## Deliberate prototype limitations

- Sulley has longer legs than the film character so the stock foot/knee/hip motion
  remains useful. This is a functional full-body first pass, not final art.
- The face/eyes move rigidly with the head; facial expressions have not been mapped.
- Fur uses the source color/normal textures and short face geometry. Angular
  cheeks and the limited source sculpt remain visible in close-ups; matching
  the supplied movie reference needs further sculpt and fur work.
- Four source tail joints map onto the stock tail chain. Extreme motion and ground
  contact need live review. Fingers also need a live gun-grip check.
- The compiler reports successful output but can fail to exit. `compile_donor.ps1`
  waits 60 seconds, stops only its own child, and requires a fresh output plus the
  explicit success log. It never accepts a pre-existing stale donor.
- CSWin64 was not found in the local toolchain. The guide's alternative final
  compiler route was therefore not executed; this build reuses the proven splice.

## Rebuild

From the repository root:

```powershell
.\model_work\fullbody\build.ps1
```

Uses the existing Blender, CSDK mesh compiler, Source2Viewer, VtexPacker and repo
Python environment. NumPy is supplied by Blender, not added to the Python venv.
The build does not install, launch the game or modify stock Steam VPKs.

To recreate the stock inputs:

```powershell
.\tools\s2v-cli\Source2Viewer-CLI.exe -i 'C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\pak01_dir.vpk' -o model_work\fullbody\stock -f models/heroes_wip/abrams/abrams.vmdl_c
.\tools\s2v-cli\Source2Viewer-CLI.exe -i model_work\fullbody\stock\models\heroes_wip\abrams\abrams.vmdl_c -o model_work\fullbody\stock\abrams.gltf -d --gltf_export_format gltf --gltf_export_animations --gltf_animation_list primary_stand_idle,primary_run_n,primary_stand_aim,melee_quick_1,slide_forward,ability_charge,ability_leap_smash
```

The fitter uses the Sulley source weights and explicit bone-name mappings. A
monotone body fit and limb/tail centerlines avoid transferring coat deformation.
The packaging check verifies the host mesh order before calling the old splicer.

Model routing: Terra can run established rebuilds and make simple script/material
changes. Luna can inventory and compare manifests. Sol is suitable for bounded
rigging-script work. Keep unresolved camera-source and animation-graph diagnosis
with the lead model until there is a reproducible failing case.
