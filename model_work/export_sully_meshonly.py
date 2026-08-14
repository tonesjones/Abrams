"""
Cut stock Abrams head/glasses off the body, build a readable Sully head,
export MESH-ONLY FBX (no armature) in Source 2 inches.

Do not remesh the whole head — that melted features into a bowling ball.
Do not parent to the armature. Vertex groups bind in ModelDoc.
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
    PORTRAIT = ROOT / r"release\showcase_portrait.jpg"
CONTENT = (
    ROOT
    / r"tools\Reduced_CSDK_12\content\citadel_addons\sully_abrams\models\heroes_wip\abrams"
)
OUT_DIR = ROOT / r"model_work\sully_export"
OUT_DIR.mkdir(parents=True, exist_ok=True)
INCH = 39.37007874
HEAD_MAT = "models/heroes_wip/abrams/materials/abrams_head"
HEAD_TOKENS = {
    "head",
    "jaw",
    "glass",
    "glasses",
    "eye",
    "lid",
    "brow",
    "cheek",
    "lip",
    "lips",
    "teeth",
    "tongue",
    "nose",
    "ear",
    "horn",
    "face",
    "eyelid",
    "eyelash",
}


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


def is_head_group(name: str) -> bool:
    tokens = name.lower().replace(".", "_").split("_")
    return any(t in HEAD_TOKENS for t in tokens)


def add_sphere(loc, radius, segs=32, rings=20, scale=None, name="part"):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segs, ring_count=rings, radius=radius, location=loc
    )
    obj = bpy.context.active_object
    obj.name = name
    if scale:
        obj.scale = scale
        bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
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
    bpy.ops.object.shade_smooth()
    return obj


def assign_mat(obj, name, color, roughness=0.7):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return mat


def join_objects(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    return obj


def delete_head_verts(body):
    groups = {g.name: g.index for g in body.vertex_groups}
    head_gis = {i for n, i in groups.items() if is_head_group(n)}
    print("head-like groups", [n for n, i in groups.items() if i in head_gis])
    remove = set()
    for v in body.data.vertices:
        wsum = 0.0
        for g in v.groups:
            if g.group in head_gis:
                wsum += g.weight
        z = (body.matrix_world @ v.co).z
        if wsum >= 0.40:
            remove.add(v.index)
        elif z > 97.0 and wsum >= 0.12:
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
    print("body remaining", len(body.data.vertices))


def make_fur_shader(mat, portrait_path: Path, use_uv_portrait: bool):
    """Teal fur + purple spots. Optional UV portrait, ignoring its black bg."""
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    for n in list(nodes):
        if n.type != "OUTPUT_MATERIAL" and n.type != "BSDF_PRINCIPLED":
            nodes.remove(n)
    bsdf = nodes.get("Principled BSDF")
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2.6, 2.6, 2.6)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "F1"
    vor.inputs["Scale"].default_value = 2.8
    links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.36
    ramp.color_ramp.elements[0].color = (0.40, 0.14, 0.58, 1)
    ramp.color_ramp.elements[1].position = 0.50
    ramp.color_ramp.elements[1].color = (0.11, 0.64, 0.74, 1)
    links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    color_out = ramp.outputs["Color"]
    if use_uv_portrait and portrait_path.exists():
        pimg = bpy.data.images.load(str(portrait_path))
        ptex = nodes.new("ShaderNodeTexImage")
        ptex.image = pimg
        ptex.extension = "CLIP"
        links.new(tex_coord.outputs["UV"], ptex.inputs["Vector"])
        # Treat near-black portrait pixels as transparent so the card
        # background does not paint the snout black.
        rgb2bw = nodes.new("ShaderNodeRGBToBW")
        links.new(ptex.outputs["Color"], rgb2bw.inputs["Color"])
        cr = nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].position = 0.08
        cr.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr.color_ramp.elements[1].position = 0.18
        cr.color_ramp.elements[1].color = (1, 1, 1, 1)
        links.new(rgb2bw.outputs["Val"], cr.inputs["Fac"])
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        links.new(cr.outputs["Color"], mix.inputs["Fac"])
        links.new(ramp.outputs["Color"], mix.inputs["Color1"])
        links.new(ptex.outputs["Color"], mix.inputs["Color2"])
        color_out = mix.outputs["Color"]
    if bsdf:
        links.new(color_out, bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.88
    return mat


def bake_color(obj, dest: Path, size=2048):
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "CPU"
    bpy.context.scene.cycles.samples = 8
    bpy.context.scene.cycles.bake_type = "DIFFUSE"
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_color = True
    img = bpy.data.images.new("sully_head_bake", size, size, alpha=False)
    # one bake target on every material
    for mat in obj.data.materials:
        if not mat or not mat.use_nodes:
            continue
        node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = img
        mat.node_tree.nodes.active = node
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
        img.filepath_raw = str(dest)
        img.file_format = "PNG"
        img.save()
        print("Baked", dest)
        return True
    except Exception as e:
        print("bake failed", e)
        return False


def export_mesh_fbx(path: Path, obj):
    # Apply transforms so FBX gets raw Source-2-inch coordinates
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_anim=False,
        apply_unit_scale=False,
        apply_scale_options="FBX_SCALE_NONE",
        axis_forward="-Y",
        axis_up="Z",
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        path_mode="COPY",
        embed_textures=True,
        global_scale=1.0,
    )
    print("Wrote", path, "verts", len(obj.data.vertices))


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
    fill = bpy.ops.object.light_add(type="AREA", location=look_at + Vector((20, 10, 16)))
    bpy.context.object.data.energy = 400
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.render.resolution_x = 900
    bpy.context.scene.render.resolution_y = 900
    bpy.context.scene.render.filepath = str(path)
    bpy.context.scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)
    print("Wrote", path)


def project_front_uvs(head, look_at, cam_loc, fwd):
    """Project the portrait onto front-facing faces from a face-on camera."""
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.name = "uv_cam"
    cam.rotation_euler = (look_at - cam_loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start = 0.1
    cam.data.clip_end = 4000
    bpy.context.scene.camera = cam
    bpy.context.view_layer.update()

    bpy.ops.object.select_all(action="DESELECT")
    head.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.mode_set(mode="OBJECT")
    for p in head.data.polygons:
        n = (head.matrix_world.to_3x3() @ p.normal).normalized()
        p.select = n.dot(fwd) > 0.25
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="FACE")
    try:
        bpy.ops.uv.project_from_view(camera_bounds=True, correct_aspect=True, scale_to_bounds=True)
        print("projected front UVs from view")
    except Exception as e:
        print("project_from_view failed", e)
        bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.012)
    bpy.ops.object.mode_set(mode="OBJECT")
    return cam


def build_sully_head(center, fwd, up, right):
    # Keep the skull modest so eyes/snout/horns stay readable.
    r = 7.6
    c = center + up * 0.3
    teal = (0.12, 0.64, 0.73)
    purple = (0.38, 0.16, 0.55)
    fur_parts = []
    fur_parts.append(add_sphere(c, r, 40, 28, (1.16, 1.04, 1.08), "skull"))
    # Snout sits in front of the skull, not swallowing the eyes.
    fur_parts.append(
        add_sphere(
            c + fwd * (r * 0.78) - up * (r * 0.18),
            r * 0.40,
            28,
            18,
            (1.35, 1.15, 0.80),
            "snout",
        )
    )
    fur_parts.append(
        add_sphere(
            c + fwd * (r * 1.05) - up * (r * 0.22),
            r * 0.20,
            20,
            12,
            (1.35, 0.90, 0.70),
            "muzzle",
        )
    )
    fur_parts.append(
        add_sphere(c - up * (r * 0.95) - fwd * (r * 0.02), r * 0.40, 24, 16, (1.0, 0.85, 1.05), "neck")
    )
    for sx in (-1, 1):
        fur_parts.append(
            add_sphere(
                c + right * sx * (r * 0.72) - up * (r * 0.06) + fwd * (r * 0.12),
                r * 0.38,
                22,
                14,
                (0.90, 0.95, 0.95),
                f"cheek_{sx}",
            )
        )
        fur_parts.append(
            add_sphere(
                c + right * sx * (r * 1.05) + up * (r * 0.12) - fwd * (r * 0.18),
                r * 0.30,
                18,
                12,
                (0.38, 0.95, 1.25),
                f"ear_{sx}",
            )
        )
        fur_parts.append(
            add_sphere(
                c + right * sx * (r * 0.28) + up * (r * 0.32) + fwd * (r * 0.78),
                r * 0.14,
                14,
                10,
                (1.25, 0.50, 0.50),
                f"brow_{sx}",
            )
        )
    for o in fur_parts:
        assign_mat(o, "sully_fur", teal, 0.9)
    fur = join_objects(fur_parts, "sully_fur")

    detail = []
    for sx in (-1, 1):
        horn = add_cone(
            c + right * sx * (r * 0.36) + up * (r * 1.12) + right * sx * (r * 0.08),
            r * 0.15,
            r * 0.030,
            r * 0.85,
            rot=(math.radians(-16), math.radians(sx * -28), math.radians(sx * 4)),
            name=f"horn_{sx}",
        )
        assign_mat(horn, "sully_horn", purple, 0.45)
        detail.append(horn)

        # Eyes sit on the skull surface, in front of the snout root.
        eye_c = c + right * sx * (r * 0.28) + up * (r * 0.18) + fwd * (r * 0.92)
        eye = add_sphere(eye_c, r * 0.20, 22, 16, (1.10, 0.72, 0.80), f"eye_{sx}")
        assign_mat(eye, "sully_eye", (0.96, 0.96, 0.93), 0.22)
        detail.append(eye)

        iris = add_sphere(
            eye_c + fwd * (r * 0.12),
            r * 0.085,
            16,
            10,
            (1.0, 0.40, 1.0),
            f"iris_{sx}",
        )
        assign_mat(iris, "sully_iris", (0.16, 0.60, 0.18), 0.32)
        detail.append(iris)

        pupil = add_sphere(eye_c + fwd * (r * 0.17), r * 0.038, 12, 8, None, f"pupil_{sx}")
        assign_mat(pupil, "sully_pupil", (0.02, 0.02, 0.02), 0.18)
        detail.append(pupil)

    nose = add_sphere(
        c + fwd * (r * 1.22) - up * (r * 0.18),
        r * 0.12,
        16,
        10,
        (1.20, 0.65, 0.60),
        "nose",
    )
    assign_mat(nose, "sully_nose", (0.05, 0.04, 0.05), 0.4)
    detail.append(nose)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=c + fwd * (r * 0.98) - up * (r * 0.42)
    )
    teeth = bpy.context.active_object
    teeth.name = "teeth"
    teeth.scale = (r * 0.48, r * 0.12, r * 0.09)
    bpy.ops.object.transform_apply(scale=True)
    assign_mat(teeth, "sully_teeth", (0.93, 0.90, 0.82), 0.35)
    detail.append(teeth)

    for sx in (-1, 1):
        fang = add_cone(
            c + right * sx * (r * 0.16) + fwd * (r * 1.00) - up * (r * 0.52),
            r * 0.05,
            r * 0.012,
            r * 0.18,
            rot=(math.radians(165), 0, 0),
            name=f"fang_{sx}",
        )
        assign_mat(fang, "sully_teeth", (0.93, 0.90, 0.82), 0.35)
        detail.append(fang)

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
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.012)
    bpy.ops.object.mode_set(mode="OBJECT")

    look = c + fwd * (r * 0.4)
    cam_loc = look + fwd * 28 + up * 1.5
    project_front_uvs(head, look, cam_loc, fwd)
    make_fur_shader(head.data.materials[0], PORTRAIT, use_uv_portrait=True)

    if "head" not in head.vertex_groups:
        vg = head.vertex_groups.new(name="head")
    else:
        vg = head.vertex_groups["head"]
    vg.add([v.index for v in head.data.vertices], 1.0, "REPLACE")

    if head.data.materials:
        head.data.materials[0].name = HEAD_MAT
    return head


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

    # Character faces -Y in this dump (camera at Y=-80 saw the front).
    fwd = Vector((0.0, -1.0, 0.0))
    up = Vector((0.0, 0.0, 1.0))
    right = Vector((1.0, 0.0, 0.0))

    head = build_sully_head(center, fwd, up, right)

    # Do not parent. Clear any leftover parenting from construction.
    head.parent = None
    body.parent = None
    head.name = "sully_face"
    body.name = "abrams_model"

    baked = ROOT / r"sully_textures\abrams_head_color_png_ce8a55ec.png"
    ok = bake_color(head, baked)
    if ok:
        alt = ROOT / r"sully_textures\abrams_head_basecolor_png_f84c4214.png"
        import shutil

        shutil.copyfile(baked, alt)
        print("Copied bake to", alt)

    # Bake object transforms into verts so FBX numbers stay Source-2 inches.
    for obj in (head, body):
        mw = obj.matrix_world.copy()
        obj.data.transform(mw)
        obj.matrix_world.identity()
        obj.data.update()

    hcenter, hsize, _, _ = mesh_world_bounds(head)
    print("head after flatten center", tuple(hcenter), "size", tuple(hsize), "verts", len(head.data.vertices))
    bcenter, bsize, _, _ = mesh_world_bounds(body)
    print("body after flatten center", tuple(bcenter), "size", tuple(bsize), "verts", len(body.data.vertices))

    CONTENT.mkdir(parents=True, exist_ok=True)
    export_mesh_fbx(CONTENT / "sully_face.fbx", head)
    export_mesh_fbx(OUT_DIR / "sully_face.fbx", head)
    export_mesh_fbx(CONTENT / "abrams_body_nohead.fbx", body)
    export_mesh_fbx(OUT_DIR / "abrams_body_nohead.fbx", body)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_DIR / "sully_cut.blend"))
    render_preview(
        OUT_DIR / "cut_preview.png",
        Vector((0, 4, 104)),
        Vector((22, -72, 112)),
    )
    # close-up of the new head
    render_preview(
        OUT_DIR / "sully_face_preview.png",
        Vector(hcenter),
        Vector((hcenter.x + 4, hcenter.y - 28, hcenter.z + 2)),
    )
    print("DONE")


if __name__ == "__main__":
    main()
