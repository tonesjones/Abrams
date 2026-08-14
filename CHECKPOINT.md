# Checkpoint — Sully Abrams (2026-08-14, statue confirmed; next = stock-host splice)

Resume file. Stock Deadlock `pak01_*` / `game\core` were never modified.

Git snapshot (private): https://github.com/tonesjones/Abrams  
Earlier snapshot commit: `b3ceff6bc21fd8d654409a9b8e5c486a42f1179c` on `main`  
Blender scenes (~800 MB each) are **not** in git. They go on GitHub Release `snapshot-pre-import-head`.

---

## Status

**Sully head looks good in-match.** Imported GLB head is seated, textured, on the neck.

**Locomotion is a statue.** Walk / jump / slide / third-person gun do not play. First-person gun still draws. Body is skinned (not a world slab, not 100×). Confirmed on both:

- Current Isolation B pack (`release\pak69_dir.vpk`)
- Aug 12 primitive-head A/B (`release\pak69_aug12_dir.vpk`)

**Root cause:** Isolation B is compiled with `bin_cs2`. That compiler **cannot allocate** `AnimGraph2List` / `NmSkeletonList`. Stock Abrams walk lives in those compiled nodes plus `abrams.vnmskel` and `hero.vnmgraph+abrams.vnmgraph`. Recompiling the whole hero through CSDK will not hook walk.

Tried and **failed** (do not redo):

- GameData `m_sAG2HeroPawnAnimGraph` strings only
- Same plus `m_animGraph2Refs` / `m_vecNmSkeletonRefs` inside GameData (RERL *did* list the three stock IDs; pawn still did not run the graph)
- Adding source `AnimGraph2List` — `Failed to allocate an instance of class 'AnimGraph2List'`
- `bin` / `bin_tools` — `ParticleFloatType_t` schema abort

**Next work (agreed, not started):** do **not** run `make_clean_vmdl.py` / `compile_and_pack.ps1` on the hero. Keep **stock compiled** `abrams.vmdl_c` as the host (`model_work\abrams_backup.vmdl_c`). Graft the already-built Sully head into it. Recommended: also graft Isolation B’s already-cut body (no glasses). Glasses live on the stock body; a face-only splice brings glasses back.

Head and body meshes are done. Remaining work is a binary graft, not Blender.

In-match shots (do not overwrite the Aug 12 one):

- `in-game-screen\screenshot_working_bind.png` — Aug 12, primitive head, gun already on the floor
- `in-game-screen\screenshot_aug-latest.png` — imported head, statue + gun on the floor

Blender seat preview:

`model_work\sully_export\import_head_preview.png`

| Piece | Result |
|--------|--------|
| Body / coat / pants | Teal fur + purple spots. Isolation B body FBX, glasses cut |
| Glasses | Gone on Isolation B body; will return if we splice face onto **stock** body |
| Live head | Imported Sully + eyes, 2599 verts, 100% `head`, center `(0, 3.361, 103)` |
| HUD portrait | Good Sully card — leave it |
| Walk / jump / slide | Broken on every Isolation B compile |

Imported mesh (local only, not GameBanana):

`C:\TestCode\Abrams\model_work\import_head\sully.glb`

- Full-body Dreamlight Valley Sully. Their skeleton is discarded; rebound to Abrams `head`
- Cut at neck (token head/neck/face groups, w>=0.40), joined `Object_83` eyes
- Scaled 1.632× to stock face height 20.69 in
- Color/normal copied over `sully_textures\abrams_head_*`

Portrait target (HUD, leave it):

`C:\TestCode\Abrams\sully_textures\bull_card_psd.png`

---

## VPKs and hosts

| Path | What |
|------|------|
| `release\pak69_dir.vpk` | Latest Isolation B: imported head + GameData AG2 refs + RERL graph/skel. **Still a statue.** |
| `release\pak69_aug12_dir.vpk` | Aug 12 primitive-head A/B (real `.vpk` name). **Also a statue.** Use this for DMM A/B, not the `.bak` filename. |
| `release\pak69_dir.vpk.bak_pre_import_head` | Same bytes as Aug 12. DMM rejects this name. |
| `release\pak69_imported_head_static_dir.vpk` | Imported head before AG2 GameData patch. Statue. |
| `release\pak69_isolationA_dir.vpk` | Stock 3D + Sully textures. Glasses come back. Same CSDK path — **not** a walk fix. |
| `model_work\abrams_backup.vmdl_c` | **Stock compiled Abrams. Host for the next splice.** ~8.6 MB. Has AG2 + vnmskel. |
| CSDK compiled Isolation B | `tools\Reduced_CSDK_12\game\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.vmdl_c` — **donor** of face/body mesh blocks only |

Inspected Isolation B bounds (pass for scale, not for anims): body size z ≈ 2.81, head center z ≈ 2.62.

---

## Next session — do this

1. Read this file. Do **not** recompile Isolation B to “fix walk.”
2. Splice Sully face (+ recommended cut body) into **stock** `model_work\abrams_backup.vmdl_c`.
3. Keep stock AnimGraph2 / vnmskel / gun / book / attachments.
4. Pack a new `*_dir.vpk` whose `abrams.vmdl_c` is the spliced stock host + current `sully_textures`. Do **not** ship the 1.4 MB Isolation B model as the hero.
5. Before asking the user to install: body ~2.8 m, head on the neck, RERL still has the three stock graph/skel refs.
6. User installs only that new VPK, full restart. Leave HUD portraits alone.

Splice recipe:

1. Host = `model_work\abrams_backup.vmdl_c`
2. Donor meshes from current Isolation B compile (CTRL `embedded_meshes` + vert counts)
3. Replace stock face (and body if keeping no-glasses) MVTX/MIDX/MDAT
4. Update CTRL counts/bounds; head remap = 100% `head`
5. Pack; confirm AG2/vnmskel RERL still present

---

## Working pipeline (meshes only — already done)

Do not rerun this to fix walk. Kept so the donor FBXs can be rebuilt if a blend is lost.

1. Cut stock head/glasses off the body (token bone-name match, **not** substring `lip`).
2. Seat Sully head in inches at `(0, 3.36, 103)`, 100% `head`.
3. Parent to the **original unedited** armature with `matrix_parent_inverse`. **Never** `head.parent = arm` without keep_transform.
4. Export FBX **with armature** (`object_types={'ARMATURE','MESH'}`, `add_leaf_bones=False`, `use_armature_deform_only=True`, axes `-Z` / `Y`, `apply_unit_scale=True`, `FBX_SCALE_UNITS`).
5. Isolation B compile is **only** a mesh donor now. Do not ship that `vmdl_c` as the live hero.

Scripts:

| Script | Role |
|--------|------|
| `model_work\build_import_head.py` | Cut imported GLB head, seat at FACE_CENTER, write `sully_cut.blend` |
| `model_work\export_sully_skinned.py` | Rebind cut blend + export skinned FBX |
| `model_work\export_sully_meshonly.py` | Old primitive-head builder — **do not rerun** |
| `model_work\make_clean_vmdl.py` | Isolation A/B vmdl — **do not use to ship walk** |
| `model_work\compile_and_pack.ps1` | `bin_cs2` compile + pack — **do not use to ship walk** |

Working Blender files:

- `model_work\sully_export\sully_skinned.blend` — last skinned export (imported head)
- `model_work\sully_export\sully_cut.blend` — cut body + imported head
- `model_work\sully_export\sully_cut.blend.bak_pre_import` — cut body + primitive head
- Face center after ×39.37: `(-0, 3.361, 102.962)`

---

## Git snapshot — what is / is not on GitHub

On `main` (private repo):

- `CHECKPOINT.md`, scripts, VPKs, textures, portraits, in-game shots
- `model_work\import_head\sully.glb` + inspect previews/textures
- Packer source under `tools\VtexPacker\`, `tools\deadmod_src\`

Not in git (too big or reinstallable):

- `*.blend` / `*.blend1` — Release `snapshot-pre-import-head`
- `tools\Reduced_CSDK_12\`, Blender install, compiler copies
- Stock `abrams.gltf` / `vmdl_src\` extracts, leftover `disabled_vpks\`

---

## Mistakes — do not repeat

### Bind / compile

| Mistake | What happened |
|---------|----------------|
| Texture-only paint on stock Abrams UVs | Face still read as Abrams + glasses. |
| Voxel remesh of the whole head | Features melted into a bowling ball. |
| Mesh-only FBX (`object_types={'MESH'}`, no armature) | Giant unskinned teal slab. |
| Inch numbers + meters + `FBX_SCALE_NONE` + `axis_up='Z'` | Compiled ~100× too big. |
| Flatten `matrix_world` into verts + unparent | Destroyed the armature relationship. |
| `head.parent = arm` without keep_transform | Head yanked to armature origin. |
| 14k-line **stock decompiled** vmdl as CSDK source | Red wireframe explosion in first person. |
| Substring match `"lip"` when deleting head verts | Hits `flip_a_page_*`. Use **token** match. |
| Compile with `bin` / `bin_tools` | `ParticleFloatType_t` schema mismatch. |
| Live Deadlock DLLs mixed with CSDK | Missing `modeldoc_utils` (126/127). |
| Write into Steam `pak01_*` or `game\core` | Forbidden. Addon VPK only. |
| Source `*.vmat` in the addon content folder | Compiler rebuilds them and fails. |
| `dotnet run` after compile script wipes PATH | Call `tools\VtexPacker\bin\Release\net8.0\VtexPacker.exe`. |
| Orphan `pak08` / `pak69` / `pak90` in `addons` | DMM does not remove orphans. |
| Pack Dreamlight Valley Sully in a public zip | Local addon only. |
| Isolation B recompile to fix walk | Statue. `bin_cs2` cannot emit AG2/NmSkeleton. |
| GameData / RERL AG2 strings only | RERL IDs matched stock; pawn still a statue. |
| Source `AnimGraph2List` in the vmdl | Allocate failure. |
| DMM on `*.bak_pre_import_head` | Not a `.vpk`. Use `pak69_aug12_dir.vpk`. |
| Face-only splice into stock without handling glasses | Stock body still has glasses. |
| `export_sully_meshonly.py` | Rebuilds the primitive blob head. |

---

## Verify scale (if a donor mesh is rebuilt)

```
blender --background --python model_work\inspect_compiled.py
```

Pass: body size z ≈ 2.8, head center z ≈ 2.6.  
Fail: body size z ≈ 280 (100×) or groups-less mesh-only slab.

After a stock-host splice, also confirm RERL still lists:

- `animgraphs/animgraph2/hero/hero.vnmgraph+abrams.vnmgraph`
- `animgraphs/animgraph2/hero/hero_ui.vnmgraph+abrams.vnmgraph`
- `models/heroes_wip/abrams/abrams.vnmskel`

---

## Rollback

Disable/remove only the Sully addon VPK in DMM. No Steam verify. If leftover `pak08`/`pak69`/`pak90` reappear in `addons`, move them to `disabled_vpks\`.
