"""
Build a Sully-like head in Source 2 inches, bind to Abrams head bone, export FBX.

glTF from Source2Viewer is in meters. CSDK/ModelDoc meshes are inches (x39.37).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\TestCode\Abrams")
GLTF = ROOT / r"model_work\abrams_export\models\heroes_wip\abrams\abrams.gltf"
PORTRAIT = ROOT / r"sully_textures\bull_card_psd.png"
if not PORTRAIT.exists():
    PORTRAIT = ROOT / r"refs\sulley_profile.jpg"
OUT_DIR = ROOT / r"model_work\sully_export"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FBX = OUT_DIR / "sully_face.fbx"
OUT_BLEND = OUT_DIR / "sully_face.blend"
OUT_PREVIEW = OUT_DIR / "sully_face_preview.png"
OUT_TEX = ROOT / r"sully_textures\abrams_head_color_png_ce8a55ec.png"
CONTENT_FBX = (
    ROOT
    / r"tools\Reduced_CSDK_12\content\citadel_addons\sully_abrams\models\heroes_wip\abrams\sully_face.fbx"
)
INCH = 39.37007874
MAT_NAME = "models/heroes_wip/abrams/materials/abrams_head"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mesh_world_bounds(obj):
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    zs = [c.z for c in coords]
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


def add_cone(loc, r1, r2, depth, rot=None, name="horn"):
    bpy.ops.mesh.primitive_cone_add(
        vertices=16, radius1=r1, radius2=r2, depth=depth, location=loc
    )
    obj = bpy.context.active_object
    obj.name = name
    if rot:
        obj.rotation_euler = rot
        bpy.ops.object.transform_apply(rotation=True)
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
    rem.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier=rem.name)
    smooth = obj.modifiers.new("Smooth", "SMOOTH")
    smooth.factor = 0.8
    smooth.iterations = 8
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    bpy.ops.object.shade_smooth()


def main():
    clear()
    bpy.ops.import_scene.gltf(filepath=str(GLTF))

    # Official CSDK path: glTF meters -> Source 2 inches
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.transform.resize(value=(INCH, INCH, INCH))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    arm = face = None
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == "ARMATURE":
            arm = o
        elif o.type == "MESH" and "face" in n and "lod" not in n:
            face = o
    if not arm or not face:
        print("ERROR missing arm/face", arm, face)
        sys.exit(1)

    center, size, mn, mx = mesh_world_bounds(face)
    print("Face center", tuple(center), "size", tuple(size))

    # Source 2 / VRF glTF after scale: +X is typically character left/right,
    # +Y up, -Z or +Y forward depending on export. Face AABB tells us the
    # long axes. Abrams looks down -Y in many VRF dumps; also try using the
    # face mesh's average normal.
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
    print("fwd", tuple(fwd), "up", tuple(up), "right", tuple(right))

    w, h, d = size.x, size.y, size.z
    # Head should be larger than stock Abrams face (monster snout + cheeks)
    skull_r = max(w, h, d) * 0.48
    c = center + up * (h * 0.05) + fwd * (d * 0.05)

    body_parts = []
    body_parts.append(add_sphere(c, skull_r, 40, 28, (1.15, 1.05, 1.1), "skull"))
    body_parts.append(
        add_sphere(
            c + fwd * skull_r * 0.55 - up * skull_r * 0.12,
            skull_r * 0.55,
            32,
            22,
            (1.15, 1.25, 0.85),
            "snout",
        )
    )
    body_parts.append(
        add_sphere(
            c + fwd * skull_r * 0.85 - up * skull_r * 0.22,
            skull_r * 0.28,
            24,
            16,
            (1.2, 0.9, 0.7),
            "muzzle",
        )
    )
    for sx in (-1, 1):
        body_parts.append(
            add_sphere(
                c + right * sx * skull_r * 0.72 - up * skull_r * 0.05 + fwd * skull_r * 0.15,
                skull_r * 0.42,
                24,
                16,
                (0.85, 0.95, 0.9),
                f"cheek_{sx}",
            )
        )
        body_parts.append(
            add_sphere(
                c + right * sx * skull_r * 0.55 + up * skull_r * 0.15 + fwd * skull_r * 0.35,
                skull_r * 0.22,
                16,
                12,
                (1.1, 0.7, 0.7),
                f"brow_{sx}",
            )
        )
        body_parts.append(
            add_sphere(
                c + right * sx * skull_r * 0.95 + up * skull_r * 0.05 - fwd * skull_r * 0.1,
                skull_r * 0.22,
                16,
                12,
                (0.45, 0.85, 1.15),
                f"ear_{sx}",
            )
        )

    fur = join_objects(body_parts, "sully_fur")
    apply_voxel(fur, max(skull_r * 0.045, 0.25))

    detail = []
    # Horns: out, up, slightly back
    for sx in (-1, 1):
        horn_base = (
            c
            + right * sx * skull_r * 0.38
            + up * skull_r * 0.72
            - fwd * skull_r * 0.05
        )
        horn = add_cone(
            horn_base + up * skull_r * 0.28 + right * sx * skull_r * 0.08,
            skull_r * 0.12,
            skull_r * 0.03,
            skull_r * 0.62,
            rot=(
                math.radians(-18),
                math.radians(sx * -28),
                math.radians(sx * 8),
            ),
            name=f"horn_{sx}",
        )
        detail.append(horn)

    # Eyes
    for sx in (-1, 1):
        eye_c = (
            c
            + right * sx * skull_r * 0.28
            + up * skull_r * 0.18
            + fwd * skull_r * 0.62
        )
        eye = add_sphere(eye_c, skull_r * 0.16, 20, 14, (1.05, 0.85, 0.75), f"eye_{sx}")
        detail.append(eye)

    # Teeth block under snout
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=c + fwd * skull_r * 0.78 - up * skull_r * 0.38,
    )
    teeth = bpy.context.active_object
    teeth.name = "teeth"
    teeth.scale = (skull_r * 0.55, skull_r * 0.18, skull_r * 0.12)
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
    head.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Procedural teal fur + purple spots + optional front-mapped portrait, then bake
    mat = bpy.data.materials.new(MAT_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    nodes, links = nt.nodes, nt.links
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2.2, 2.2, 2.2)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 3.5
    links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (0.35, 0.12, 0.55, 1)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (0.12, 0.62, 0.70, 1)
    links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    color_out = ramp.outputs["Color"]
    if PORTRAIT.exists():
        pimg = bpy.data.images.load(str(PORTRAIT))
        ptex = nodes.new("ShaderNodeTexImage")
        ptex.image = pimg
        ptex.projection = "BOX"
        ptex.projection_blend = 0.25
        pmap = nodes.new("ShaderNodeMapping")
        # Map portrait onto the front of the head in object space
        pmap.inputs["Scale"].default_value = (0.035, 0.035, 0.035)
        links.new(tex_coord.outputs["Object"], pmap.inputs["Vector"])
        links.new(pmap.outputs["Vector"], ptex.inputs["Vector"])
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(tex_coord.outputs["Normal"], sep.inputs["Vector"])
        # Face-forward mix: more portrait on the snout (object -Y after our basis)
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs["Fac"].default_value = 0.55
        links.new(ramp.outputs["Color"], mix.inputs["Color1"])
        links.new(ptex.outputs["Color"], mix.inputs["Color2"])
        color_out = mix.outputs["Color"]
    if bsdf:
        links.new(color_out, bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.85
    bake_img = bpy.data.images.new("sully_face_color", 2048, 2048, alpha=False)
    bake_node = nodes.new("ShaderNodeTexImage")
    bake_node.image = bake_img
    nodes.active = bake_node
    head.data.materials.clear()
    head.data.materials.append(mat)
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "CPU"
    bpy.context.scene.cycles.samples = 8
    bpy.context.scene.cycles.bake_type = "DIFFUSE"
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_color = True
    bpy.context.view_layer.objects.active = head
    head.select_set(True)
    try:
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
        bake_img.filepath_raw = str(OUT_TEX)
        bake_img.file_format = "PNG"
        bake_img.save()
        print("Baked", OUT_TEX)
    except Exception as e:
        print("bake failed", e)
        if PORTRAIT.exists():
            import shutil
            shutil.copyfile(PORTRAIT, OUT_TEX)

    cam_loc = c + fwd * skull_r * 4.2 + up * skull_r * 0.1
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.active_object
    cam.rotation_euler = (c - cam_loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    # Bind 100% to head bone (name must match Abrams skeleton)
    vg = head.vertex_groups.new(name="head")
    vg.add([v.index for v in head.data.vertices], 1.0, "REPLACE")
    head.parent = arm
    mod = head.modifiers.new("Armature", "ARMATURE")
    mod.object = arm

    bpy.data.objects.remove(face, do_unlink=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

    # Preview render
    bpy.context.scene.render.resolution_x = 768
    bpy.context.scene.render.resolution_y = 768
    bpy.context.scene.render.filepath = str(OUT_PREVIEW)
    bpy.context.scene.render.film_transparent = True
    try:
        bpy.ops.render.render(write_still=True)
        print("Wrote preview", OUT_PREVIEW)
    except Exception as e:
        print("preview failed", e)

    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    head.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.export_scene.fbx(
        filepath=str(OUT_FBX),
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        armature_nodetype="NULL",
        use_armature_deform_only=True,
    )
    CONTENT_FBX.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(CONTENT_FBX),
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        armature_nodetype="NULL",
        use_armature_deform_only=True,
    )
    print("Wrote", OUT_FBX)
    print("Wrote", CONTENT_FBX)
    print("DONE")


if __name__ == "__main__":
    main()
