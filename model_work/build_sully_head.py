"""
Blender script: load Abrams glTF, remove face+glasses meshes, add Sully head
bound to head bone, export FBX for CSDK import.
Run: blender --background --python build_sully_head.py
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(r"C:\TestCode\Abrams")
GLTF = ROOT / r"model_work\abrams_export\models\heroes_wip\abrams\abrams.gltf"
PORTRAIT = ROOT / r"sully_textures\bull_card_psd.png"
if not PORTRAIT.exists():
    # fallback to session portrait
    PORTRAIT = Path(
        r"C:\Users\Owner\.grok\sessions\C%3A%5CTestCode%5CAbrams\019fe34f-a791-76b1-a53a-c9039a574e66\images\5.jpg"
    )
OUT_DIR = ROOT / r"model_work\sully_export"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_BLEND = OUT_DIR / "sully_abrams.blend"
OUT_FBX = OUT_DIR / "sully_abrams.fbx"
OUT_GLB = OUT_DIR / "sully_abrams.glb"


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_abrams():
    bpy.ops.import_scene.gltf(filepath=str(GLTF))
    print("Imported", GLTF)


def find_objects():
    arm = None
    face = None
    body = None
    gun = None
    book = None
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == "ARMATURE":
            arm = o
        elif o.type == "MESH":
            if "face" in n:
                face = o
            elif "abrams_model" in n and "face" not in n:
                body = o
            elif "gun" in n:
                gun = o
            elif "book" in n:
                book = o
    print("arm", arm, "face", face, "body", body)
    return arm, face, body, gun, book


def bone_world_matrix(arm, bone_name):
    arm.data.bones[bone_name]
    # pose matrix in world space
    pb = arm.pose.bones[bone_name]
    return arm.matrix_world @ pb.matrix


def delete_object(obj):
    if obj is None:
        return
    bpy.data.objects.remove(obj, do_unlink=True)


def make_sully_head(arm):
    """Create a stylized bulky monster head near the head bone."""
    head_m = bone_world_matrix(arm, "head")
    head_loc = head_m.translation.copy()

    # Base skull - elongated sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=24, radius=1.0, location=head_loc)
    skull = bpy.context.active_object
    skull.name = "sully_skull"
    skull.scale = (1.15, 1.35, 1.25)
    bpy.ops.object.transform_apply(scale=True)

    # Snout
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.55, location=head_loc + Vector((0, -0.85, -0.15)))
    snout = bpy.context.active_object
    snout.name = "sully_snout"
    snout.scale = (0.95, 1.2, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Ears L/R
    ears = []
    for side, sx in (("L", -0.95), ("R", 0.95)):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16, ring_count=12, radius=0.35, location=head_loc + Vector((sx, 0.1, 0.15))
        )
        e = bpy.context.active_object
        e.name = f"sully_ear_{side}"
        e.scale = (0.55, 0.9, 1.1)
        bpy.ops.object.transform_apply(scale=True)
        ears.append(e)

    # Horns
    horns = []
    for side, sx in (("L", -0.35), ("R", 0.35)):
        bpy.ops.mesh.primitive_cone_add(
            vertices=12,
            radius1=0.12,
            radius2=0.02,
            depth=0.55,
            location=head_loc + Vector((sx, 0.15, 0.95)),
        )
        h = bpy.context.active_object
        h.name = f"sully_horn_{side}"
        h.rotation_euler = (math.radians(-25), math.radians(sx * 25), 0)
        bpy.ops.object.transform_apply(rotation=True)
        horns.append(h)

    # Join all into one mesh
    bpy.ops.object.select_all(action="DESELECT")
    for o in [skull, snout, *ears, *horns]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = skull
    bpy.ops.object.join()
    head = bpy.context.active_object
    head.name = "sully_head"

    # Shade smooth
    bpy.ops.object.shade_smooth()

    # UV unwrap
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Material + portrait texture if available
    mat = bpy.data.materials.new(name="sully_head_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.72, 0.78, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.65
    if PORTRAIT.exists():
        try:
            img = bpy.data.images.load(str(PORTRAIT))
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            tex.location = (-300, 300)
            if bsdf:
                nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        except Exception as e:
            print("texture load failed", e)
    if head.data.materials:
        head.data.materials[0] = mat
    else:
        head.data.materials.append(mat)

    # Parent with automatic weights to armature, then force head bone weights
    head.parent = arm
    head.parent_type = "ARMATURE"
    # Add armature modifier
    mod = head.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm

    # Vertex groups: 100% head bone
    vg = head.vertex_groups.new(name="head")
    idxs = [v.index for v in head.data.vertices]
    vg.add(idxs, 1.0, "REPLACE")

    # Also parent to head bone for transform
    # Use bone-relative placement
    head.parent_type = "BONE"
    head.parent_bone = "head"
    # Reset to sit on bone - bone parent uses bone tip space
    head.location = (0.0, 0.0, 0.15)
    head.rotation_euler = (math.radians(90), 0, 0)
    head.scale = (12.0, 12.0, 12.0)  # glTF/Source scales vary; tune

    return head


def remove_glasses_meshes(arm, body):
    """Scale glasses bones to zero so frames collapse if skinned to them."""
    if arm is None:
        return
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for b in arm.pose.bones:
        if "glass" in b.name.lower():
            b.scale = (0.001, 0.001, 0.001)
            print("collapsed bone", b.name)
    bpy.ops.object.mode_set(mode="OBJECT")


def main():
    clear_scene()
    import_abrams()
    arm, face, body, gun, book = find_objects()
    if arm is None:
        print("ERROR: no armature")
        sys.exit(1)

    # Remove separate face mesh entirely (stock Abrams face)
    if face:
        print("Deleting face mesh", face.name)
        delete_object(face)

    remove_glasses_meshes(arm, body)
    head = make_sully_head(arm)
    print("Created", head.name, "verts", len(head.data.vertices))

    # Save blend
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print("Saved", OUT_BLEND)

    # Export FBX (common CSDK import path)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(
        filepath=str(OUT_FBX),
        use_selection=False,
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        armature_nodetype="NULL",
    )
    print("Saved", OUT_FBX)

    # Also GLB for inspection
    bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format="GLB", export_animations=False)
    print("Saved", OUT_GLB)
    print("DONE")


if __name__ == "__main__":
    main()
