"""
Rebind the cut body + Sully head to the original Abrams armature and
export FBX *with* the armature (skin weights). Mesh-only FBX wrote no
skin clusters, so the last ship sat in the world as a giant unskinned slab.

Scene units are set to inches so CSDK does not treat our inch numbers as meters.
"""
from __future__ import annotations

from pathlib import Path

import bpy

BLEND = Path(r"C:\TestCode\Abrams\model_work\sully_export\sully_cut.blend")
CONTENT = Path(
    r"C:\TestCode\Abrams\tools\Reduced_CSDK_12\content\citadel_addons\sully_abrams\models\heroes_wip\abrams"
)
OUT = Path(r"C:\TestCode\Abrams\model_work\sully_export")
HEAD_MAT = "models/heroes_wip/abrams/materials/abrams_head"
REMAP = {
    "abrams_coat": "models/heroes_wip/abrams/materials/abrams_coat",
    "abrams_upper_body": "models/heroes_wip/abrams/materials/abrams_upper_body",
    "abrams_lower_body": "models/heroes_wip/abrams/materials/abrams_lower_body",
    "abrams_head": HEAD_MAT,
    "abrams_teeth": "models/heroes_wip/abrams/materials/abrams_teeth",
}


def find_objects():
    arm = body = head = None
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == "ARMATURE":
            arm = o
        elif o.type == "MESH":
            if o.name == "sully_face" or (head is None and "sully" in n):
                head = o
            elif o.name == "abrams_model" or (
                body is None and "abrams_model" in n and "face" not in n
            ):
                body = o
    return arm, body, head


def bind(obj, arm, extra_group=None):
    """Parent with keep-transform and ensure an armature deformer."""
    mw = obj.matrix_world.copy()
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()
    obj.matrix_world = mw
    mod = None
    for m in obj.modifiers:
        if m.type == "ARMATURE":
            mod = m
            break
    if mod is None:
        mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    mod.use_vertex_groups = True
    if extra_group and extra_group not in obj.vertex_groups:
        vg = obj.vertex_groups.new(name=extra_group)
        vg.add([v.index for v in obj.data.vertices], 1.0, "REPLACE")
    print(
        f"bound {obj.name} parent={obj.parent} groups={len(obj.vertex_groups)} "
        f"mod={mod.object} verts={len(obj.data.vertices)}"
    )


def fix_materials(body, head):
    hm = bpy.data.materials.get(HEAD_MAT)
    if hm is None:
        for m in bpy.data.materials:
            if m.name.lower() == "abrams_head":
                m.name = HEAD_MAT
                hm = m
                break
    if hm is None:
        hm = bpy.data.materials.new(HEAD_MAT)
    hm.use_nodes = True
    for i, m in enumerate(list(body.data.materials)):
        if not m:
            continue
        low = m.name.lower()
        if "abrams_head" in low:
            body.data.materials[i] = hm
            continue
        for key, dest in REMAP.items():
            if key in low and m.name != dest:
                m.name = dest
                break
    head.data.materials.clear()
    head.data.materials.append(hm)
    print("body mats", [m.name if m else None for m in body.data.materials])
    print("head mats", [m.name if m else None for m in head.data.materials])


def set_inch_units():
    # 1 Blender unit = 1 inch. Verts are already in inch numbers.
    u = bpy.context.scene.unit_settings
    u.system = "IMPERIAL"
    u.scale_length = 0.0254
    u.length_unit = "INCHES"
    print("units", u.system, "scale_length", u.scale_length, "length", u.length_unit)


def export_fbx(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
        o.hide_set(False)
        o.hide_viewport = False
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False,
        bake_anim=False,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        use_armature_deform_only=True,
        armature_nodetype="NULL",
        path_mode="STRIP",
        embed_textures=False,
        global_scale=1.0,
    )
    print("Wrote", path)


def main():
    if not BLEND.exists():
        raise SystemExit(f"missing {BLEND}")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    arm, body, head = find_objects()
    print("found", arm, body, head)
    if not arm or not body or not head:
        raise SystemExit("need armature + body + head in the blend")

    print("body groups sample", [g.name for g in body.vertex_groups][:15], "n=", len(body.vertex_groups))
    print("head groups", [g.name for g in head.vertex_groups])

    bind(body, arm)
    bind(head, arm, extra_group="head")
    fix_materials(body, head)
    set_inch_units()

    # Hide everything else so FBX is just these objects
    keep = {arm, body, head}
    for o in bpy.data.objects:
        if o not in keep:
            o.hide_set(True)

    CONTENT.mkdir(parents=True, exist_ok=True)
    export_fbx(CONTENT / "sully_face.fbx", [head, arm])
    export_fbx(OUT / "sully_face.fbx", [head, arm])
    export_fbx(CONTENT / "abrams_body_nohead.fbx", [body, arm])
    export_fbx(OUT / "abrams_body_nohead.fbx", [body, arm])
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "sully_skinned.blend"))
    print("DONE")


if __name__ == "__main__":
    main()
