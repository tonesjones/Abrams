"""
Cut stock Abrams head/glasses off the body mesh, build a Sully head, export both FBXs.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\TestCode\Abrams")
GLTF = ROOT / r"model_work\abrams_export\models\heroes_wip\abrams\abrams.gltf"
CONTENT = (
    ROOT
    / r"tools\Reduced_CSDK_12\content\citadel_addons\sully_abrams\models\heroes_wip\abrams"
)
OUT_DIR = ROOT / r"model_work\sully_export"
OUT_DIR.mkdir(parents=True, exist_ok=True)
INCH = 39.37007874
HEAD_BONE_SUBSTR = (
    "head",
    "glass",
    "jaw",
    "eye",
    "lid",
    "brow",
    "cheek",
    "lip",
    "teeth",
    "tongue",
    "nose",
    "ear",
    "horn",
    "face",
)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mesh_world_bounds(obj):
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs, ys, zs = [c.x for c in coords], [c.y for c in coords], [c.z for c in coords]
    mn = Vector((min(xs), min(ys), min(zs)))
    mx = Vector((max(xs), max(ys), max(zs)))
    return (mn + mx) * 0.5, mx - mn, mn, mx


def add_sphere(loc, radius, segs=32, rings=20, scale=None, name="part"):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segs, ring_count=rings, radius=radius, location=loc
    )
    obj = bpy.context.active_object
    obj.name = name
    if scale:
        obj.scale = scale
        bpy.ops.object.transform_apply(scale=True)
    return obj


def join_objects(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    return obj


def apply_voxel(obj, voxel_size):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    rem = obj.modifiers.new("Voxel", "REMESH")
    rem.mode = "VOXEL"
    rem.voxel_size = voxel_size
    bpy.ops.object.modifier_apply(modifier=rem.name)
    smooth = obj.modifiers.new("Smooth", "SMOOTH")
    smooth.factor = 0.75
    smooth.iterations = 6
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    bpy.ops.object.shade_smooth()


def delete_head_verts(body):
    groups = {g.name: g.index for g in body.vertex_groups}
    print("body groups", list(groups)[:40], "...", len(groups))
    head_gis = [
        i
        for n, i in groups.items()
        if any(s in n.lower() for s in HEAD_BONE_SUBSTR)
    ]
    print("head-like groups", [n for n, i in groups.items() if i in head_gis])
    remove = set()
    for v in body.data.vertices:
        wsum = 0.0
        for g in v.groups:
            if g.group in head_gis:
                wsum += g.weight
        if wsum >= 0.45:
            remove.add(v.index)
        else:
            z = (body.matrix_world @ v.co).z
            if z > 96.0 and wsum >= 0.15:
                remove.add(v.index)
    print("deleting", len(remove), "of", len(body.data.vertices), "body verts")
    if not remove:
        return
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for i, v in enumerate(body.data.vertices):
        v.select = i in remove
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")


def export_fbx(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        armature_nodetype="NULL",
        use_armature_deform_only=True,
    )
    print("Wrote", path)


def main():
    clear()
    bpy.ops.import_scene.gltf(filepath=str(GLTF))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.transform.resize(value=(INCH, INCH, INCH))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    arm = face = body = None
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == "ARMATURE":
            arm = o
        elif o.type == "MESH" and "face" in n and "lod" not in n:
            face = o
        elif o.type == "MESH" and "abrams_model" in n and "face" not in n and "lod" not in n:
            body = o
    if not arm or not face or not body:
        print("ERROR", arm, face, body)
        sys.exit(1)

    center, size, mn, mx = mesh_world_bounds(face)
    print("Face center", tuple(center), "size", tuple(size))

    delete_head_verts(body)

    normals = [face.matrix_world.to_3x3() @ v.normal for v in face.data.vertices]
    fwd = sum(normals, Vector((0, 0, 0)))
    if fwd.length < 1e-6:
        fwd = Vector((0, -1, 0))
    fwd.normalize()
    up = Vector((0, 0, 1))
    if abs(fwd.dot(up)) > 0.85:
        up = Vector((0, 1, 0))
    right = up.cross(fwd).normalized()
    up = fwd.cross(right).normalized()

    skull_r = max(size.x, size.y, size.z) * 0.50
    c = center + up * (size.z * 0.02)
    parts = [
        add_sphere(c, skull_r, 40, 28, (1.18, 1.08, 1.12), "skull"),
        add_sphere(
            c + fwd * skull_r * 0.58 - up * skull_r * 0.10,
            skull_r * 0.56,
            32,
            22,
            (1.18, 1.28, 0.88),
            "snout",
        ),
        add_sphere(
            c + fwd * skull_r * 0.88 - up * skull_r * 0.22,
            skull_r * 0.30,
            24,
            16,
            (1.25, 0.95, 0.72),
            "muzzle",
        ),
    ]
    for sx in (-1, 1):
        parts.append(
            add_sphere(
                c + right * sx * skull_r * 0.74 - up * skull_r * 0.04 + fwd * skull_r * 0.18,
                skull_r * 0.44,
                24,
                16,
                (0.88, 0.95, 0.92),
                f"cheek_{sx}",
            )
        )
        parts.append(
            add_sphere(
                c + right * sx * skull_r * 0.98 + up * skull_r * 0.06 - fwd * skull_r * 0.08,
                skull_r * 0.22,
                16,
                12,
                (0.45, 0.9, 1.15),
                f"ear_{sx}",
            )
        )
    fur = join_objects(parts, "sully_fur")
    apply_voxel(fur, max(skull_r * 0.048, 0.28))

    detail = []
    for sx in (-1, 1):
        detail.append(
            add_sphere(
                c + right * sx * skull_r * 0.22 + up * skull_r * 0.72 - fwd * skull_r * 0.02,
                skull_r * 0.13,
                16,
                10,
                None,
                f"hornbase_{sx}",
            )
        )
        bpy.ops.mesh.primitive_cone_add(
            vertices=14,
            radius1=skull_r * 0.11,
            radius2=skull_r * 0.025,
            depth=skull_r * 0.62,
            location=c
            + right * sx * skull_r * 0.42
            + up * skull_r * 1.02
            + right * sx * skull_r * 0.06,
        )
        h = bpy.context.active_object
        h.rotation_euler = (math.radians(-22), math.radians(sx * -26), 0)
        bpy.ops.object.transform_apply(rotation=True)
        detail.append(h)
        detail.append(
            add_sphere(
                c + right * sx * skull_r * 0.28 + up * skull_r * 0.20 + fwd * skull_r * 0.64,
                skull_r * 0.155,
                20,
                14,
                (1.05, 0.82, 0.72),
                f"eye_{sx}",
            )
        )
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=c + fwd * skull_r * 0.80 - up * skull_r * 0.38
    )
    teeth = bpy.context.active_object
    teeth.scale = (skull_r * 0.55, skull_r * 0.16, skull_r * 0.11)
    bpy.ops.object.transform_apply(scale=True)
    detail.append(teeth)

    bpy.ops.object.select_all(action="DESELECT")
    fur.select_set(True)
    for o in detail:
        o.select_set(True)
    bpy.context.view_layer.objects.active = fur
    bpy.ops.object.join()
    head = bpy.context.active_object
    head.name = "sully_face"
    bpy.ops.object.shade_smooth()

    bpy.context.view_layer.objects.active = head
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")

    mat = bpy.data.materials.new("models/heroes_wip/abrams/materials/abrams_head")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.14, 0.68, 0.74, 1)
    head.data.materials.clear()
    head.data.materials.append(mat)
    vg = head.vertex_groups.new(name="head")
    vg.add([v.index for v in head.data.vertices], 1.0, "REPLACE")
    head.parent = arm
    amod = head.modifiers.new("Armature", "ARMATURE")
    amod.object = arm

    bpy.data.objects.remove(face, do_unlink=True)

    body_fbx = CONTENT / "abrams_body_nohead.fbx"
    face_fbx = CONTENT / "sully_face.fbx"
    export_fbx(face_fbx, [head, arm])
    export_fbx(OUT_DIR / "sully_face.fbx", [head, arm])
    export_fbx(body_fbx, [body, arm])
    export_fbx(OUT_DIR / "abrams_body_nohead.fbx", [body, arm])
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_DIR / "sully_cut.blend"))
    print("DONE")


if __name__ == "__main__":
    main()
