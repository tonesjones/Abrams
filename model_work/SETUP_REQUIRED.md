# Model-swap setup (non-destructive)

Stock Deadlock files under Steam are **never modified**. All tools and work go under `C:\TestCode\Abrams\` or a separate CSDK folder you choose. Rollback = remove/disable addon VPKs only.

## Already done (safe)

- Abrams exported read-only to:
  - `C:\TestCode\Abrams\model_work\abrams_export\models\heroes_wip\abrams\abrams.gltf`
  - (plus textures / physics glTF)
- Existing body recolor + Sully portraits remain in `sully_textures\` / `release\`

## You need to install (Phase 0 blockers)

This environment could not install packages or download CSDK automatically. Please install both:

### 1) Blender

```powershell
winget install BlenderFoundation.Blender.LTS.4.5
```

Or download from https://www.blender.org/

### 2) Reduced CSDK 12 (compile tools)

1. Open: https://deadlockmodding.pages.dev/modding-tools/csdk-12  
2. Download **Reduced CSDK 12** (Google Drive link on that page).  
3. Extract to something like:
   - `C:\TestCode\Abrams\tools\Reduced_CSDK_12\`  
   **Not** inside your Steam Deadlock install.  
4. Run `csdkcfg.exe` once (Steam must be running).  
5. Create a new addon, e.g. `sully_abrams` (lowercase, no spaces).

Confirm compiler exists:

`C:\TestCode\Abrams\tools\Reduced_CSDK_12\game\bin_tools\win64\resourcecompiler.exe`

(or similar path under the extracted CSDK)

## After both are installed

Tell me “Blender + CSDK ready” (and the CSDK path if different). Then we continue Phase 2:

1. Open `abrams.gltf` in Blender  
2. Build/bind a Sully-like head (no glasses) to Abrams bones  
3. Compile via CSDK into an **addon-only** VPK  
4. Install only under `Deadlock\game\citadel\addons\`

## Rollback anytime

- Deadlock Mod Manager → disable/remove the Sully local mod  
- Or delete only `addons\pak##_dir.vpk` that DMM assigned  
- Game returns to stock + your other mods; no Steam verify required
