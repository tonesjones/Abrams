# Checkpoint — Sully Abrams (2026-08-13, pre-import-head bind)

Resume file. Stock Deadlock `pak01_*` / `game\core` were never modified.

Git snapshot (private): https://github.com/tonesjones/Abrams  
Commit: `b3ceff6bc21fd8d654409a9b8e5c486a42f1179c` on `main`  
Blender scenes (~800 MB each) are **not** in git. They go on GitHub Release `snapshot-pre-import-head`.

---

## Status

**Bind is still solved.** User-tested in-match on 2026-08-12. That ship is untouched.

Screenshot (keep this; do not overwrite):

`C:\TestCode\Abrams\in-game-screen\screenshot_working_bind.png`

| Piece | Result |
|--------|--------|
| Body / coat / pants | Teal fur + purple spots, on the character, animating |
| Glasses | Gone |
| Live head | Primitive teal blob: tiny horn nubs, googly green eyes, two fangs |
| HUD portrait | Already good Sully card (leave it) |

**Head-bind work has not started.** User said stop and snapshot first.

Imported mesh (enough; do not hunt for more):

`C:\TestCode\Abrams\model_work\import_head\sully.glb` (5,843,120 bytes, 2026-08-13 8:28 PM)

Inspected in Blender 4.5:

- Full-body Dreamlight Valley Sully, not a head-only mesh
- Body `Object_82`: 5792 verts / 9734 tris, UVs, 76 Bip001 groups
- Eyes `Object_83`: 292 verts / 528 tris, material `sully_eyes.002`
- Textures: 3× 2048 maps in `model_work\import_head\textures\` (color, normal, extra)
- Their skeleton is discarded; we rebind to Abrams `head`
- Next work (when told): cut head at neck, scale to face center `(0, 3.36, 103)`, same skinned FBX path
- Local addon only. Do not put this mesh in `BlueSpot_Monster_Abrams.zip` / GameBanana copy

Portrait target (HUD, leave it):

`C:\TestCode\Abrams\sully_textures\bull_card_psd.png`

---

## Working ship (do not replace blindly)

`C:\TestCode\Abrams\release\pak69_dir.vpk` (29,527,586 bytes, 2026-08-12 8:08 PM)

Compiled model: `abrams.vmdl_c` = 1,521,352 bytes  
Inspected bounds: body ~2.8 m tall, Sully head at z≈2.64 m.

Fallback if a later head pass breaks the bind:

`C:\TestCode\Abrams\release\pak69_isolationA_dir.vpk`  
(stock 3D Abrams + Sully textures/portraits — glasses come back)

---

## Working pipeline (use this, nothing else)

1. Cut stock head/glasses off the body (token bone-name match, **not** substring `lip`).
2. Build / seat Sully head in inches at stock face center `(0, 3.36, 103)`.
3. Vertex groups: body keeps the imported Abrams groups; head is 100% `head`.
4. Parent to the **original unedited** armature with `matrix_parent_inverse` (keep world transform). Armature modifier on. **Never** `head.parent = arm` without keep_transform.
5. Scene units: imperial inches, `scale_length = 0.0254`.
6. Export FBX **with armature** (`object_types={'ARMATURE','MESH'}`, `add_leaf_bones=False`, `use_armature_deform_only=True`, default axes `-Z` / `Y`, `apply_unit_scale=True`, `FBX_SCALE_UNITS`).
7. Clean community-shaped vmdl via `make_clean_vmdl.py B --scale 1.0` (stock gun/book DMX + custom body/face FBX, `AnimIncludeModel` → `abrams_backup.vmdl`, **no** NmSkeleton / AnimGraph2 / compiled Skeleton dump).
8. Compile with **`bin_cs2`** only. Pack with `VtexPacker.exe` (not `dotnet run` — PATH is wiped by the compiler script).

Scripts for that path:

| Script | Role |
|--------|------|
| `model_work\export_sully_skinned.py` | Rebind existing cut blend + export skinned FBX (the one that worked) |
| `model_work\export_sully_meshonly.py` | Builds the cut + head into `sully_cut.blend` (then run skinned export) |
| `model_work\make_clean_vmdl.py` | Isolation A/B vmdl |
| `model_work\compile_and_pack.ps1` | `bin_cs2` compile + pack |
| `model_work\inspect_import_head.py` | Read-only inspect of `import_head\sully.glb` |

Working Blender files:

- `model_work\sully_export\sully_skinned.blend` — last successful bind/export
- `model_work\sully_export\sully_cut.blend` — cut body + primitive head
- Face center after ×39.37: `(-0, 3.361, 102.962)`

---

## Git snapshot — what is / is not on GitHub

On `main` (private repo):

- `CHECKPOINT.md`, scripts, working + fallback VPKs, textures, portraits, in-game shot
- `model_work\import_head\sully.glb` + inspect previews/textures
- Packer source under `tools\VtexPacker\`, `tools\deadmod_src\`

Not in git (too big or reinstallable):

- `*.blend` / `*.blend1` — Release `snapshot-pre-import-head`
- `tools\Reduced_CSDK_12\`, Blender install, compiler copies
- Stock `abrams.gltf` / `vmdl_src\` extracts, leftover `disabled_vpks\`

Restore if the next bind pass wrecks the live files:

1. `git checkout main -- release/pak69_dir.vpk CHECKPOINT.md`
2. Re-download the two `.blend` files from the Release into `model_work\sully_export\`
3. Install only `release\pak69_dir.vpk`, full restart

---

## Mistakes — do not repeat

### Bind / compile (solved)

| Mistake | What happened |
|---------|----------------|
| Texture-only paint on stock Abrams UVs | Face still read as Abrams + glasses. Ruled out. |
| Voxel remesh of the whole head | Features melted into a bowling ball. |
| Mesh-only FBX (`object_types={'MESH'}`, no armature) | No skin clusters. Mesh sat in the world as a giant teal slab in the menu. |
| Inch numbers + Blender meters + `FBX_SCALE_NONE` + `axis_up='Z'` | Compiled ~100× too big (2.54×39.37). Camera inside the mesh. |
| Flatten `matrix_world` into verts + identity + unparent | Destroyed the armature relationship. |
| `head.parent = arm` without keep_transform | Yanked the head to the armature origin. |
| 14k-line **stock decompiled** vmdl as source (LODs, leftover weight lists, NmSkeleton, AnimGraph2) | Red wireframe explosion in first person. |
| Substring match `"lip"` when deleting head verts | Hits `flip_a_page_*` and deletes book/page verts. Use **token** match. |
| Compile with `bin` / `bin_tools` | `ParticleFloatType_t` schema mismatch. Use `bin_cs2`. |
| Live Deadlock DLLs mixed with CSDK | Missing `modeldoc_utils` (126/127). |
| DepotDownloader / Steam QR | Not needed. Do not redo. |
| Write into Steam `pak01_*` or `game\core` | Forbidden. Addon VPK only. |
| Leave source `*.vmat` in the addon content folder | Compiler tries to rebuild them and fails on missing PNGs. |
| `dotnet run` after compile script sets PATH to `bin_cs2` | `dotnet` not found. Call `tools\VtexPacker\bin\Release\net8.0\VtexPacker.exe`. |
| Portrait box-project / CLIP mix on the fur shader | Black portrait background painted the snout black. |
| Orphan `pak08` / `pak69` / `pak90` in `addons` | Skin stayed on after DMM disable. DMM does not remove orphans. |
| Download / pack official-game Sulley into a public zip | Local addon only. Sketchfab CC BY does not license a Dreamlight Valley rip. |

### Head quality (still open)

The live head is joined spheres. The imported GLB is the next shape source. Do **not** voxel-remesh it. Do **not** invent a new compile path.

---

## Next session — do this

1. Read this file. Do not “try a new compile path.”
2. Only after the user says to start: cut the imported Sulley **head** off the body, seat at `(0, 3.36, 103)`, 100% `head` weights, keep-transform parent.
3. Re-export with `export_sully_skinned.py` (or the same FBX flags). Do **not** go back to mesh-only.
4. `make_clean_vmdl.py B --scale 1.0` then `compile_and_pack.ps1`.
5. Before asking the user to install: inspect compiled glTF bounds (body ~2.8 m, head on the neck). If body is ~280 m, scale is broken again — do not ship.
6. User installs only `release\pak69_dir.vpk`, full restart. Leave HUD portraits alone.

---

## Verify compile scale (mandatory before ship)

```
blender --background --python model_work\inspect_compiled.py
```

Pass: body size z ≈ 2.8, head center z ≈ 2.6.  
Fail: body size z ≈ 280 (100×) or groups-less mesh-only slab.

---

## Rollback

Disable/remove only the Sully addon VPK in DMM. No Steam verify. If leftover `pak08`/`pak69`/`pak90` reappear in `addons`, move them to `disabled_vpks\`.
