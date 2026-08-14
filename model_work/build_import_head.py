"""
Replace the primitive sully_face in sully_cut.blend with the imported
Dreamlight Sully head. Does not remesh. Does not invent a compile path.

1. Open the working cut blend (body + Abrams armature stay untouched).
2. Import sully.glb, bake the armature-deformed standing mesh.
3. Cut at the neck using imported head/neck/face groups (token match).
4. Join the separate eye mesh. Keep imported UVs.
5. Scale to stock face height and seat at FACE_CENTER.
6. 100% `head` weights. Leave parenting to export_sully_skinned.py.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\TestCode\Abrams")
BLEND = ROOT / r"model_work\sully_export\sully_cut.blend"
GLB = ROOT / r"model_work\import_head\sully.glb"
OUT_DIR = ROOT / r"model_work\sully_export"
TEX_DIR = ROOT / r"sully_textures"
SRC_COLOR = ROOT / r"model_work\import_head\textures\Image_0.png"
SRC_NORMAL = ROOT / r"model_work\import_head\textures\Image_1.png"
HEAD_MAT = "models/heroes_wip/abrams/materials/abrams_head"
FACE_CENTER = Vector((0.0, 3.361, 102.962))
# Stock Abrams face AABB z after x39.37. Matches neck to the old face bottom.
TARGET_HEIGHT = 20.6901
HEAD_TOKENS = {
    "head",
    "neck",
    "neck1",
    "jaw",
    "eye",
    "eyelid",
    "brow",
    "lip",
    "mouth",
    "teeth",
}


def is_head_group(name: str) -> bool:
    tokens = name.lower().replace(".", "_").split("_")
    return any(t in HEAD_TOKENS for t in tokens)


def bounds(obj):
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    zs = [c.z for c in coords]
    mn = Vector((min(xs), min(ys), min(zs)))
    mx = Vector((max(xs), max(ys), max(zs)))
    return (mn + mx) * 0.5, mx - mn, mn, mx


def bake_deformed(obj, name):
    """New object whose verts are the armature-deformed standing mesh."""
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=deps)
    new = bpy.data.objects.new(name, me)
    new.matrix_world = ev.matrix_world.copy()
    bpy.context.collection.objects.link(new)
    print(
        f"baked {obj.name} -> {name} verts={len(me.vertices)} "
        f"groups={len(new.vertex_groups)} uvs={len(me.uv_layers)}"
    )
    return new


def delete_non_head_verts(obj):
    groups = {g.name: g.index for g in obj.vertex_groups}
    head_gis = {i for n, i in groups.items() if is_head_group(n)}
    print("head groups", [n for n, i in groups.items() if i in head_gis])
    remove = set()
    for v in obj.data.vertices:
        wsum = sum(g.weight for g in v.groups if g.group in head_gis)
        if wsum < 0.40:
            remove.add(v.index)
    print("deleting", len(remove), "of", len(obj.data.vertices), "imported body verts")
    if not remove:
        raise SystemExit("neck cut selected nothing")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for i, v in enumerate(obj.data.vertices):
        v.select = i in remove
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    print("head remaining", len(obj.data.vertices))


def apply_world(obj):
    mw = obj.matrix_world.copy()
    obj.data.transform(mw)
    obj.matrix_world.identity()
    obj.data.update()


def seat_at_face(obj):
    apply_world(obj)
    center, size, mn, mx = bounds(obj)
    print("head pre-seat center", tuple(center), "size", tuple(size))
    if size.z < 1e-4:
        raise SystemExit("head has no height")
    scale = TARGET_HEIGHT / size.z
    print("seat scale", scale, "target height", TARGET_HEIGHT)
    for v in obj.data.vertices:
        v.co = FACE_CENTER + (v.co - center) * scale
    obj.data.update()
    center, size, mn, mx = bounds(obj)
    print("head seated center", tuple(center), "size", tuple(size))
    print("head seated min", tuple(mn), "max", tuple(mx))


def assign_head_weights(obj):
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    vg = obj.vertex_groups.new(name="head")
    vg.add([v.index for v in obj.data.vertices], 1.0, "REPLACE")


def assign_head_material(obj):
    mat = bpy.data.materials.get(HEAD_MAT)
    if mat is None:
        mat = bpy.data.materials.new(HEAD_MAT)
    mat.use_nodes = True
    img = bpy.data.images.load(str(SRC_COLOR), check_existing=True)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = None
    for n in nt.nodes:
        if n.type == "TEX_IMAGE":
            tex = n
            break
    if tex is None:
        tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    if bsdf:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.85
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def copy_head_textures():
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    for dest_name in (
        "abrams_head_color_png_ce8a55ec.png",
        "abrams_head_basecolor_png_f84c4214.png",
    ):
        dest = TEX_DIR / dest_name
        shutil.copyfile(SRC_COLOR, dest)
        print("copied color", dest, dest.stat().st_size)
    if SRC_NORMAL.exists():
        dest = TEX_DIR / "abrams_head_normal_png_20d421b4.png"
        shutil.copyfile(SRC_NORMAL, dest)
        print("copied normal", dest, dest.stat().st_size)


def render_preview(path, look_at, cam_loc):
    world = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.18, 0.22, 1)
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.rotation_euler = (look_at - cam_loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start = 0.1
    cam.data.clip_end = 4000
    bpy.context.scene.camera = cam
    bpy.ops.object.light_add(type="SUN", location=cam_loc)
    bpy.context.object.data.energy = 5
    bpy.ops.object.light_add(type="AREA", location=look_at + Vector((20, 10, 16)))
    bpy.context.object.data.energy = 400
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.render.resolution_x = 900
    bpy.context.scene.render.resolution_y = 900
    bpy.context.scene.render.filepath = str(path)
    bpy.context.scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)
    print("Wrote", path)


def main():
    if not BLEND.exists():
        raise SystemExit(f"missing {BLEND}")
    if not GLB.exists():
        raise SystemExit(f"missing {GLB}")

    bak = BLEND.with_suffix(".blend.bak_pre_import")
    if not bak.exists():
        shutil.copy2(BLEND, bak)
        print("backed up", bak)

    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    old_head = bpy.data.objects.get("sully_face")
    body = bpy.data.objects.get("abrams_model")
    if old_head is None or body is None:
        raise SystemExit("sully_cut.blend missing sully_face or abrams_model")
    keep_names = {o.name for o in bpy.data.objects}

    bpy.ops.import_scene.gltf(filepath=str(GLB))
    src_body = bpy.data.objects.get("Object_82")
    src_eyes = bpy.data.objects.get("Object_83")
    if src_body is None or src_eyes is None:
        raise SystemExit(f"glb missing Object_82/83: {[o.name for o in bpy.data.objects]}")

    head = bake_deformed(src_body, "sully_head_src")
    eyes = bake_deformed(src_eyes, "sully_eyes_src")

    # Drop the imported armature and raw meshes so they cannot leak into FBX.
    for o in list(bpy.data.objects):
        if o.name not in keep_names and o not in {head, eyes}:
            bpy.data.objects.remove(o, do_unlink=True)

    delete_non_head_verts(head)

    bpy.ops.object.select_all(action="DESELECT")
    head.select_set(True)
    eyes.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.join()
    head = bpy.context.active_object
    print("joined head+eyes verts", len(head.data.vertices))

    bpy.data.objects.remove(old_head, do_unlink=True)
    head.name = "sully_face"
    head.parent = None
    seat_at_face(head)
    assign_head_weights(head)
    assign_head_material(head)
    bpy.ops.object.shade_smooth()

    copy_head_textures()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    render_preview(
        OUT_DIR / "import_head_preview.png",
        Vector((0, 4, 104)),
        Vector((22, -72, 112)),
    )
    hcenter, _, _, _ = bounds(head)
    render_preview(
        OUT_DIR / "sully_face_preview.png",
        Vector(hcenter),
        Vector((hcenter.x + 4, hcenter.y - 28, hcenter.z + 2)),
    )
    print("DONE")


if __name__ == "__main__":
    main()
