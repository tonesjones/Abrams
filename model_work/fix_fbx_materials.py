"""Rename body/head materials to stock Deadlock paths and re-export mesh-only FBX."""
from pathlib import Path
import bpy

BLEND = r"C:\TestCode\Abrams\model_work\sully_export\sully_cut.blend"
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
    "abrams_gun": "models/heroes_wip/abrams/materials/abrams_gun",
}


def export_mesh_fbx(path, obj):
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
        path_mode="STRIP",
        embed_textures=False,
        global_scale=1.0,
    )
    print("Wrote", path)


bpy.ops.wm.open_mainfile(filepath=BLEND)

print("all materials:")
for m in bpy.data.materials:
    print(" ", m.name)

head = bpy.data.objects.get("sully_face")
body = bpy.data.objects.get("abrams_model")
if not head or not body:
    raise SystemExit(f"missing objects head={head} body={body}")

# Shared stock head material (one datablock, used by body leftover + sully head)
hm = bpy.data.materials.get(HEAD_MAT)
if hm is None:
    # prefer renaming the imported abrams_head block
    for m in bpy.data.materials:
        if m.name.lower() == "abrams_head":
            m.name = HEAD_MAT
            hm = m
            break
if hm is None:
    hm = bpy.data.materials.new(HEAD_MAT)
hm.use_nodes = True

# Body: remap short names to full game paths; share head mat
for i, m in enumerate(list(body.data.materials)):
    if not m:
        continue
    low = m.name.lower()
    if "abrams_head" in low:
        body.data.materials[i] = hm
        print(f"body slot {i} -> shared {HEAD_MAT}")
        continue
    for key, dest in REMAP.items():
        if key in low and m.name != dest:
            print(f"rename body mat {m.name} -> {dest}")
            m.name = dest
            break

# Head: only the stock head material so the baked atlas applies
head.data.materials.clear()
head.data.materials.append(hm)
print("head materials now", [m.name for m in head.data.materials])
print("body materials now", [m.name if m else None for m in body.data.materials])

export_mesh_fbx(CONTENT / "sully_face.fbx", head)
export_mesh_fbx(OUT / "sully_face.fbx", head)
export_mesh_fbx(CONTENT / "abrams_body_nohead.fbx", body)
export_mesh_fbx(OUT / "abrams_body_nohead.fbx", body)
print("DONE")
