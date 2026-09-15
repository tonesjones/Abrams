"""
Stock-host mesh splice — the method that actually walks.

Host = stock compiled abrams.vmdl_c (ANIM + AG2 + vnmskel).
Donor = Isolation B compile (body + face mesh blocks only).
Do not recompile the live hero. Do not patch GameData AG2 strings.

See README.md ("The method that works").
"""

from __future__ import annotations

import argparse
import copy
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resource_io import Block, kv3_read_block, kv3_write_block, read_resource, write_resource

ROOT = Path(r"C:\TestCode\Abrams")
HOST_DEFAULT = ROOT / r"model_work\abrams_backup.vmdl_c"
DONOR_DEFAULT = (
    ROOT
    / r"tools\Reduced_CSDK_12\game\citadel_addons\sulley_fullbody\models\heroes_wip\abrams\sulley_donor.vmdl_c"
)
OUT_DEFAULT = ROOT / r"model_work\abrams_spliced.vmdl_c"

BODY_HOST_NAMES = {
    "abrams_model",
    "abrams_model_lod1",
    "abrams_model_lod2",
    "abrams_model_lod3",
}
FACE_HOST_NAMES = {
    "abrams_face_model",
    "abrams_face_model_lod1",
    "abrams_face_model_lod2",
    "abrams_face_model_lod3",
}

REQUIRED_RERL = [
    "animgraphs/animgraph2/hero/hero.vnmgraph+abrams.vnmgraph",
    "animgraphs/animgraph2/hero/hero_ui.vnmgraph+abrams.vnmgraph",
    "models/heroes_wip/abrams/abrams.vnmskel",
]


def norm_bone(name: str) -> str:
    if name.startswith("$cloth_"):
        return "cloth_" + name[7:]
    if name.startswith("_cloth_"):
        return "cloth_" + name[7:]
    return name


def kv_of(blocks: list[Block], typ: bytes):
    for b in blocks:
        if b.typ == typ:
            return kv3_read_block(b.data)
    raise SystemExit(f"missing block {typ!r}")


def remap_slice(table, starts, mesh_index: int):
    start = int(starts[mesh_index])
    end = int(starts[mesh_index + 1]) if mesh_index + 1 < len(starts) else len(table)
    return [int(x) for x in table[start:end]]


def translate_remaps(donor_indices, donor_names, host_map):
    out = []
    for idx in donor_indices:
        name = donor_names[int(idx)]
        key = norm_bone(name)
        if key not in host_map:
            raise SystemExit(f"cannot map donor bone {name!r}")
        out.append(host_map[key])
    return out


def copy_donor_mesh_blocks(host_blocks: list[Block], donor_blocks: list[Block], donor_ctrl_mesh: dict) -> dict:
    """Append donor MVTX/MIDX/MDAT used by this CTRL mesh. Return remapped CTRL mesh dict."""
    cloned = copy.deepcopy(donor_ctrl_mesh)
    index_map: dict[int, int] = {}

    def take(old_index: int) -> int:
        old_index = int(old_index)
        if old_index in index_map:
            return index_map[old_index]
        if old_index < 0 or old_index >= len(donor_blocks):
            raise SystemExit(f"donor block index out of range: {old_index}")
        src = donor_blocks[old_index]
        if src.typ not in (b"MVTX", b"MIDX", b"MDAT"):
            raise SystemExit(f"refusing to copy donor block {src.typ!r} index {old_index}")
        new_index = len(host_blocks)
        host_blocks.append(Block(src.typ, src.data))
        index_map[old_index] = new_index
        return new_index

    cloned["m_nDataBlock"] = take(cloned["m_nDataBlock"])
    for buf in cloned.get("m_vertexBuffers", []):
        buf["m_nBlockIndex"] = take(buf["m_nBlockIndex"])
    for buf in cloned.get("m_indexBuffers", []):
        buf["m_nBlockIndex"] = take(buf["m_nBlockIndex"])
    for buf in cloned.get("m_toolsBuffers", []):
        buf["m_nBlockIndex"] = take(buf["m_nBlockIndex"])
    return cloned


def apply_donor_layout(host_mesh: dict, donor_layout: dict) -> None:
    """Keep host name/index; replace buffer layout and MDAT pointer."""
    host_mesh["m_nDataBlock"] = donor_layout["m_nDataBlock"]
    host_mesh["m_vertexBuffers"] = copy.deepcopy(donor_layout["m_vertexBuffers"])
    host_mesh["m_indexBuffers"] = copy.deepcopy(donor_layout["m_indexBuffers"])
    host_mesh["m_toolsBuffers"] = copy.deepcopy(donor_layout.get("m_toolsBuffers", []))
    if "m_nMorphBlock" in donor_layout:
        host_mesh["m_nMorphBlock"] = donor_layout["m_nMorphBlock"]
    if "m_nVBIBBlock" in donor_layout:
        host_mesh["m_nVBIBBlock"] = donor_layout["m_nVBIBBlock"]
    if "m_nToolsVBBlock" in donor_layout:
        host_mesh["m_nToolsVBBlock"] = donor_layout["m_nToolsVBBlock"]


def rebuild_remaps(host_data: dict, donor_data: dict, host_names: list[str], donor_names: list[str]) -> None:
    host_map = {norm_bone(n): i for i, n in enumerate(host_names)}
    h_table = [int(x) for x in host_data["m_remappingTable"]]
    h_starts = [int(x) for x in host_data["m_remappingTableStarts"]]
    d_table = donor_data["m_remappingTable"]
    d_starts = donor_data["m_remappingTableStarts"]

    body_remaps = translate_remaps(remap_slice(d_table, d_starts, 0), donor_names, host_map)
    face_remaps = translate_remaps(remap_slice(d_table, d_starts, 1), donor_names, host_map)

    # mesh index 0/5/9/13 = body family, 1/4/8/12 = face family
    replacements = {
        0: body_remaps,
        5: body_remaps,
        9: body_remaps,
        13: body_remaps,
        1: face_remaps,
        4: face_remaps,
        8: face_remaps,
        12: face_remaps,
    }

    new_table: list[int] = []
    new_starts: list[int] = []
    for mesh_i in range(len(h_starts)):
        new_starts.append(len(new_table))
        if mesh_i in replacements:
            new_table.extend(replacements[mesh_i])
        else:
            new_table.extend(remap_slice(h_table, h_starts, mesh_i))
    host_data["m_remappingTable"] = new_table
    host_data["m_remappingTableStarts"] = new_starts
    print(f"remaps: body={len(body_remaps)} face={len(face_remaps)} total={len(new_table)} (was {len(h_table)})")
    print(f"  face bones: {[host_names[i] for i in face_remaps]}")


def rerl_names(blocks: list[Block]) -> list[str]:
    for b in blocks:
        if b.typ != b"RERL":
            continue
        # ResourceExtRefList: uint32 count, then entries of id(u64)+name offset, then string table.
        # VRF dump is easier via strings.
        names = []
        # strings are null-terminated utf8 after a small header
        i = 0
        data = b.data
        while i < len(data):
            # scan for printable paths
            i += 1
        text = data.split(b"\x00")
        for part in text:
            try:
                s = part.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if "/" in s and len(s) > 8:
                names.append(s)
        return names
    return []


def apply_camera_overrides(
    host_data: dict,
    *,
    side_offset: float | None = None,
    back_offset: float | None = None,
    aiming_back_offset: float | None = None,
) -> None:
    """Apply optional camera-clearance settings without changing the default build."""
    overrides = {
        "m_flCameraSideOffset": side_offset,
        "m_flCameraBackOffset": back_offset,
        "m_flCameraBackOffsetAiming": aiming_back_offset,
    }
    requested = {key: value for key, value in overrides.items() if value is not None}
    if not requested:
        return

    model_info = host_data.get("m_modelInfo")
    if not isinstance(model_info, dict) or not isinstance(model_info.get("m_keyValueText"), str):
        raise SystemExit("host DATA is missing m_modelInfo.m_keyValueText")
    text = model_info["m_keyValueText"]
    if "CitadelCameraSettings_t" not in text:
        raise SystemExit("host model keyvalues are missing CitadelCameraSettings_t")
    for key, value in requested.items():
        pattern = rf"({re.escape(key)}\s*=\s*)(-?\d+(?:\.\d+)?)"
        match = re.search(pattern, text)
        if match is None:
            raise SystemExit(f"host camera settings are missing {key}")
        old = float(match.group(2))
        replacement = rf"\g<1>{float(value):.1f}"
        text, count = re.subn(pattern, replacement, text, count=1)
        if count != 1:
            raise SystemExit(f"expected one camera setting for {key}, found {count}")
        print(f"camera {key}: {old} -> {float(value):.1f}")
    model_info["m_keyValueText"] = text


def read_camera_settings(data: dict) -> dict[str, float | None]:
    text = data.get("m_modelInfo", {}).get("m_keyValueText", "")
    keys = (
        "m_flCameraSideOffset",
        "m_flCameraBackOffset",
        "m_flCameraBackOffsetAiming",
        "m_flCameraHeightStanding",
    )
    values: dict[str, float | None] = {}
    for key in keys:
        match = re.search(rf"{re.escape(key)}\s*=\s*(-?\d+(?:\.\d+)?)", text)
        values[key] = float(match.group(1)) if match else None
    return values


def splice(
    host_path: Path,
    donor_path: Path,
    out_path: Path,
    *,
    camera_side_offset: float | None = None,
    camera_back_offset: float | None = None,
    camera_aiming_back_offset: float | None = None,
) -> None:
    _hdr, ver, host_blocks = read_resource(host_path)
    _dh, _dv, donor_blocks = read_resource(donor_path)

    host_ctrl_file = kv_of(host_blocks, b"CTRL")
    donor_ctrl_file = kv_of(donor_blocks, b"CTRL")
    host_data_file = kv_of(host_blocks, b"DATA")
    donor_data_file = kv_of(donor_blocks, b"DATA")
    host_ctrl = host_ctrl_file.value
    donor_ctrl = donor_ctrl_file.value
    host_data = host_data_file.value
    donor_data = donor_data_file.value

    donor_meshes = {m["m_Name"]: m for m in donor_ctrl["embedded_meshes"]}
    if "body" not in donor_meshes or "face" not in donor_meshes:
        raise SystemExit(f"donor meshes: {list(donor_meshes)}")

    body_layout = copy_donor_mesh_blocks(host_blocks, donor_blocks, donor_meshes["body"])
    face_layout = copy_donor_mesh_blocks(host_blocks, donor_blocks, donor_meshes["face"])

    for mesh in host_ctrl["embedded_meshes"]:
        name = mesh["m_Name"]
        if name in BODY_HOST_NAMES:
            apply_donor_layout(mesh, body_layout)
            print(f"CTRL {name} -> donor body mdat={mesh['m_nDataBlock']}")
        elif name in FACE_HOST_NAMES:
            apply_donor_layout(mesh, face_layout)
            print(f"CTRL {name} -> donor face mdat={mesh['m_nDataBlock']}")

    host_names = list(host_data["m_modelSkeleton"]["m_boneName"])
    donor_names = list(donor_data["m_modelSkeleton"]["m_boneName"])
    rebuild_remaps(host_data, donor_data, host_names, donor_names)
    apply_camera_overrides(
        host_data,
        side_offset=camera_side_offset,
        back_offset=camera_back_offset,
        aiming_back_offset=camera_aiming_back_offset,
    )

    # write CTRL + DATA back
    for i, b in enumerate(host_blocks):
        if b.typ == b"CTRL":
            host_blocks[i] = Block(b"CTRL", kv3_write_block(host_ctrl))
        elif b.typ == b"DATA":
            host_blocks[i] = Block(b"DATA", kv3_write_block(host_data))

    write_resource(out_path, ver, host_blocks)
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes) blocks={len(host_blocks)}")

    # verify reload
    _h, _v, check = read_resource(out_path)
    names = rerl_names(check)
    print("RERL paths:")
    for n in names:
        mark = "OK" if any(req in n for req in REQUIRED_RERL) else "  "
        print(f"  {mark} {n}")
    missing = [r for r in REQUIRED_RERL if not any(r in n for n in names)]
    if missing:
        raise SystemExit(f"missing RERL: {missing}")
    ctrl = kv_of(check, b"CTRL").value
    data = kv_of(check, b"DATA").value
    print("reload meshes:", [m["m_Name"] for m in ctrl["embedded_meshes"]])
    print("reload remaps", len(data["m_remappingTable"]), "starts", list(data["m_remappingTableStarts"]))
    ag2 = data.get("m_animGraph2Refs")
    print("AG2 refs present:", ag2 is not None, "count", len(ag2) if ag2 else 0)
    print("NmSkeleton refs:", data.get("m_vecNmSkeletonRefs") is not None)
    print("camera settings:", read_camera_settings(data))


def roundtrip_kv(host_path: Path, out_path: Path) -> None:
    """Rewrite CTRL+DATA as VKV3 with no semantic change (sanity)."""
    _hdr, ver, blocks = read_resource(host_path)
    for i, b in enumerate(blocks):
        if b.typ in (b"CTRL", b"DATA"):
            parsed = kv3_read_block(b.data)
            blocks[i] = Block(b.typ, kv3_write_block(parsed.value))
            print(f"rewrote {b.typ.decode()} {len(b.data)} -> {len(blocks[i].data)}")
    write_resource(out_path, ver, blocks)
    print(f"wrote {out_path} ({out_path.stat().st_size})")


def inspect(path: Path) -> None:
    _hdr, ver, blocks = read_resource(path)
    print(f"{path} ver={ver} blocks={len(blocks)} size={path.stat().st_size}")
    for i, b in enumerate(blocks):
        print(f"  [{i:3}] {b.typ.decode('latin1')} {len(b.data)}")
    data = kv_of(blocks, b"DATA").value
    print("DATA keys", list(data.keys()))
    print("m_animGraph2Refs", data.get("m_animGraph2Refs"))
    print("m_vecNmSkeletonRefs", data.get("m_vecNmSkeletonRefs"))
    print("remap starts", data.get("m_remappingTableStarts"))
    ctrl = kv_of(blocks, b"CTRL").value
    for m in ctrl["embedded_meshes"]:
        vbs = m.get("m_vertexBuffers", [])
        print(
            f"  {m['m_Name']}: mdat={m['m_nDataBlock']} vbs="
            f"{[(vb.get('m_nBlockIndex'), vb.get('m_nElementCount')) for vb in vbs]}"
        )
    print("RERL", rerl_names(blocks))


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("inspect")
    s.add_argument("path")
    s = sub.add_parser("roundtrip")
    s.add_argument("--host", default=str(HOST_DEFAULT))
    s.add_argument("--out", default=str(ROOT / r"model_work\abrams_kv3_roundtrip.vmdl_c"))
    s = sub.add_parser("splice")
    s.add_argument("--host", default=str(HOST_DEFAULT))
    s.add_argument("--donor", default=str(DONOR_DEFAULT))
    s.add_argument("--out", default=str(OUT_DEFAULT))
    s.add_argument("--camera-side-offset", type=float)
    s.add_argument("--camera-back-offset", type=float)
    s.add_argument("--camera-aiming-back-offset", type=float)
    args = p.parse_args()
    if args.cmd == "inspect":
        inspect(Path(args.path))
    elif args.cmd == "roundtrip":
        roundtrip_kv(Path(args.host), Path(args.out))
    else:
        splice(
            Path(args.host),
            Path(args.donor),
            Path(args.out),
            camera_side_offset=args.camera_side_offset,
            camera_back_offset=args.camera_back_offset,
            camera_aiming_back_offset=args.camera_aiming_back_offset,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
