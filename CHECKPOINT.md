# Checkpoint — Sully Abrams

## 2026-09-05: full-body rebuild

Latest revision: `release/fullbody/pak69_sulley_head_donor_v3_dir.vpk` (unapproved).
User confirmed baseline animations and crosshair placement. Restored the exact
five previously working Sulley portraits and refined head proportions, smile,
cheek smoothing and short fur. The film reference likeness is not yet matched.
User's milestone feedback: this is a decent functional milestone, but the face
is still unsatisfactory and does not resemble real Sulley. Do not repeat the
same proportion/smoothing/fur pass with a different model and expect a material
result. A future face attempt needs a different art approach: reshape/sculpt the
facial planes and muzzle, revise brows/eyes/nose as one composition, and use a
reference-driven texture/material pass before recompiling. Astra is only worth
using if it is assigned that changed approach and given the reference and this
checkpoint; otherwise retain the current working milestone.
Skeleton, original weights and all 3,483 vertices outside the head are unchanged.
The baseline is preserved in `release/fullbody/accepted_baseline/` and
`model_work/fullbody/accepted_baseline/`. The latest revision is installed as
`Deadlock/game/citadel/addons/pak69_dir.vpk`, SHA256
`21081248c4a2095c62e47b69d3215b6840ace6d423c3a93c8d97f3f1346d1ac9`.
The V3 candidate has not been installed or playtested. Keep the accepted
rollback available while judging any future face revision.

## Disk-space audit, 2026-09-05

The current full-body rebuild requires `model_work/import_head/`,
`model_work/fullbody/stock/`, `model_work/fullbody/`, and the small
`sulley_fullbody` source/output trees inside `tools/Reduced_CSDK_12/`.
Keep the latest VPK and its accepted baseline rollback.

The 2026-09-15 cleanup removed the duplicate VPK, automatic Blender backups,
transient previews, obsolete extracted/export trees, and the retired
`sully_abrams` CSDK workspace. The current source, stock snapshot, accepted
rollback, latest donor experiment, portraits, and verification reports remain.

## 2026-09-06: new donor-head V3

Built with Terra at medium effort from
`C:\Users\Owner\Downloads\sulley_monsters_inc..glb`. This replaces the V2
head/fur presentation with a direct, fitted transfer of the new donor's head
geometry and embedded 512px texture. It retains the accepted V2 body, stock
Abrams skeleton, animation payload, camera, weapon/book attachments, and the
five proven Sulley portraits. The donor skeleton is not packed or merged.

Candidate VPK: `release/fullbody/pak69_sulley_head_donor_v3_dir.vpk`
SHA256 `fb58ae6a89a23f22cb084b9ee17f54938b1b7430525f26cbf6d23ae3fbc8be4f`.
It was deliberately **not installed** into Steam or Mod Manager. Compiler,
VPK CRC, compiled round-trip animation samples, 60 offline camera rays, and
stock-host block preservation all passed. Actual compiled close-up:
`model_work/head_donor/compiled_face_close.png`.

The donor provides a materially better Sulley silhouette and correct textured
eyes/smile, but its face is inherently low-poly (472 source head vertices,
508 compiled). If it is rejected after a game test, do not repeat pipeline
tuning. That is when Sol or Astra is justified to select a higher-detail donor
or specify a real sculpt/texture workflow.

The initial prototype was `release/fullbody/pak69_sulley_fullbody_test_dir.vpk`.
Read `model_work/fullbody/README.md` for its verification evidence, rebuild command,
limitations and next in-game test. Full Sulley body/eyes replace the old head swap;
stock animation, skeleton, camera and attachments are retained. Offline checks
pass for the documented samples; user subsequently confirmed animations and
crosshair clearance. Do not describe the artwork as finished.

Everything below is the earlier head-swap/camera-test history.

## Previous checkpoint (2026-08-20, camera-clearance test)

Resume file. Method record is **`README.md`** — read that before touching compile or AG2.

Stock Deadlock `pak01_*` / `game\core` were never modified.

Git: https://github.com/tonesjones/Abrams (`main`)

---

## Status

**Ship:** `release\pak69_stockhost_dir.vpk`

**Current test:** `release\pak69_camera_test_v2_dir.vpk`

Stock compiled Abrams is the host. Isolation B donated only body + face mesh blocks. Stock ANIM / AG2 / `vnmskel` stayed on the file.

| Piece | Result |
|--------|--------|
| Head | Sully, 2577 verts, 100% `head`, center z ≈ 2.62 m |
| Body | Cut Isolation B body, 2.81 m, no glasses |
| HUD | Leave portraits alone |
| Locomotion | Stock sequences + graph refs preserved. User signed off. |

### 2026-08-20 camera-clearance iteration

The first conservative test (`pak69_camera_test_dir.vpk`, side `-54`, aiming
back `86`) still left the crosshair behind the custom model. The screenshot
showed that Sully needs substantially more clearance, not a small stock-like
adjustment.

For reference, the stock Paradox/Chrono model used in the comparison screenshot
has side `-33.6`, normal back `108.15`, and aiming back `68.25`. That confirms
the offset sign; her much narrower silhouette is what makes the smaller value
work.

Built a stronger isolated V2 calibration. It uses the exact same Sully body,
head, textures, stock animation payload, and mesh splice as the current ship.
Only these stock Abrams camera values changed:

| Setting | Stock | Test |
|---------|------:|-----:|
| Camera side offset | -44 | **-90** |
| Aiming back offset | 75 | **110** |
| Normal back offset | 111 | **135** |
| Standing height | 100 | 100 (unchanged) |

This deliberately moves Sully farther left in frame and reduces his apparent
size in both normal and aiming views. The normal/default build remains
unchanged; camera overrides are optional CLI arguments in
`tools\SpliceHost\splice.py`.

Verification completed:

- VPK checksum verification: passed.
- `ANIM`, `ASEQ`, `AGRP`, `PHYS`, and `RERL`: byte-identical to the working splice.
- Only the compiled model's `DATA` block differs from `abrams_spliced.vmdl_c`.
- Both AnimGraph2 references and the NmSkeleton reference are present after reload.

Build command:

```powershell
.\.venv\Scripts\python.exe tools\SpliceHost\splice.py splice `
  --out model_work\abrams_camera_test_v2.vmdl_c `
  --camera-side-offset -90 `
  --camera-back-offset 135 `
  --camera-aiming-back-offset 110

.\tools\VtexPacker\bin\Release\net8.0\VtexPacker.exe `
  .\sully_textures `
  .\release\pak69_camera_test_v2_dir.vpk `
  models/heroes_wip/abrams/abrams.vmdl_c `
  .\model_work\abrams_camera_test_v2.vmdl_c
```

### In-game test requested

Install **only** `pak69_camera_test_v2_dir.vpk`, fully restart Deadlock, and compare:

1. Normal movement camera.
2. Aiming at level targets.
3. Looking sharply up and down.
4. Crouch, slide, and melee.

Capture one screenshot if the reticle still overlaps Abrams. If the new camera
feels too far left or too distant, tune the two optional values rather than
editing the mesh.

Rebuild: `python tools\SpliceHost\splice.py splice` then `VtexPacker.exe` (see README).

Do **not** recompile Isolation B to change walk.

---

## Paths

| Path | What |
|------|------|
| `release\pak69_stockhost_dir.vpk` | Install this |
| `release\pak69_camera_test_v2_dir.vpk` | Current strong camera-clearance test; install by itself |
| `release\pak69_camera_test_dir.vpk` | Rejected conservative camera test; retained for comparison |
| `release\pak69_dir.vpk` | Isolation B statue rollback |
| `model_work\abrams_backup.vmdl_c` | Stock host — do not overwrite |
| `model_work\abrams_spliced.vmdl_c` | Last splice output |
| `model_work\abrams_camera_test_v2.vmdl_c` | Same splice with V2 camera values |
| `model_work\abrams_camera_test.vmdl_c` | Rejected conservative camera test model |
| CSDK `.../sully_abrams/.../abrams.vmdl_c` | Mesh donor only |
| `model_work\import_head\sully.glb` | Local mesh — not for GameBanana |

---

## Rollback

Disable/remove only the Sully addon VPK. No Steam verify. Orphans `pak08`/`pak69`/`pak90` in `addons` → `disabled_vpks\`.

---

## Next step after camera feedback

Do the first head-likeness pass without changing animation plumbing: widen the
head, reduce front-to-back depth, and shorten the lower chin using landmark-based
transforms. Keep the camera-test settings separate until the user approves them.

---

## 2026-08-20 V2 result — failed; next iteration awaiting approval

The strong V2 camera test (`side -90`, `normal back 135`, `aiming back 110`)
did **not** correct the in-game placement. The supplied stock Abrams screenshot
shows the intended baseline clearly: Abrams occupies the left/center of the
frame while the crosshair sits in a clear lane to his right. With the Sully
splice, the crosshair remains over the character despite extreme changes to the
camera values stored in the compiled model.

This result changes the working theory. Do not keep tuning those three numbers.
Either Deadlock is sourcing the active gameplay camera from somewhere other
than this compiled-model GameData, or the custom mesh/origin data is changing
the relationship between the stock skeleton and the visible silhouette.

### Proposed next iteration (do not start without user approval)

1. Measure the stock Abrams and Sully screenshots at normalized screen
   coordinates so the target offset is explicit rather than estimated by eye.
2. Trace every runtime source of `CitadelCameraSettings_t` and Abrams camera
   overrides in the current game data, including hero/skin definitions, and
   verify which addon asset wins at load time.
3. Build one controlled diagnostic using the **untouched stock Abrams mesh**
   with an unmistakably extreme camera value. This isolates whether model-level
   camera GameData is honored at all.
4. Based on that single test:
   - If stock Abrams moves, compare stock and donor mesh transforms/bounds and
     correct the Sully mesh origin or lateral placement while preserving the
     stock skeleton and animation blocks.
   - If stock Abrams does not move, stop editing the model camera block and
     patch the actual hero/skin camera source found in step 2.
5. Produce only one follow-up VPK, verify protected animation/physics/skeleton
   blocks, and request matching stock/custom screenshots from the same position.

No implementation work for this iteration has been started. The current V2
files are retained only as evidence that compiled-model camera tuning was not
effective.

## 2026-09-15: repository cleanup

Removed duplicate camera-test and face-v2 VPKs, the old texture-era ZIP, the
duplicate full-body package, Blender auto-backups, transient preview folders,
old extracted/export workspaces, and the retired `sully_abrams` CSDK tree.
Kept the working splice code, current full-body and donor-head source, stock
snapshots, accepted rollback, five portrait resources, source GLB, offline
reports, and the latest unapproved V3 VPK. The pipeline preserves animations,
camera, attachments and HUD; the remaining challenge is achieving a convincing
Sulley face in game. No new package was approved or installed.
