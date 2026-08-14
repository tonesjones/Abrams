# Blue Spot Monster Abrams

A **model-swap + texture recolor + portrait** skin for **Abrams** in *Deadlock*, themed as a big blue-furred monster with purple spots (Sulley / Monsters Inc. inspired). The live head is a custom mesh (stock face/glasses removed), not a paint-over of Abrams.

## What’s included

| Asset | Change |
|--------|--------|
| Head / coat / upper / lower body color maps | Cyan-blue “fur” recolor + purple spots |
| Teeth / gun color maps | Matching palette tweaks |
| Hero UI portraits | Custom blue-monster card art (main, gloat, critical, sm, vertical) |

Clothes, gun, book, and animations stay stock Abrams. The **head mesh is replaced** (no glasses). The current head is a stylized monster blockout (teal fur, spots, green eyes, snout, horns, fangs), not a film-accurate sculpt.

## Install (manual)

1. Open your Deadlock folder:  
   `...\Steam\steamapps\common\Deadlock\game\citadel\addons\`
2. If `addons` doesn’t exist, create it (or use Deadlock Mod Manager once).
3. Drop **`pak69_dir.vpk`** into `addons`.
4. If another mod already uses `pak69`, rename to any free `pak##_dir.vpk` (e.g. `pak70_dir.vpk`).
5. Launch Deadlock and pick Abrams.

### Using Deadlock Mod Manager

Import/install the zip or the VPK the same way you install other GameBanana skins.

## Files for GameBanana upload

- **Mod file:** `BlueSpot_Monster_Abrams.zip` (contains `pak69_dir.vpk`)
- **Preview images:** `showcase_portrait.jpg`, `showcase_card.jpg`, `showcase_critical.jpg`, `preview_ui_card.png`

Suggested GameBanana fields:

- **Title:** Blue Spot Monster Abrams  
- **Category:** Skins → Abrams  
- **Description:** Fan-inspired blue fur + purple spot recolor of Abrams with custom select portraits. Texture/portrait mod only.

## Credits / notes

- Base game assets © Valve.
- Character inspiration: classic animated blue-spotted monster design (fan skin, not official).
- Texture packing approach adapted from community tools (DeadMod-style PNG-in-vtex_c + ValvePak).
- Built with Source2Viewer (ValveResourceFormat) for extract/verify.

## Rebuild (optional)

From the project tools:

```powershell
python scripts\make_sully_textures.py
python scripts\make_portraits.py
dotnet run --project tools\VtexPacker -c Release -- sully_textures release\pak69_dir.vpk
```

## Disclaimer

Fan-made, non-commercial. Not affiliated with Valve or Disney/Pixar. GameBanana may take down trademarked character likenesses; use “inspired by” wording if needed.
