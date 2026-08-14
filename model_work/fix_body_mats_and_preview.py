import bpy
from mathutils import Vector
from pathlib import Path

BLEND = r"C:\TestCode\Abrams\model_work\sully_export\sully_cut.blend"
CONTENT = Path(r"C:\TestCode\Abrams\tools\Reduced_CSDK_12\content\citadel_addons\sully_abrams\models\heroes_wip\abrams")
PREVIEW = r"C:\TestCode\Abrams\model_work\sully_export\cut_preview.png"

bpy.ops.wm.open_mainfile(filepath=BLEND)
rename = {
    "abrams_head": "models/heroes_wip/abrams/materials/abrams_head",
    "abrams_upper_body": "models/heroes_wip/abrams/materials/abrams_upper_body",
    "abrams_lower_body": "models/heroes_wip/abrams/materials/abrams_lower_body",
    "abrams_coat": "models/heroes_wip/abrams/materials/abrams_coat",
    "abrams_teeth": "models/heroes_wip/abrams/materials/abrams_teeth",
    "abrams_gun": "models/heroes_wip/abrams/materials/abrams_gun",
}
for m in list(bpy.data.materials):
    if m.name in rename:
        print("rename", m.name, "->", rename[m.name])
        m.name = rename[m.name]
    else:
        print("mat", m.name)

body = next((o for o in bpy.data.objects if o.type == "MESH" and "abrams" in o.name.lower() and "face" not in o.name.lower() and "sully" not in o.name.lower()), None)
head = next((o for o in bpy.data.objects if o.type == "MESH" and "sully" in o.name.lower()), None)
arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
print("body", body, "head", head, "arm", arm)

def export_fbx(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        if o:
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

if body and arm:
    export_fbx(CONTENT / "abrams_body_nohead.fbx", [body, arm])
if head and arm:
    export_fbx(CONTENT / "sully_face.fbx", [head, arm])

# Preview body+head
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = False
world = bpy.data.worlds.new("W") if not bpy.context.scene.world else bpy.context.scene.world
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.2, 0.24, 1)
# camera in front of head
cam_loc = Vector((25, -70, 108))
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.object
cam.rotation_euler = (Vector((0, 5, 103)) - cam_loc).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type="SUN", location=cam_loc)
bpy.context.object.data.energy = 6
bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 900
bpy.context.scene.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)
print("Wrote", PREVIEW)
