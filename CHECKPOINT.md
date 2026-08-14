# Checkpoint — Sully Abrams (2026-08-14, stock-host splice)

Resume file. Method record is **`README.md`** — read that before touching compile or AG2.

Stock Deadlock `pak01_*` / `game\core` were never modified.

Git: https://github.com/tonesjones/Abrams (`main`)

---

## Status

**Ship:** `release\pak69_stockhost_dir.vpk`

Stock compiled Abrams is the host. Isolation B donated only body + face mesh blocks. Stock ANIM / AG2 / `vnmskel` stayed on the file.

| Piece | Result |
|--------|--------|
| Head | Sully, 2577 verts, 100% `head`, center z ≈ 2.62 m |
| Body | Cut Isolation B body, 2.81 m, no glasses |
| HUD | Leave portraits alone |
| Locomotion | Stock sequences + graph refs preserved. User signed off. |

Rebuild: `python tools\SpliceHost\splice.py splice` then `VtexPacker.exe` (see README).

Do **not** recompile Isolation B to change walk.

---

## Paths

| Path | What |
|------|------|
| `release\pak69_stockhost_dir.vpk` | Install this |
| `release\pak69_dir.vpk` | Isolation B statue rollback |
| `model_work\abrams_backup.vmdl_c` | Stock host — do not overwrite |
| `model_work\abrams_spliced.vmdl_c` | Last splice output |
| CSDK `.../sully_abrams/.../abrams.vmdl_c` | Mesh donor only |
| `model_work\import_head\sully.glb` | Local mesh — not for GameBanana |

---

## Rollback

Disable/remove only the Sully addon VPK. No Steam verify. Orphans `pak08`/`pak69`/`pak90` in `addons` → `disabled_vpks\`.
