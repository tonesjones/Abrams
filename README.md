# Abrams → Sully (Deadlock model mod)

Private engineering repo for a local *Deadlock* Abrams skin: teal fur, purple spots, imported Sully head, stock locomotion.

**This README is the method record.** If you are about to “try a new compile path” or patch AnimGraph2 strings into an Isolation B model, stop. That already failed. The working approach is **stock-host mesh splice**.

Short operational resume: `CHECKPOINT.md`.  
Public GameBanana notes (texture-era zip only): `release/README.md`.  
Do **not** put `model_work/import_head/sully.glb` in any public zip.

Stock Deadlock `pak01_*` / `game\core` are never modified. Addon VPK only.

---

## Current ship

| Item | Status |
|------|--------|
| Install | `release/pak69_stockhost_dir.vpk` |
| Head | Imported Sully, 2577 verts, 100% `head`, on the neck |
| Body | Isolation B cut body (teal + spots, **no glasses**) |
| HUD portraits | Done — leave alone |
| Locomotion | Stock ANIM + AG2 + `vnmskel` kept on the host (300 sequences). User signed off on this splice. |
| Gun / book | Stock meshes left on the host |

Rollback of the addon returns pak01 Abrams. The previous statue pack is `release/pak69_dir.vpk`.

---

## The method that works

Deadlock hero walk does **not** come from FBX weights alone, and it does **not** come from putting graph *paths* in GameData.

Walk lives on the **stock compiled** `abrams.vmdl_c` (~8.6 MB):

| Piece | Why it matters |
|--------|----------------|
| `ANIM` (~4 MB) | Actual sequences: run, jump, slide, melee, abilities (~300 clips) |
| `ASEQ` / `AGRP` | Sequence groups the pawn/graph play |
| `DATA.m_animGraph2Refs` | Top-level CModel resource handles, **flagged as resources**, not GameData strings |
| `DATA.m_vecNmSkeletonRefs` | `models/heroes_wip/abrams/abrams.vnmskel` |
| `RERL` | Same three IDs the stock pawn already knows |
| 489-bone `m_modelSkeleton` | What those clips are bound to |

`heroes.vdata` only points at `models/heroes_wip/abrams/abrams.vmdl`. The graph is expected **on the model**.

### What to do (and nothing else)

1. **Host** = untouched stock compile: `model_work/abrams_backup.vmdl_c`.
2. **Donor** = Isolation B `bin_cs2` compile of the custom body + face FBX. Use it **only** as a mesh factory. Never ship that 1.4 MB file as the live hero.
3. **Splice** donor `MVTX` / `MIDX` / `MDAT` onto the host:
   - Keep stock mesh **names** (`abrams_model`, `abrams_face_model`, plus LOD aliases) so bodygroups still match.
   - Point every body LOD at the donor body buffers; every face LOD at the donor face buffers.
   - Leave `gun_model*` and `book_model*` as stock.
4. **Remap bones by name**, not by index. Isolation B and stock both have 489 bones, but the **order differs** (cloth is `$cloth_*` on stock and `_cloth_*` on the donor). Translate each donor remap entry → bone name → stock index.
5. Rewrite only `CTRL` and `DATA` (Python `keyvalues3` as KV3 v0 / `VKV3` uncompressed). Leave `ANIM`, `ASEQ`, `AGRP`, `PHYS`, `DSTF`, `RERL`, `RED2` **byte-identical**.
6. Pack the spliced host as `models/heroes_wip/abrams/abrams.vmdl_c` plus `sully_textures/`. Do **not** also pack `abrams_backup.vmdl_c` as an AnimInclude — the host already has the graph.

```
python tools\SpliceHost\splice.py splice
tools\VtexPacker\bin\Release\net8.0\VtexPacker.exe `
  sully_textures `
  release\pak69_stockhost_dir.vpk `
  models/heroes_wip/abrams/abrams.vmdl_c `
  model_work\abrams_spliced.vmdl_c
```

Requires `pip install keyvalues3`.

### Glasses

Stock **body** still has glasses. Face-only splice puts Sully’s face on Abrams-with-glasses. Always splice the Isolation B **cut body** (head/glasses already removed) together with the face.

### Why Isolation B as the live hero can never walk

`bin_cs2` cannot allocate `AnimGraph2List` / `NmSkeletonList`. The compile is a correctly skinned **bind-pose statue** (~1.4 MB, ANIM ≈ 589 bytes). Third-person gun sits at the weapon bone rest (on the floor). First-person gun can still draw.

Putting graph paths in GameData, or adding the same IDs to RERL, does not give the pawn the 4 MB sequence payload or the compiled CModel AG2 nodes. The engine then has a mesh and some strings, and nothing to play.

### Why this splice is not “just RERL again”

Failed Phase 4 patched strings onto Isolation B (no ANIM). This splice keeps stock ANIM and stock CModel AG2 fields, and only replaces render-mesh blocks.

### Verify before asking anyone to install

```
python tools\SpliceHost\splice.py inspect model_work\abrams_spliced.vmdl_c
```

Must still list the three RERL graph/skel paths and `m_animGraph2Refs`. Then, optional Blender check after a Source2Viewer glTF export:

```
blender --background --python model_work\inspect_spliced.py
```

| Check | Pass |
|--------|------|
| Body, armature-deformed | size z ≈ **2.81 m** |
| Face | 2577 verts, **100% `head`**, center z ≈ **2.62 m** |
| RERL | `hero.vnmgraph+abrams.vnmgraph`, UI graph, `abrams.vnmskel` |
| Sequences | Source2Viewer `--gltf_export_animations` lists `primary_run_*`, `jump_*`, `slide_*` |
| Fail | body z ≈ 280 (100×) or a groups-less world slab |

---

## Same method on a different hero

Do not start from a community Isolation vmdl and try to “hook anims” afterward.

1. Extract that hero’s **stock compiled** `*.vmdl_c` and freeze it as the host.
2. Confirm it has a large `ANIM` block plus `m_animGraph2Refs` / `m_vecNmSkeletonRefs` in DATA.
3. Build custom meshes as a throwaway `bin_cs2` donor (same bone *names* as the stock skeleton).
4. Splice donor mesh blocks into the host. Keep stock mesh names. Translate remaps by bone name.
5. Do not rewrite ANIM / RERL. Do not compile the live hero with `bin` / `bin_tools` / `bin_cs2`.

The splice implementation to copy is `tools/SpliceHost/splice.py` + `resource_io.py`.

---

## What failed (do not retry)

Wrong *idea*, not “we almost had it.”

| Idea | What actually happens |
|------|------------------------|
| Recolor stock face UVs | Still Abrams + glasses |
| Voxel remesh the imported head | Features melt into a bowling ball |
| Mesh-only FBX (no armature) | Giant unskinned teal slab |
| Inch verts + meter scene + `FBX_SCALE_NONE` / `axis_up='Z'` | ~100× scale |
| Flatten world matrix / parent without keep_transform | Skin or head jumps to origin |
| 14k-line **stock decompiled** vmdl as CSDK source | Red first-person wireframe explosion |
| Substring `"lip"` when deleting head verts | Hits `flip_a_page_*` book verts — use **token** match |
| `bin` / `bin_tools` compile | `ParticleFloatType_t` schema abort |
| Live Deadlock DLLs mixed with CSDK | Missing `modeldoc_utils` |
| Source `*.vmat` in addon content | Compiler rebuilds and dies |
| GameData / RERL AG2 **strings** on Isolation B | RERL IDs can match stock; pawn still a statue |
| Source `AnimGraph2List` in the CSDK vmdl | `Failed to allocate an instance of class 'AnimGraph2List'` |
| Isolation B recompile to “fix walk” | Same statue, new mesh |
| Face-only splice into stock | Glasses come back |
| `export_sully_meshonly.py` | Rebuilds the primitive blob head |
| Write Steam `pak01_*` / `game\core` | Forbidden |
| Orphan `pak08` / `pak69` / `pak90` in `addons` | Skin sticks after DMM disable |
| DMM on `*.bak_*` | Not a `.vpk` |
| VRF 10.x `Resource.Serialize` on these models | That library cannot even read `MVTX` |

Mesh donor path that *is* valid (placement only, then splice):

1. Bake the imported GLB **armature-deformed** before cutting (raw GLB verts are the wrong pose).
2. Cut head/glasses with **token** bone names, weight ≥ 0.40.
3. Seat at face center `(0, 3.361, 103)` inches, scale to stock face height 20.69 in, 100% `head`.
4. Parent with `matrix_parent_inverse`. Export FBX **with armature** (`add_leaf_bones=False`, `use_armature_deform_only=True`, axes `-Z`/`Y`, `apply_unit_scale=True`, `FBX_SCALE_UNITS`).
5. `make_clean_vmdl.py B --scale 1.0` then `compile_and_pack.ps1` **only** to refresh the donor `vmdl_c`. Then splice again.

---

## Key paths

| Path | Role |
|------|------|
| `tools/SpliceHost/splice.py` | **The working ship tool** |
| `model_work/abrams_backup.vmdl_c` | Stock host (do not overwrite) |
| `model_work/abrams_spliced.vmdl_c` | Last splice output |
| CSDK `.../sully_abrams/.../abrams.vmdl_c` | Isolation B **donor only** |
| `model_work/build_import_head.py` | Cut/seat imported head |
| `model_work/export_sully_skinned.py` | Skinned FBX export |
| `model_work/sully_export/sully_face.fbx` | Donor head FBX |
| `model_work/sully_export/abrams_body_nohead.fbx` | Donor body FBX (no glasses) |
| `sully_textures/` | Color maps + portraits |
| `release/pak69_stockhost_dir.vpk` | Current addon |
| `release/pak69_dir.vpk` | Isolation B statue rollback |
| `model_work/import_head/sully.glb` | Local mesh only |
| `in-game-screen/screenshot_aug-latest.png` | Imported head, statue era |
| `model_work/sully_export/spliced_stockhost_preview.png` | Spliced bind-pose preview |

Blender scenes (~800 MB) are not in git. Restore `sully_cut.blend` / `sully_skinned.blend` from GitHub Release `snapshot-pre-import-head` if needed.

---

## Tools (local)

- Blender 4.5 — `tools/blender-install/`
- Reduced CSDK 12 — `tools/Reduced_CSDK_12/` (donor mesh compile only)
- Source2Viewer CLI — `tools/s2v-cli/Source2Viewer-CLI.exe`
- VPK packer — `tools/VtexPacker/`
- Python `keyvalues3` — KV3 read/write for CTRL + DATA

---

## Install

1. Deadlock Mod Manager: **one** `*_dir.vpk` only — `pak69_stockhost_dir.vpk`.
2. Full game restart (not just disconnect).
3. If an old skin sticks after disable, move leftover `pak##` from `game/citadel/addons` to `disabled_vpks\`.

---

## For the next session

1. Read this file. Do not recompile Isolation B to change locomotion.
2. If the mesh needs a visual fix: edit the blend / FBX, rebuild the donor compile, run `splice.py`, pack.
3. If locomotion breaks after a splice: compare `abrams_spliced.vmdl_c` to `abrams_backup.vmdl_c` (ANIM size, RERL, `m_animGraph2Refs`). Restore the host and splice again. Do not invent a third compile path.
4. Keep HUD portraits as they are.
5. Keep `sully.glb` off GameBanana.
