# Abrams → Sully (Deadlock model mod)

Private engineering repo for a *Deadlock* Abrams skin themed as a blue-furred, purple-spotted monster (Sulley / Monsters Inc. fan look).

**This README is a handoff document** for a human or another LLM: goal, current state, what already works, what failed, and what to do next. For the short operational resume, also read **`CHECKPOINT.md`**.

Public install notes for the texture-era zip live under `release/README.md`. Do **not** put the imported Dreamlight Valley mesh into any public GameBanana zip.

---

## Goal

Ship a local Deadlock **addon VPK** that:

1. Makes Abrams look like Sully (teal fur, purple spots, no glasses).
2. Replaces the **3D head** with a proper Sully mesh (not just a recolored Abrams face).
3. Keeps **stock walk / jump / slide / gun attach / abilities** animating.
4. Leaves **HUD portraits** as the already-good Sully cards.
5. Never writes into Steam `pak01_*` or `game\core` — **addon VPK only**.

### Success criteria (in-match)

| Check | Target |
|--------|--------|
| Head | Readable Sully head on the neck |
| Body | Teal coat/pants with spots, glasses gone |
| Locomotion | Legs cycle; jump/slide play |
| Gun (third person) | Stays in the hand, not on the floor |
| First person | Still usable |
| Portraits | Unchanged Sully UI cards |

### Current state (2026-08-14)

| Item | Status |
|------|--------|
| Sully head mesh + textures | **Done** — looks good in-match |
| Body recolor + no glasses (Isolation B body) | **Done** |
| HUD portraits | **Done** — leave alone |
| Walk / jump / slide | **Broken** — character is a skinned statue |
| Third-person gun | **On the floor** (same as statue; bind pose) |
| Next agreed approach | Graft meshes into **stock compiled** `abrams.vmdl_c` (not another CSDK Isolation B recompile) |

---

## Hard rules

1. **Addon VPK only.** Never modify Steam `pak01_*` or `game\core`.
2. **Local mesh only.** `model_work/import_head/sully.glb` is a Dreamlight Valley rip for local testing. Do **not** ship it in `BlueSpot_Monster_Abrams.zip` / GameBanana.
3. **Do not invent a new compile path** for “maybe this will animate.” Isolation B + `bin_cs2` is a dead end for locomotion.
4. **Do not remesh** the imported head (voxel remesh melted features into a bowling ball).
5. **Do not** rerun `export_sully_meshonly.py` (rebuilds the primitive blob head).
6. DMM needs a real `*_dir.vpk` name. Files like `*.bak_pre_import_head` are rejected.
7. One Sully VPK at a time. Orphan `pak08`/`pak69`/`pak90` left in `addons` will keep old skins after DMM disable — move orphans to `disabled_vpks\`.

---

## Architecture (what we learned)

Deadlock heroes do **not** get walk cycles from a few FBX skin weights alone.

Stock compiled Abrams (`model_work/abrams_backup.vmdl_c`, ~8.6 MB) includes:

- Skeleton (489 bones; names match our custom mesh)
- **AnimGraph2** references:
  - `animgraphs/animgraph2/hero/hero.vnmgraph+abrams.vnmgraph`
  - `animgraphs/animgraph2/hero/hero_ui.vnmgraph+abrams.vnmgraph`
- **NmSkeleton**: `models/heroes_wip/abrams/abrams.vnmskel`
- Full animation-related payload used by the pawn

Community “Isolation B” path (CSDK `make_clean_vmdl.py B` + custom body/face FBX + stock gun/book DMX) compiles with **`bin_cs2` only**. That compiler:

- **Cannot allocate** `AnimGraph2List` / `NmSkeletonList` (`Failed to allocate an instance of class 'AnimGraph2List'`)
- Produces a ~1.4 MB model that is **skinned correctly in bind pose** but never runs the hero graph

Result: mesh sits on the character at the right scale, but **does not pose for walk/jump/slide**. Third-person gun sits at the weapon bone rest (on the floor). First-person gun can still appear.

`heroes.vdata` only points at `models/heroes_wip/abrams/abrams.vmdl` — the anim graph is expected on the **model**, not as a separate hero-vdata override we found.

---

## Timeline of attempts

### Phase 1 — Texture / portrait only

- Recolor coat/upper/lower/gun/teeth; custom HUD portraits.
- **Issue:** Stock head UV still read as Abrams; glasses remained.
- Ruled out texture-only for “looks like Sully in 3D.”

### Phase 2 — Procedural / primitive head

- Built a joined-sphere Sully-ish head in Blender, cut stock head/glasses off the body, skinned FBX, Isolation B compile.
- **In-match (2026-08-12):** body recolor + glasses gone + primitive head on neck. Scale OK (~2.8 m body).
- **Misleading checkpoint language:** “bind solved / animating” meant *skinned and attached*, not *locomotion sequences play*. Gun was already on the floor in `in-game-screen/screenshot_working_bind.png`.
- Pack: later copied to `release/pak69_aug12_dir.vpk` for DMM A/B.

### Phase 3 — Imported Dreamlight Sully head

- Source: `model_work/import_head/sully.glb` (full body + eyes).
- Pipeline that worked for **mesh placement**:
  1. `build_import_head.py` — bake armature-deformed mesh, cut head (token groups, w≥0.40), join eyes, seat at face center `(0, 3.361, 103)`, scale 1.632× to stock face height 20.69 in, 100% `head` weights.
  2. `export_sully_skinned.py` — parent with keep-transform, export FBX **with armature**.
  3. `make_clean_vmdl.py B --scale 1.0` + `compile_and_pack.ps1` (`bin_cs2` + `VtexPacker.exe`).
- Head textures: `import_head/textures/Image_0.png` / `Image_1.png` → `sully_textures/abrams_head_*`.
- **In-match:** face looks good; still a statue (same as Phase 2 for locomotion).

### Phase 4 — Try to hook AnimGraph2 without rewriting the model

All **failed** (still a statue):

| Attempt | Result |
|---------|--------|
| GameData `m_sAG2HeroPawnAnimGraph` / `m_sAG2UIAnimGraph` + `m_bUseAG2* = true` | Fields appear in compiled DATA; no walk |
| Same + `m_animGraph2Refs` / `m_vecNmSkeletonRefs` in GameData | Compiler added correct **RERL** IDs for graphs + `abrams.vnmskel`; pawn still did not animate |
| Source `AnimGraph2List` / `NmSkeletonList` in the vmdl | `bin_cs2`: Failed to allocate `AnimGraph2List` |
| Compile with `bin` or `bin_tools` | Schema abort (`ParticleFloatType_t`) |
| A/B install of Aug 12 primitive pack | Confirmed **same statue** — not a regression from the new head |

### Phase 5 — Agreed next plan (not started)

**Do not recompile Isolation B as the live hero.**

1. Host = stock compiled model: `model_work/abrams_backup.vmdl_c` (~8.6 MB, has AG2 + vnmskel).
2. Donor meshes = current Isolation B compile (face + recommended cut body).
3. Binary-graft / splice mesh blocks into the stock host (MVTX/MIDX/MDAT + CTRL counts/bounds + head bone remaps).
4. Pack spliced stock host as `models/heroes_wip/abrams/abrams.vmdl_c` + existing `sully_textures`.
5. Verify RERL still has the three stock graph/skel entries; body ~2.8 m; head on neck; then in-match walk test.

**Glasses catch:** stock **body** still has glasses geometry. Face-only splice brings glasses back. Recommended graft = **Sully face + Isolation B body** (head/glasses already cut).

---

## Issues and dead ends (do not repeat)

### Mesh / Blender

| Issue | Lesson |
|-------|--------|
| Texture paint on stock Abrams UVs | Face still Abrams + glasses |
| Voxel remesh whole head | Bowling-ball melt |
| Mesh-only FBX (no armature) | Unskinned giant teal slab in menu |
| Inch verts + meter scene + bad FBX scale/axes | ~100× scale (camera inside mesh) |
| Flatten world matrix into verts / bad parent | Breaks skin |
| `head.parent = arm` without keep_transform | Head at armature origin |
| Substring `"lip"` when deleting head verts | Hits `flip_a_page_*` book verts — use **token** match |
| Imported GLB bind pose vs deformed pose | Must bake **armature-deformed** mesh before cut; raw verts are wrong |

### Compile / packing

| Issue | Lesson |
|-------|--------|
| Full stock decompiled vmdl as CSDK source | Red wireframe explosion in first person |
| `bin` / `bin_tools` | Schema mismatch — use `bin_cs2` for mesh compile only |
| Live Deadlock DLLs mixed with CSDK | Missing `modeldoc_utils` |
| Source `*.vmat` in addon content | Compiler rebuilds and fails on missing PNGs |
| `dotnet run` after compile script | PATH wiped — call `VtexPacker.exe` directly |
| Orphan addon pak numbers | Skin sticks after DMM disable |

### Animation

| Issue | Lesson |
|-------|--------|
| Isolation B “bind worked” | Meant **skinned bind pose**, not locomotion |
| AnimInclude → `abrams_backup.vmdl` only | Not enough without a running AG2 graph on the model |
| GameData / RERL AG2 strings | Not sufficient to make the pawn run the graph |
| `bin_cs2` + AnimGraph2List | Cannot allocate class — cannot emit stock anim hooks |

---

## Key paths

| Path | Role |
|------|------|
| `CHECKPOINT.md` | Short resume for the next coding session |
| `model_work/import_head/sully.glb` | User-provided Sully mesh (local only) |
| `model_work/build_import_head.py` | Cut/seat imported head → `sully_cut.blend` |
| `model_work/export_sully_skinned.py` | Skinned FBX export (working mesh path) |
| `model_work/sully_export/sully_face.fbx` | Donor head FBX |
| `model_work/sully_export/abrams_body_nohead.fbx` | Donor body FBX (no head/glasses) |
| `model_work/abrams_backup.vmdl_c` | **Stock host** for next splice |
| `tools/Reduced_CSDK_12/.../abrams.vmdl_c` | Isolation B compile — **mesh donor only** |
| `release/pak69_dir.vpk` | Current Isolation B ship (good head, statue) |
| `release/pak69_aug12_dir.vpk` | Primitive-head A/B (also statue) |
| `sully_textures/` | Color maps + portraits packed into VPK |
| `in-game-screen/screenshot_aug-latest.png` | Imported head in-match (statue) |
| `in-game-screen/screenshot_working_bind.png` | Aug 12 “bind” shot (gun already on floor) |

Blender scenes (~800 MB) are **not** in git. Restore from GitHub Release `snapshot-pre-import-head` if needed:

- `sully_cut.blend` / `sully_skinned.blend`
- `.bak_pre_import` variants (primitive head era)

---

## Tools (local, not all in git)

- Blender 4.5 under `tools/blender-install/`
- Reduced CSDK 12 under `tools/Reduced_CSDK_12/` (mesh compile only going forward)
- Source2Viewer CLI: `tools/s2v-cli/Source2Viewer-CLI.exe`
- VPK packer: `tools/VtexPacker/`

---

## Install notes (for testing)

1. Deadlock Mod Manager: install **one** `*_dir.vpk` only.
2. Full game restart (not just disconnect).
3. If skins stick after disable, clear orphan `pak##` from `game/citadel/addons` into `disabled_vpks\`.

---

## For the next LLM

1. Read **this file** then **`CHECKPOINT.md`**.
2. Do **not** restart Isolation B recompiles to fix walk.
3. Implement **stock-host mesh splice** (face + recommended cut body).
4. Preserve stock AG2 / vnmskel on the host `vmdl_c`.
5. Do not put `sully.glb` in the public zip.
6. Verify in-match walk before calling it done.

### Open problem (one line)

**How do we replace Abrams’ head (and no-glasses body) while keeping the stock compiled model’s AnimGraph2/NmSkeleton locomotion intact, given `bin_cs2` cannot emit those nodes?**

Agreed answer to try: **don’t recompile the hero graph — splice meshes into stock `abrams.vmdl_c`.**
