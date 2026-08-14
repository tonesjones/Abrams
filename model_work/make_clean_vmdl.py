"""
Build a community-swap-shaped Abrams vmdl for CSDK bin_cs2.

Takes the known-working pak87 decompile, keeps bone-based lists
(attachments / weight lists / constraints / hitboxes / gamedata),
rewrites RenderMeshList, and strips compiled-only nodes that bin_cs2
cannot allocate (NmSkeletonList, AnimGraph2List) plus the decompiled
Skeleton/Physics dumps that would double-bind a custom mesh.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(r"C:\TestCode\Abrams")
SRC = ROOT / r"extracted\custom_abrams_pak87\decompiled"
CONTENT = (
    ROOT
    / r"tools\Reduced_CSDK_12\content\citadel_addons\sully_abrams\models\heroes_wip\abrams"
)
HEADER = (
    "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} "
    "format:modeldoc28:version{fb63b6ca-f435-4aa0-a2c7-c66ddc651dca} -->\n"
)

KEEP = (
    "BoneMarkupList",
    "BodyGroupList",
    "AttachmentList",
    "WeightListList",
    "AnimationList",
    "AnimConstraintList",
    "GameDataList",
    "HitboxSetList",
)

ISOLATION_A_MESHES = [
    ("body", "models/heroes_wip/abrams/abrams_abrams_model.dmx"),
    ("book", "models/heroes_wip/abrams/abrams_book_model3.dmx"),
    ("gun", "models/heroes_wip/abrams/abrams_gun_model2.dmx"),
]
ISOLATION_B_MESHES = [
    ("body", "models/heroes_wip/abrams/abrams_body_nohead.fbx"),
    ("face", "models/heroes_wip/abrams/sully_face.fbx"),
    ("book", "models/heroes_wip/abrams/abrams_book_model3.dmx"),
    ("gun", "models/heroes_wip/abrams/abrams_gun_model2.dmx"),
]


def extract_blocks(text: str) -> dict[str, str]:
    """Map top-level rootNode child class name -> full `{ ... }` block."""
    lines = text.splitlines()
    blocks: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("\t\t\t\t_class = "):
            name = line.split('"')[1]
            # walk back to the opening brace of this child
            start = i
            while start > 0 and lines[start].strip() != "{":
                start -= 1
            depth = 0
            end = start
            while end < len(lines):
                depth += lines[end].count("{") - lines[end].count("}")
                if depth == 0 and end > start:
                    break
                end += 1
            block = "\n".join(lines[start : end + 1]).rstrip()
            if block.endswith(","):
                block = block[:-1]
            blocks[name] = block
            i = end + 1
            continue
        i += 1
    return blocks


def render_mesh_block(meshes: list[tuple[str, str]], import_scale: float = 1.0) -> str:
    children = []
    for name, filename in meshes:
        scale = import_scale if filename.lower().endswith(".fbx") else 1.0
        children.append(
            "\t\t\t\t\t{\n"
            "\t\t\t\t\t\t_class = \"RenderMeshFile\"\n"
            f'\t\t\t\t\t\tname = "{name}"\n'
            f'\t\t\t\t\t\tfilename = "{filename}"\n'
            "\t\t\t\t\t\timport_translation = [ 0.0, 0.0, 0.0 ]\n"
            "\t\t\t\t\t\timport_rotation = [ 0.0, 0.0, 0.0 ]\n"
            f'\t\t\t\t\t\timport_scale = {scale:.8f}\n'
            "\t\t\t\t\t\talign_origin_x_type = \"None\"\n"
            "\t\t\t\t\t\talign_origin_y_type = \"None\"\n"
            "\t\t\t\t\t\talign_origin_z_type = \"None\"\n"
            "\t\t\t\t\t\tparent_bone = \"\"\n"
            "\t\t\t\t\t\timport_filter =\n"
            "\t\t\t\t\t\t{\n"
            "\t\t\t\t\t\t\texclude_by_default = false\n"
            "\t\t\t\t\t\t\texception_list = [  ]\n"
            "\t\t\t\t\t\t}\n"
            "\t\t\t\t\t}"
        )
    inner = ",\n".join(children)
    return (
        "\t\t\t{\n"
        "\t\t\t\t_class = \"RenderMeshList\"\n"
        "\t\t\t\tchildren =\n"
        "\t\t\t\t[\n"
        f"{inner}\n"
        "\t\t\t\t]\n"
        "\t\t\t}"
    )


def bodygroup_block(mesh_names: list[str], include_face: bool) -> str:
    default_meshes = ["body", "book"]
    if include_face:
        default_meshes = ["body", "face", "book"]
    default_list = ",\n".join(f'\t\t\t\t\t\t\t\t\t"{n}"' for n in default_meshes)
    return f"""			{{
				_class = "BodyGroupList"
				children =
				[
					{{
						_class = "BodyGroup"
						name = "default"
						children =
						[
							{{
								_class = "BodyGroupChoice"
								name = "0"
								meshes =
								[
{default_list}
								]
							}},
						]
					}},
					{{
						_class = "BodyGroup"
						name = "gun"
						children =
						[
							{{
								_class = "BodyGroupChoice"
								name = "0"
								meshes =
								[
									"gun",
								]
							}},
							{{
								_class = "BodyGroupChoice"
								name = "1"
								meshes = [  ]
							}},
						]
					}},
				]
			}}"""


def animation_block() -> str:
    return """			{
				_class = "AnimationList"
				children =
				[
					{
						_class = "AnimIncludeModel"
						model = "models/heroes_wip/abrams/abrams_backup.vmdl"
					},
				]
			}"""


def assemble(
    blocks: dict[str, str],
    meshes: list[tuple[str, str]],
    include_face: bool,
    import_scale: float = 1.0,
) -> str:
    parts = [
        HEADER.rstrip(),
        "{",
        "\trootNode =",
        "\t{",
        '\t\t_class = "RootNode"',
        "\t\tchildren =",
        "\t\t[",
    ]
    children = []
    children.append(blocks["BoneMarkupList"])
    children.append(render_mesh_block(meshes, import_scale=import_scale))
    children.append(bodygroup_block([n for n, _ in meshes], include_face))
    for key in (
        "AttachmentList",
        "WeightListList",
        "AnimationList",
        "AnimConstraintList",
        "GameDataList",
        "HitboxSetList",
    ):
        if key == "AnimationList":
            children.append(animation_block())
        elif key in blocks:
            children.append(blocks[key])
        else:
            raise SystemExit(f"missing block {key}")
    parts.append(",\n".join(children))
    parts.append("\t\t]")
    parts.append("\t}")
    parts.append("}")
    parts.append("")
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=("A", "B"))
    ap.add_argument("--scale", type=float, default=1.0, help="FBX import_scale")
    args = ap.parse_args()
    text = SRC.read_text(encoding="utf-8", errors="replace")
    blocks = extract_blocks(text)
    print("found blocks:", ", ".join(blocks))
    dest = CONTENT / "abrams.vmdl"
    bak = CONTENT / "abrams.vmdl.bak_isolation"
    if dest.exists() and not bak.exists():
        shutil.copy2(dest, bak)
        print("backed up", dest, "->", bak)
    if args.variant == "A":
        out = assemble(blocks, ISOLATION_A_MESHES, include_face=False, import_scale=1.0)
    else:
        out = assemble(blocks, ISOLATION_B_MESHES, include_face=True, import_scale=args.scale)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({dest.stat().st_size} bytes) variant={args.variant} scale={args.scale}")


if __name__ == "__main__":
    main()
